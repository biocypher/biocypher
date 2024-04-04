#!/usr/bin/env python

#
# Copyright 2021, Heidelberg University Clinic
#
# File author(s): Sebastian Lobentanzer
#                 ...
#
# Distributed under MIT licence, see the file `LICENSE`.
#
"""
BioCypher get module. Used to download and cache data from external sources.
"""

from __future__ import annotations

from typing import Optional
import shutil

from ._logger import logger

logger.debug(f"Loading module {__name__}.")

from datetime import datetime, timedelta
from tempfile import TemporaryDirectory
import os
import json
import ftplib

import pooch

from ._misc import to_list


class Resource:
    def __init__(
        self,
        name: str,
        url_s: str | list[str],
        lifetime: int = 0,
        is_dir: bool = False,
    ):
        """
        A resource is a file that can be downloaded from a URL and cached
        locally. This class implements checks of the minimum requirements for
        a resource, to be implemented by a biocypher adapter.

        Args:
            name (str): The name of the resource.

            url_s (str | list[str]): The URL or URLs of the resource.

            lifetime (int): The lifetime of the resource in days. If 0, the
                resource is considered to be permanent.

            is_dir (bool): Whether the resource is a directory or not.
        """
        self.name = name
        self.url_s = url_s
        self.lifetime = lifetime
        self.is_dir = is_dir


