import pytest
from biocypher._check import VersionNode
from biocypher._driver import Driver


@pytest.fixture
def driver():
    # neo4j database needs to be running!
    d = Driver(increment_version=False)
    yield d

    # teardown
    d.close()


def test_version_node(driver):
    v = VersionNode(driver, from_config=True)
    assert v.get_label() == "BioCypher"


def test_multiple_ids(driver):
    v = VersionNode(driver, from_config=True)

    leaves = v.leaves

    assert "WIKIPATHWAYS.Pathway" in leaves