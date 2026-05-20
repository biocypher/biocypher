import json
import os

from datetime import datetime, timedelta
from unittest.mock import patch, Mock

import pytest

from hypothesis import (
    given,
    strategies as st,
)

from biocypher._get import APIRequest, Downloader, FileDownload, Resource


@pytest.fixture
def downloader(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def downloader_without_specified_cache_dir():
    return Downloader()


@pytest.fixture
def downloader_with_specified_cache_dir(tmp_path):
    tmp_cache_dir = tmp_path / ".cache"
    tmp_cache_dir.mkdir()
    return Downloader(cache_dir=str(tmp_cache_dir))


def _mock_retrieve(url, known_hash, fname, path, **kwargs):
    _mock_retrieve.calls += 1
    timestamp = datetime.now().timestamp() + _mock_retrieve.calls
    os.makedirs(path, exist_ok=True)

    if fname.endswith(".zip"):
        unzip_dir = os.path.join(path, f"{fname}.unzip")
        os.makedirs(unzip_dir, exist_ok=True)
        paths = [
            os.path.join(unzip_dir, "file1.csv"),
            os.path.join(unzip_dir, "file2.csv"),
        ]
        for file_path in paths:
            with open(file_path, "w") as f:
                f.write("source,target\nA,B\n")
            os.utime(file_path, (timestamp, timestamp))
        return paths

    full_path = os.path.join(path, fname)
    with open(full_path, "w") as f:
        f.write(f"mocked content from {url}\n")
    os.utime(full_path, (timestamp, timestamp))
    return full_path


_mock_retrieve.calls = 0


@given(
    st.builds(
        Resource,
        name=st.text(),
        url_s=st.text(),
        lifetime=st.integers(),
    )
)
def test_resource(resource):
    assert isinstance(resource.name, str)
    assert isinstance(resource.url_s, str) or isinstance(resource.url_s, list)
    assert isinstance(resource.lifetime, int)


@given(
    st.builds(
        FileDownload,
        name=st.text(),
        url_s=st.text(),
        lifetime=st.integers(),
    )
)
def test_file_download(file_download):
    assert isinstance(file_download.name, str)
    assert isinstance(file_download.url_s, str)
    assert isinstance(file_download.lifetime, int)


@given(
    st.builds(
        APIRequest,
        name=st.text(),
        url_s=st.text(),
        lifetime=st.integers(),
    )
)
def test_API(api):
    assert isinstance(api.name, str)
    assert isinstance(api.url_s, str)
    assert isinstance(api.lifetime, int)


@pytest.mark.parametrize(
    "downloader",
    [
        "downloader_without_specified_cache_dir",
        "downloader_with_specified_cache_dir",
    ],
    indirect=True,
)
def test_downloader(downloader):
    assert isinstance(downloader.cache_dir, str)
    assert isinstance(downloader.cache_file, str)


@pytest.mark.parametrize(
    "downloader",
    [
        "downloader_without_specified_cache_dir",
        "downloader_with_specified_cache_dir",
    ],
    indirect=True,
)
@patch("biocypher._get.pooch.retrieve", side_effect=_mock_retrieve)
def test_download_file(mock_retrieve, downloader):
    resource = FileDownload(
        "test_resource",
        "https://github.com/biocypher/biocypher/raw/main/biocypher/_config/test_config.yaml",
        lifetime=7,
    )
    paths = downloader.download(resource)
    initial_download_time = os.path.getmtime(paths[0])
    assert len(paths) == 1
    assert os.path.exists(paths[0])
    assert f"{os.sep}test_resource{os.sep}test_config.yaml" in paths[0]

    # test caching
    paths = downloader.download(resource)
    assert len(paths) == 1
    # should not download again
    assert initial_download_time == os.path.getmtime(paths[0])

    # manipulate cache dict to test expiration
    downloader.cache_dict["test_resource"]["date_downloaded"] = str(datetime.now() - timedelta(days=8))

    paths = downloader.download(resource)
    assert len(paths) == 1
    # should download again
    assert initial_download_time < os.path.getmtime(paths[0])
    assert mock_retrieve.call_count == 2


@pytest.mark.parametrize(
    "downloader",
    [
        "downloader_without_specified_cache_dir",
        "downloader_with_specified_cache_dir",
    ],
    indirect=True,
)
@patch("biocypher._get.pooch.retrieve", side_effect=_mock_retrieve)
def test_download_lists(mock_retrieve, downloader):
    resource1 = FileDownload(
        name="test_resource1",
        url_s=[
            "https://github.com/biocypher/biocypher/raw/main/biocypher/_config/test_config.yaml",
            "https://github.com/biocypher/biocypher/raw/main/biocypher/_config/test_schema_config_disconnected.yaml",
        ],
    )
    resource2 = FileDownload(
        "test_resource2",
        "https://github.com/biocypher/biocypher/raw/main/test/test_CSVs.zip",
    )
    paths = downloader.download(resource1, resource2)
    assert len(paths) == 4  # 2 files from resource1, 2 files from resource2 zip
    assert os.path.exists(paths[0])
    assert os.path.exists(paths[1])
    assert os.path.exists(paths[2])
    assert os.path.exists(paths[3])
    expected_paths = [
        os.path.realpath(os.path.join(downloader.cache_dir, "test_resource1", "test_config.yaml")),
        os.path.realpath(
            os.path.join(
                downloader.cache_dir,
                "test_resource1",
                "test_schema_config_disconnected.yaml",
            )
        ),
        os.path.realpath(
            os.path.join(
                downloader.cache_dir,
                "test_resource2",
                "test_CSVs.zip.unzip",
                "file1.csv",
            )
        ),
        os.path.realpath(
            os.path.join(
                downloader.cache_dir,
                "test_resource2",
                "test_CSVs.zip.unzip",
                "file2.csv",
            )
        ),
    ]
    for path in paths:
        assert os.path.realpath(path) in expected_paths
    # valid datetime
    dt = datetime.strptime(
        downloader.cache_dict["test_resource1"]["date_downloaded"],
        "%Y-%m-%d %H:%M:%S.%f",
    )
    assert isinstance(dt, datetime)
    assert isinstance(downloader.cache_dict["test_resource1"]["url"], list)
    assert len(downloader.cache_dict["test_resource1"]["url"]) == 2
    assert downloader.cache_dict["test_resource1"]["lifetime"] == 0
    assert isinstance(downloader.cache_dict["test_resource2"]["url"], list)
    assert len(downloader.cache_dict["test_resource2"]["url"]) == 1
    assert downloader.cache_dict["test_resource2"]["lifetime"] == 0
    assert mock_retrieve.call_count == 3


@pytest.mark.skip(reason="Inconsistent FTP server response")
def test_download_directory_and_caching():
    # use temp dir, no cache file present
    downloader = Downloader(cache_dir=None)
    assert os.path.exists(downloader.cache_dir)
    assert os.path.exists(downloader.cache_file)
    resource = FileDownload(
        "ot_indication",
        "ftp://ftp.ebi.ac.uk/pub/databases/opentargets/platform/24.09/output/etl/parquet/go",
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
    assert len(paths) == 17
    assert "tmp" in paths[0]


@patch("biocypher._get.pooch.retrieve", side_effect=_mock_retrieve)
def test_download_zip_and_expiration(mock_retrieve):
    # use temp dir, no cache file present
    downloader = Downloader(cache_dir=None)
    assert os.path.exists(downloader.cache_dir)
    assert os.path.exists(downloader.cache_file)
    resource = FileDownload(
        "test_resource",
        "https://github.com/biocypher/biocypher/raw/main/test/test_CSVs.zip",
        lifetime=7,
    )
    paths = downloader.download(resource)
    with open(downloader.cache_file, "r") as f:
        cache = json.load(f)
    assert cache["test_resource"]["url"][0] == "https://github.com/biocypher/biocypher/raw/main/test/test_CSVs.zip"
    assert cache["test_resource"]["lifetime"] == 7
    assert cache["test_resource"]["date_downloaded"]

    for path in paths:
        assert os.path.exists(path)

    # use files downloaded here and manipulate cache file to test expiration
    downloader.cache_dict["test_resource"]["date_downloaded"] = str(datetime.now() - timedelta(days=4))
    paths = downloader.download(resource)
    # should not download again
    assert "tmp" in paths[0]

    # minus 8 days from date_downloaded
    downloader.cache_dict["test_resource"]["date_downloaded"] = str(datetime.now() - timedelta(days=8))

    paths = downloader.download(resource)
    # should download again
    assert paths[0] is not None
    assert mock_retrieve.call_count == 2


@pytest.mark.parametrize(
    "downloader",
    [
        "downloader_without_specified_cache_dir",
        "downloader_with_specified_cache_dir",
    ],
    indirect=True,
)
@patch("requests.get")
def test_cache_api_request(mock_get, downloader):
    mock_data = {
        "P12345.json": {"uniprotId": "P12345", "entryType": "UniProtKB reviewed (Swiss-Prot)"},
        "P69905.json": {"uniprotId": "P69905", "entryType": "UniProtKB reviewed (Swiss-Prot)"},
        "countTotal": {"count": 12345},
    }

    def side_effect(url=None, **kwargs):
        resp = Mock()
        resp.status_code = 200
        resp.raise_for_status = Mock()
        for key, data in mock_data.items():
            if key in url:
                resp.json = lambda d=data: d
                return resp
        resp.json = lambda: {}
        return resp

    mock_get.side_effect = side_effect

    api1 = APIRequest(
        name="uniprot_api",
        url_s=[
            "https://rest.uniprot.org/uniprotkb/P12345.json",
            "https://rest.uniprot.org/uniprotkb/P69905.json",
        ],
        lifetime=1,
    )
    api2 = APIRequest(
        name="intact_api",
        url_s="https://www.ebi.ac.uk/intact/ws/interactor/countTotal",
        lifetime=1,
    )

    paths = downloader.download(api1, api2)

    # test download list
    assert isinstance(paths, list)
    assert len(paths) == 3  # 2 API requests from api1, 1 API request from api2
    for path in paths:
        assert os.path.exists(path)
    assert f"{os.sep}{api1.name}{os.sep}P12345.json" in paths[0]
    assert f"{os.sep}{api1.name}{os.sep}P69905.json" in paths[1]
    assert f"{os.sep}{api2.name}{os.sep}countTotal.json" in paths[2]

    # api1 and api2 have been cached
    # test cached api request
    test_paths = downloader.download(api1, api2)  # get the path(s) of cached API request(s)
    assert isinstance(test_paths, list)
    assert len(paths) == len(test_paths)

    paths.sort()
    test_paths.sort()
    for i in range(len(paths)):
        with open(paths[i], "r") as file1:
            api_request1 = json.load(file1)

        with open(test_paths[i], "r") as file2:
            api_request2 = json.load(file2)
        assert api_request1 == api_request2


@patch("requests.get")
def test_api_expiration(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json = lambda: {"uniprotId": "P12345", "entryType": "UniProtKB reviewed (Swiss-Prot)"}
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    downloader = Downloader(cache_dir=None)
    assert os.path.exists(downloader.cache_dir)
    assert os.path.exists(downloader.cache_file)
    resource = APIRequest(
        "test_resource",
        "https://rest.uniprot.org/uniprotkb/P12345.json",
        lifetime=7,
    )
    paths = downloader.download(resource)
    with open(downloader.cache_file, "r") as f:
        cache = json.load(f)
    assert cache["test_resource"]["url"][0] == "https://rest.uniprot.org/uniprotkb/P12345.json"
    assert cache["test_resource"]["lifetime"] == 7
    assert cache["test_resource"]["date_downloaded"]

    assert os.path.exists(paths[0])

    # use files downloaded here and manipulate cache file to test expiration
    downloader.cache_dict["test_resource"]["date_downloaded"] = str(datetime.now() - timedelta(days=4))
    paths = downloader.download(resource)
    # should not download again
    assert "tmp" in paths[0]

    # minus 8 days from date_downloaded
    downloader.cache_dict["test_resource"]["date_downloaded"] = str(datetime.now() - timedelta(days=8))

    paths = downloader.download(resource)
    # should download again
    assert paths[0] is not None


@patch("biocypher._get.pooch.retrieve")
def test_download_with_parameter(mock_retrieve):
    def side_effect(url, known_hash, fname, path, **kwargs):
        full_path = os.path.join(path, fname)
        os.makedirs(path, exist_ok=True)
        with open(full_path, "w") as f:
            f.write("source\ttarget\tweight\nA\tB\t0.9\n")
        return full_path

    mock_retrieve.side_effect = side_effect

    downloader = Downloader(cache_dir=None)
    resource = FileDownload(
        name="zenodo",
        url_s="https://zenodo.org/records/7773985/files/CollecTRI_source.tsv?download=1",
        lifetime=1,
    )

    paths1 = downloader.download(resource)
    assert isinstance(paths1, list)
    assert os.path.exists(paths1[0])
    assert "?download=1" not in paths1[0]

    with open(downloader.cache_file, "r") as f:
        cache = json.load(f)
    assert cache["zenodo"]["url"][0] == "https://zenodo.org/records/7773985/files/CollecTRI_source.tsv?download=1"
    # load resource from cache
    paths2 = downloader.download(resource)
    assert "tmp" in paths2[0]


@patch("requests.get")
def test_download_with_long_url(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json = lambda: {"data": "test content"}
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # Create a long URL that would exceed filename length limits
    long_url = "https://example.com/api/data/" + "x" * 200 + "?" + "y" * 200
    downloader = Downloader(cache_dir=None)
    resource = APIRequest(
        name="test_long_url",
        url_s=long_url,
        lifetime=1,
    )
    paths = downloader.download(resource)
    # Verify file path exists
    assert os.path.exists(paths[0])
    # Check filename length is within limits
    filename = os.path.basename(paths[0])
    assert len(filename) <= 150

    # Verify the downloaded file contains our mock data
    with open(paths[0], "r") as f:
        content = f.read()
        assert "test content" in content


@patch("requests.get")
def test_download_file_with_long_url(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = b"test file content"
    mock_response.raise_for_status = Mock()
    mock_response.headers = {"content-length": "15"}  # Length of "test file content"
    # Mock iter_content to return an iterator of our test content
    mock_response.iter_content = lambda chunk_size: iter([b"test file content"])
    mock_get.return_value = mock_response

    # Create a long URL that would exceed filename length limits
    long_url = "https://example.com/files/data/" + "x" * 200 + "?" + "y" * 200
    downloader = Downloader(cache_dir=None)
    resource = FileDownload(
        name="test_long_file_url",
        url_s=long_url,
        lifetime=1,
    )
    paths = downloader.download(resource)
    # Verify file path exists
    assert os.path.exists(paths[0])
    # Check filename length is within limits
    filename = os.path.basename(paths[0])
    assert len(filename) <= 150

    # Verify the downloaded file contains our mock data
    with open(paths[0], "rb") as f:
        content = f.read()
        assert b"test file content" in content


@patch("requests.get")
def test_api_request_long_query_string(mock_get):
    """Regression test for issue #433: short path + long query string → ENAMETOOLONG."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json = lambda: {"data": "test content"}
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # Reproduce the real-world pattern: short endpoint name, many query params
    conditions = [f"linear_sequence.ilike.*SEQ{i}*" for i in range(20)]
    query = "or=(" + ",".join(conditions) + ")"
    long_url = f"https://query-api.example.org/epitope_search?{query}"

    downloader = Downloader(cache_dir=None)
    resource = APIRequest(name="iedb_test", url_s=long_url, lifetime=1)
    paths = downloader.download(resource)

    assert os.path.exists(paths[0])
    filename = os.path.basename(paths[0])
    assert len(filename) <= 150, f"Filename too long: {len(filename)} chars"


@patch("requests.get")
def test_api_request_multiple_urls_distinct_cache_files(mock_get):
    """Multiple URLs to the same endpoint with different query params must not share a cache file.

    Regression test for issue #433: stripping query params caused every URL
    to the same path to collide on the same cached filename.
    """
    call_count = [0]

    def side_effect(url, **kwargs):
        call_count[0] += 1
        resp = Mock()
        resp.status_code = 200
        resp.json = lambda n=call_count[0]: {"result": n}
        resp.raise_for_status = Mock()
        return resp

    mock_get.side_effect = side_effect

    url_a = "https://example.com/api/search?filter=alpha"
    url_b = "https://example.com/api/search?filter=beta"

    downloader = Downloader(cache_dir=None)
    resource = APIRequest(name="search_test", url_s=[url_a, url_b], lifetime=1)
    paths = downloader.download(resource)

    # Each URL must produce a distinct cache file
    assert len(paths) == 2
    assert paths[0] != paths[1], "Different query params produced the same cache file"
    assert os.path.exists(paths[0])
    assert os.path.exists(paths[1])