class Downloader:
    def __init__(self, cache_dir: Optional[str] = None) -> None:
        """
        A downloader is a collection of resources that can be downloaded
        and cached locally. It manages the lifetime of downloaded resources by
        keeping a JSON record of the download date of each resource.

        Args:
            cache_dir (str): The directory where the resources are cached. If
                not given, a temporary directory is created.

        Returns:
            Downloader: The downloader object.
        """
        self.cache_dir = cache_dir or TemporaryDirectory().name
        self.cache_file = os.path.join(self.cache_dir, "cache.json")
        self.cache_dict = self._load_cache_dict()

    # download function that accepts a resource or a list of resources
    def download(self, *resources: Resource):
        """
        Download one or multiple resources.

        Args:
            resources (Resource): The resource or resources to download.

        Returns:
            str or list: The path or paths to the downloaded resource(s).
        """
        paths = []
        for resource in resources:
            paths.append(self._download_or_cache(resource))

        # flatten list if it is nested
        if is_nested(paths):
            paths = [path for sublist in paths for path in sublist]

        return paths

    def _download_or_cache(self, resource: Resource, cache: bool = True):
        """
        Download a resource if it is not cached or exceeded its lifetime.

        Args:
            resource (Resource): The resource to download.

        Returns:
            str or list: The path or paths to the downloaded resource(s).
        """
        expired = self._is_cache_expired(resource)

        if expired or not cache:
            self._delete_expired_resource_cache(resource)
            logger.info(f"Asking for download of {resource.name}.")
            paths = self._download_resource(cache, resource)
        else:
            paths = self.get_cached_version(resource)
        self._update_cache_record(resource)
        return paths

    def _is_cache_expired(self, resource: Resource) -> bool:
        """
        Check if resource cache is expired.

        Args:
            resource (Resource): The resource to download.

        Returns:
            bool: cache is expired or not.
        """
        cache_record = self._get_cache_record(resource)
        if cache_record:
            download_time = datetime.strptime(
                cache_record.get("date_downloaded"), "%Y-%m-%d %H:%M:%S.%f"
            )
            lifetime = timedelta(days=resource.lifetime)
            expired = download_time + lifetime < datetime.now()
        else:
            expired = True
        return expired

    def _delete_expired_resource_cache(self, resource: Resource):
        resource_cache_path = self.cache_dir + "/" + resource.name
        if os.path.exists(resource_cache_path) and os.path.isdir(
            resource_cache_path
        ):
            shutil.rmtree(resource_cache_path)

    def _download_resource(self, cache, resource):
        """Download a resource.

        Args:
            cache (bool): Whether to cache the resource or not.
            resource (Resource): The resource to download.

        Returns:
            str or list: The path or paths to the downloaded resource(s).
        """
        if resource.is_dir:
            files = self._get_files(resource)
            resource.url_s = [resource.url_s + "/" + file for file in files]
            resource.is_dir = False
            paths = self._download_or_cache(resource, cache)
        elif isinstance(resource.url_s, list):
            paths = []
            for url in resource.url_s:
                fname = url[url.rfind("/") + 1 :]
                paths.append(
                    self._retrieve(
                        url=url,
                        fname=fname,
                        path=os.path.join(self.cache_dir, resource.name),
                    )
                )
        else:
            fname = resource.url_s[resource.url_s.rfind("/") + 1 :]
            paths = self._retrieve(
                url=resource.url_s,
                fname=fname,
                path=os.path.join(self.cache_dir, resource.name),
            )
        # sometimes a compressed file contains multiple files
        # TODO ask for a list of files in the archive to be used from the
        # adapter
        return paths

    def get_cached_version(self, resource) -> list[str]:
        """Get the cached version of a resource.

        Args:
            resource (Resource): The resource to get the cached version of.

        Returns:
            list[str]: The paths to the cached resource(s).
        """
        cached_resource_location = os.path.join(self.cache_dir, resource.name)
        logger.info(f"Use cached version from {cached_resource_location}.")
        paths = []
        for file in os.listdir(cached_resource_location):
            paths.append(os.path.join(cached_resource_location, file))
        return paths

    def _retrieve(
        self,
        url: str,
        fname: str,
        path: str,
        known_hash: str = None,
    ):
        """
        Retrieve a file from a URL using Pooch. Infer type of file from
        extension and use appropriate processor.

        Args:
            url (str): The URL to retrieve the file from.

            fname (str): The name of the file.

            path (str): The path to the file.
        """
        if fname.endswith(".zip"):
            return pooch.retrieve(
                url=url,
                known_hash=known_hash,
                fname=fname,
                path=path,
                processor=pooch.Unzip(),
                progressbar=True,
            )

        elif fname.endswith(".tar.gz"):
            return pooch.retrieve(
                url=url,
                known_hash=known_hash,
                fname=fname,
                path=path,
                processor=pooch.Untar(),
                progressbar=True,
            )

        elif fname.endswith(".gz"):
            return pooch.retrieve(
                url=url,
                known_hash=known_hash,
                fname=fname,
                path=path,
                processor=pooch.Decompress(),
                progressbar=True,
            )

        else:
            return pooch.retrieve(
                url=url,
                known_hash=known_hash,
                fname=fname,
                path=path,
                progressbar=True,
            )

    def _get_files(self, resource: Resource):
        """
        Get the files contained in a directory resource.

        Args:
            resource (Resource): The directory resource.

        Returns:
            list: The files contained in the directory.
        """
        if resource.url_s.startswith("ftp://"):
            # remove protocol
            url = resource.url_s[6:]
            # get base url
            url = url[: url.find("/")]
            # get directory (remove initial slash as well)
            dir = resource.url_s[7 + len(url) :]
            # get files
            ftp = ftplib.FTP(url)
            ftp.login()
            ftp.cwd(dir)
            files = ftp.nlst()
            ftp.quit()
        else:
            raise NotImplementedError(
                "Only FTP directories are supported at the moment."
            )

        return files

    def _load_cache_dict(self):
        """
        Load the cache dictionary from the cache file. Create an empty cache
        file if it does not exist.
        """
        if not os.path.exists(self.cache_dir):
            logger.info(f"Creating cache directory {self.cache_dir}.")
            os.makedirs(self.cache_dir)

        if not os.path.exists(self.cache_file):
            logger.info(f"Creating cache file {self.cache_file}.")
            with open(self.cache_file, "w") as f:
                json.dump({}, f)

        with open(self.cache_file, "r") as f:
            logger.info(f"Loading cache file {self.cache_file}.")
            return json.load(f)

    def _get_cache_record(self, resource: Resource):
        """
        Get the cache record of a resource.

        Args:
            resource (Resource): The resource to get the cache record of.

        Returns:
            The cache record of the resource.
        """
        return self.cache_dict.get(resource.name, {})

    def _update_cache_record(self, resource: Resource):
        """
        Update the cache record of a resource.

        Args:
            resource (Resource): The resource to update the cache record of.
        """
        cache_record = {}
        cache_record["url"] = to_list(resource.url_s)
        cache_record["date_downloaded"] = str(datetime.now())
        cache_record["lifetime"] = resource.lifetime
        self.cache_dict[resource.name] = cache_record
        with open(self.cache_file, "w") as f:
            json.dump(self.cache_dict, f, default=str)


def is_nested(lst):
    """
    Check if a list is nested.

    Args:
        lst (list): The list to check.

    Returns:
        bool: True if the list is nested, False otherwise.
    """
    for item in lst:
        if isinstance(item, list):
            return True
    return False
