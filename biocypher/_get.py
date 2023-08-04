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

from ._logger import logger

logger.debug(f"Loading module {__name__}.")

from datetime import datetime, timedelta
from tempfile import TemporaryDirectory
import os
import json

import pooch


class Resource:
    def __init__(self, name: str, url: str, lifetime: int = 0):
        """
        A resource is a file that can be downloaded from a URL and cached
        locally. This class implements checks of the minimum requirements for
        a resource, to be implemented by a biocypher adapter.

        Args:
            name (str): The name of the resource.

            url (str): The URL of the resource.

            lifetime (int): The lifetime of the resource in days. If 0, the
                resource is considered to be permanent.
        """
        self.name = name
        self.url = url
        self.lifetime = lifetime


class Downloader:
    def __init__(self, cache_dir: str):
        """
        A downloader is a collection of resources that can be downloaded
        and cached locally. It manages the lifetime of downloaded resources by
        keeping a JSON record of the download date of each resource.

        Args:
            cache_dir (str): The directory where the resources are cached. If
                not given, a temporary directory is created.
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

        # flatten list
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
        # check if resource is cached
        cache_record = self._get_cache_record(resource)

        if cache_record:
            # check if resource is expired (formatted in days)
            dl = datetime.fromisoformat(cache_record.get("date_downloaded"))
            lt = timedelta(days=resource.lifetime)
            expired = dl + lt < datetime.now()
        else:
            expired = True

        # download resource
        if expired or not cache:
            logger.info(f"Downloading resource {resource.name}.")

            path = pooch.retrieve(
                resource.url,
                None,
                fname=resource.name,
                path=self.cache_dir,
                processor=pooch.Unzip(),
                progressbar=True,
            )

            # sometimes a compressed file contains multiple files
            # TODO ask for a list of files in the archive to be used from the
            # adapter

            # update cache record
            self._update_cache_record(resource)

            return path

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
        cache_record["url"] = resource.url
        cache_record["date_downloaded"] = datetime.now()
        cache_record["lifetime"] = resource.lifetime
        self.cache_dict[resource.name] = cache_record
        with open(self.cache_file, "w") as f:
            json.dump(self.cache_dict, f, default=str)
