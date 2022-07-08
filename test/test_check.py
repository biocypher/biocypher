import pytest
from biocypher._check import VersionNode
from biocypher._driver import Driver


@pytest.fixture
def version_node():
    yield VersionNode(
        offline=True,
        from_config=True, 
        config_file="biocypher/_config/test_schema_config.yaml"
    )


def test_version_node(version_node):
    assert version_node.get_label() == "BioCypher"

def test_virtual_leaves_node(version_node):
    assert "WIKIPATHWAYS.Pathway" in version_node.leaves

def test_virtual_leaves_edge(version_node):
    pass