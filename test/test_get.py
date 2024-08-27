from datetime import datetime, timedelta
import os
import json

from hypothesis import given
from hypothesis import strategies as st
import pytest

from biocypher._get import Resource, APIRequest, Downloader


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


@given(
    st.builds(
        Resource,
        name=st.text(),
        url_s=st.text(),
        lifetime=st.integers(),
        is_dir=st.booleans(),
    )
)
def test_resource(resource):
    assert isinstance(resource.name, str)
    assert isinstance(resource.url_s, str) or isinstance(resource.url_s, list)
    assert isinstance(resource.lifetime, int)


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
def test_download_file(downloader):
    resource = Resource(
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
    downloader.cache_dict["test_resource"]["date_downloaded"] = str(
        datetime.now() - timedelta(days=8)
    )

    paths = downloader.download(resource)
    assert len(paths) == 1
    # should download again
    assert initial_download_time < os.path.getmtime(paths[0])


@pytest.mark.parametrize(
    "downloader",
    [
        "downloader_without_specified_cache_dir",
        "downloader_with_specified_cache_dir",
    ],
    indirect=True,
)
def test_download_lists(downloader):
    resource1 = Resource(
        name="test_resource1",
        url_s=[
            "https://github.com/biocypher/biocypher/raw/main/biocypher/_config/test_config.yaml",
            "https://github.com/biocypher/biocypher/raw/main/biocypher/_config/test_schema_config_disconnected.yaml",
        ],
    )
    resource2 = Resource(
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
        os.path.realpath(
            os.path.join(
                downloader.cache_dir, "test_resource1", "test_config.yaml"
            )
        ),
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


def test_download_directory_and_caching():
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
    assert len(paths) == 17
    assert "tmp" in paths[0]


def test_download_zip_and_expiration():
    # use temp dir, no cache file present
    downloader = Downloader(cache_dir=None)
    assert os.path.exists(downloader.cache_dir)
    assert os.path.exists(downloader.cache_file)
    resource = Resource(
        "test_resource",
        "https://github.com/biocypher/biocypher/raw/main/test/test_CSVs.zip",
        lifetime=7,
    )
    api = APIRequest(
        "test_api",
        "https://rest.uniprot.org/uniprotkb/P12345.json",
        lifetime=7,
    )
    paths = downloader.download(resource, api)
    with open(downloader.cache_file, "r") as f:
        cache = json.load(f)
    assert (
        cache["test_resource"]["url"][0]
        == "https://github.com/biocypher/biocypher/raw/main/test/test_CSVs.zip",
        cache["test_api"]["url"][0]
        == "https://rest.uniprot.org/uniprotkb/P12345.json",
    )
    assert cache["test_resource"]["lifetime"] == 7
    assert cache["test_api"]["lifetime"] == 7
    assert cache["test_resource"]["date_downloaded"]
    assert cache["test_api"]["date_downloaded"]

    for path in paths:
        assert os.path.exists(path)

    # use files downloaded here and manipulate cache file to test expiration
    downloader.cache_dict["test_resource"]["date_downloaded"] = str(
        datetime.now() - timedelta(days=4)
    )
    downloader.cache_dict["test_api"]["date_downloaded"] = str(
        datetime.now() - timedelta(days=4)
    )

    paths = downloader.download(resource, api)
    # should not download again
    assert "tmp" in paths[0]
    assert "tmp" in paths[1]

    # minus 8 days from date_downloaded
    downloader.cache_dict["test_resource"]["date_downloaded"] = str(
        datetime.now() - timedelta(days=8)
    )
    downloader.cache_dict["test_api"]["date_downloaded"] = str(
        datetime.now() - timedelta(days=8)
    )

    paths = downloader.download(resource, api)
    # should download again
    assert paths[0] is not None
    assert paths[1] is not None


@pytest.mark.parametrize(
    "downloader",
    [
        "downloader_without_specified_cache_dir",
        "downloader_with_specified_cache_dir",
    ],
    indirect=True,
)
def test_cache_api_request(downloader):
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
    test_paths = downloader.download(
        api1, api2
    )  # get the path(s) of cached API request(s)
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


@pytest.mark.parametrize(
    "downloader",
    [
        "downloader_without_specified_cache_dir",
        "downloader_with_specified_cache_dir",
    ],
    indirect=True,
)
def test_path_splitted(downloader):
    resourc1 = Resource(
        "test_resource1",
        "https://github.com/biocypher/biocypher/raw/main/biocypher/_config/test_config.yaml",
        lifetime=7,
    )
    resource2 = Resource(
        name="test_resource2",
        url_s=[
            "https://github.com/biocypher/biocypher/raw/main/biocypher/_config/test_config.yaml",
            "https://github.com/biocypher/biocypher/raw/main/biocypher/_config/test_schema_config_disconnected.yaml",
        ],
    )

    paths = downloader.download(resourc1, resource2)
    assert isinstance(paths, list)
    assert len(paths) == 3  # if len(paths) == 3, then not splitted


def test_download_with_parameter():
    downloader = Downloader(cache_dir=None)
    resource = Resource(
        name="zenodo",
        url_s="https://zenodo.org/records/7773985/files/CollecTRI_source.tsv?download=1",
        lifetime=1,
    )

    paths1 = downloader.download(resource)
    assert isinstance(paths1, list)
    assert os.path.exists(paths1[0])

    # load resource from cache
    paths2 = downloader.download(resource)
    assert "tmp" in paths2[0]
