from datetime import datetime, timedelta
import os
import json

from hypothesis import given
from hypothesis import strategies as st
import pytest

from biocypher._get import Resource, Downloader


@pytest.fixture
def downloader():
    return Downloader(cache_dir=None)


@given(st.builds(Resource))
def test_resource(resource):
    assert isinstance(resource.name, str)
    assert isinstance(resource.url_s, str) or isinstance(resource.url_s, list)
    assert isinstance(resource.lifetime, int)


def test_downloader(downloader):
    assert isinstance(downloader.cache_dir, str)
    assert isinstance(downloader.cache_file, str)


def test_download_file(downloader):
    resource = Resource(
        "test_resource",
        "https://github.com/biocypher/biocypher/raw/main/biocypher/_config/test_config.yaml",
        lifetime=7,
    )
    paths = downloader.download(resource)
    assert len(paths) == 1
    assert os.path.exists(paths[0])

    # test caching
    paths = downloader.download(resource)
    # should not download again
    assert paths[0] is None

    # manipulate cache dict to test expiration (datetime format)
    downloader.cache_dict["test_resource"][
        "date_downloaded"
    ] = datetime.now() - timedelta(days=8)

    paths = downloader.download(resource)
    # should download again
    assert len(paths) == 1
    assert paths[0] is not None


def test_download_file_list(downloader):
    resource = Resource(
        "test_resource",
        [
            "https://github.com/biocypher/biocypher/raw/main/biocypher/_config/test_config.yaml",
            "https://github.com/biocypher/biocypher/raw/main/biocypher/_config/test_schema_config_disconnected.yaml",
        ],
    )
    paths = downloader.download(resource)
    assert len(paths) == 2
    assert os.path.exists(paths[0])
    assert os.path.exists(paths[1])


def test_download_directory():
    # use temp dir, no cache file present
    downloader = Downloader(cache_dir=None)
    assert os.path.exists(downloader.cache_dir)
    assert os.path.exists(downloader.cache_file)
    resource = Resource(
        "ot_indication",
        "ftp://ftp.ebi.ac.uk/pub/databases/opentargets/platform/23.06/output/etl/parquet/go",
        lifetime=7,
        is_dir=True,
    )
    paths = downloader.download(resource)
    assert len(paths) == 17
    for path in paths:
        assert os.path.exists(path)

    # test caching
    paths = downloader.download(resource)
    # should not download again
    assert len(paths) == 1
    assert paths[0] is None


def test_download_zip():
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

    # use files downloaded here and manipulate cache file to test expiration?


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
