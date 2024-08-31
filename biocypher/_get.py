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

from typing import Union, Optional
import shutil

import requests

from ._logger import logger

logger.debug(f"Loading module {__name__}.")

from datetime import datetime, timedelta
from tempfile import TemporaryDirectory
import os
import json
import ftplib

import pooch

from ._misc import to_list, is_nested


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


class APIRequest:
    def __init__(self, name: str, url_s: str | list, lifetime: int = 0):
        """
        Represents basic information for an API request.

        Args:
            name(str): The name of the API request.

            url(str|list): The URL of the API endpoint.

            lifetime(int): The lifetime of the API request in days. If 0, the
                API request is cached indefinitely.

        """
        self.name = name
        self.url_s = url_s
        self.lifetime = lifetime


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
    def download(self, *downloads: Union[Resource, APIRequest]):
        """
        Download one or multiple resources, APIrequest, or both.

        Args:
            downloads (Resource or APIRequest): The resource(s) or API request(s) to download.

        Returns:
            list[str]: The path or paths to the downloaded resource(s) or API request(s).
        """
        paths = []
        for download in downloads:
            paths.append(self._download_or_cache(download))

        # flatten list if it is nested
        if is_nested(paths):
            paths = [path for sublist in paths for path in sublist]

        return paths

    def _download_or_cache(
        self, download: Union[Resource, APIRequest], cache: bool = True
    ):
        """
        Download a resource or an API request if it is not cached or exceeded its lifetime.

        Args:
            download (Resource or APIRequest): The resource or API request to download.
        Returns:
            list[str]: The path or paths to the downloaded resource(s) or API request(s).
        """
        expired = self._is_cache_expired(download)

        if expired or not cache:
            self._delete_expired_cache(download)
            if isinstance(download, Resource):
                logger.info(f"Asking for download of resource {download.name}.")
                paths = self._download_resource(cache, download)
            else:
                logger.info(
                    f"Asking for download of api request {download.name}."
                )
                paths = self._download_api_request(download)
        else:
            paths = self.get_cached_version(download)
        self._update_cache_record(download)
        return paths

    def _is_cache_expired(self, download: Union[Resource, APIRequest]) -> bool:
        """
        Check if resource or API request cache is expired.

        Args:
            download (Resource or APIRequest): The resource or API request to download.

        Returns:
            bool: cache is expired or not.
        """
        cache_record = self._get_cache_record(download)
        if cache_record:
            download_time = datetime.strptime(
                cache_record.get("date_downloaded"), "%Y-%m-%d %H:%M:%S.%f"
            )
            lifetime = timedelta(days=download.lifetime)
            expired = download_time + lifetime < datetime.now()
        else:
            expired = True
        return expired

    def _delete_expired_cache(self, download: Union[Resource, APIRequest]):
        cache_path = self.cache_dir + "/" + download.name
        if os.path.exists(cache_path) and os.path.isdir(cache_path):
            shutil.rmtree(cache_path)

    def _download_resource(self, cache, resource):
        """Download a resource.

        Args:
            cache (bool): Whether to cache the resource or not.
            resource (Resource): The resource to download.

        Returns:
            list[str]: The path or paths to the downloaded resource(s).
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
            paths = []
            fname = resource.url_s[resource.url_s.rfind("/") + 1 :]
            results = self._retrieve(
                url=resource.url_s,
                fname=fname,
                path=os.path.join(self.cache_dir, resource.name),
            )
            if isinstance(results, list):
                paths.extend(results)
            else:
                paths.append(results)

        # sometimes a compressed file contains multiple files
        # TODO ask for a list of files in the archive to be used from the
        # adapter
        return paths

    def _download_api_request(self, api_request: APIRequest):
        """
        Download the API request and return the path.
        Args:

            api_request(APIRequest): The API request result that is being cached.
        Returns:
            list[str]: The path to the cached API request.

        """
        urls = (
            api_request.url_s
            if isinstance(api_request.url_s, list)
            else [api_request.url_s]
        )
        paths = []
        for url in urls:
            fname = url[url.rfind("/") + 1 :].rsplit(".", 1)[0]
            logger.info(
                f"Asking for caching API of {api_request.name} {fname}."
            )
            response = requests.get(url=url)

            if response.status_code != 200:
                response.raise_for_status()
            response_data = response.json()
            api_path = os.path.join(
                self.cache_dir, api_request.name, f"{fname}.json"
            )

            os.makedirs(os.path.dirname(api_path), exist_ok=True)
            with open(api_path, "w") as f:
                json.dump(response_data, f)
                logger.info(f"Caching API request to {api_path}.")
            paths.append(api_path)
        return paths

    def get_cached_version(
        self, download: Union[Resource, APIRequest]
    ) -> list[str]:
        """Get the cached version of a resource.

        Args:
            download(Resource or APIRequest): The resource or API request to get the cached version of.

        Returns:
            list[str]: The paths to the cached resource(s) or API request(s).
        """
        cached_location = os.path.join(self.cache_dir, download.name)
        logger.info(f"Use cached version from {cached_location}.")
        paths = []
        for file in os.listdir(cached_location):
            paths.append(os.path.join(cached_location, file))
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

    def _get_cache_record(self, download: Union[Resource, APIRequest]):
        """
        Get the cache record of a resource or an API request.

        Args:
            download (Resource or APIRequest): The resource or API request to get the cache record of.

        Returns:
            The cache record of the resource.
        """
        return self.cache_dict.get(download.name, {})

    def _update_cache_record(self, download: Union[Resource, APIRequest]):
        """
        Update the cache record of a resource or an API request.

        Args:
            download (Resource or APIrequest): The resource or API request to update the cache record of.
        """
        cache_record = {}
        cache_record["url"] = to_list(download.url_s)
        cache_record["date_downloaded"] = str(datetime.now())
        cache_record["lifetime"] = download.lifetime
        self.cache_dict[download.name] = cache_record
        with open(self.cache_file, "w") as f:
            json.dump(self.cache_dict, f, default=str)
