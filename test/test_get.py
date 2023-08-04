import os
import json

from hypothesis import given
from hypothesis import strategies as st
import pytest

from biocypher._get import Resource, Downloader


@given(st.builds(Resource))
def test_resource(resource):
    assert isinstance(resource.name, str)
    assert isinstance(resource.url, str)
    assert isinstance(resource.lifetime, int)


@given(st.builds(Downloader))
def test_downloader(downloader):
    assert isinstance(downloader.cache_dir, str)
    assert isinstance(downloader.cache_file, str)


def test_download():
    # use temp dir, no cache file present
    downloader = Downloader(cache_dir=None)
    assert os.path.exists(downloader.cache_dir)
    assert os.path.exists(downloader.cache_file)
    resource = Resource(
        "test_resource",
        "https://github.com/biocypher/biocypher/raw/get-module/test/test_CSVs.zip",
        lifetime=7,
    )
    paths = downloader.download(resource)
    with open(downloader.cache_file, "r") as f:
        cache = json.load(f)
    assert (
        cache["test_resource"]["url"]
        == "https://github.com/biocypher/biocypher/raw/get-module/test/test_CSVs.zip"
    )
    assert cache["test_resource"]["lifetime"] == 7
    assert cache["test_resource"]["date_downloaded"]
    for path in paths:
        assert os.path.exists(path)


def test_download_expired():
    # set up test file to be expired, monkeypatch?
    {
        "test_resource": {
            "url": "https://github.com/biocypher/biocypher/raw/get-module/test/test_CSVs.zip",
            "date_downloaded": "2022-08-04 20:41:09.375915",
            "lifetime": 7,
        }
    }


def test_download_resource_list():
    pass
