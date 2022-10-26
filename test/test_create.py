from typing import Union

from hypothesis import given
from hypothesis import strategies as st
import pytest

from biocypher._create import (
    VersionNode,
    BioCypherEdge,
    BioCypherNode,
    BioCypherRelAsNode,
)

__all__ = [
    'test_edge',
    'test_getting_properties_via_config',
    'test_node',
    'test_rel_as_node',
    'test_rel_as_node_invalid_node',
    'test_version_node',
    'test_virtual_leaves_node',
    'version_node',
]


@pytest.fixture
def version_node():
    yield VersionNode(
        offline=True,
        from_config=True,
        config_file='biocypher/_config/test_schema_config.yaml',
    )


def test_version_node(version_node):
    assert version_node.get_label() == 'BioCypher'


def test_virtual_leaves_node(version_node):
    assert 'wikipathways.pathway' in version_node.leaves


def test_getting_properties_via_config(version_node):
    assert 'name' in version_node.leaves['protein'].get('properties').keys()


@given(st.builds(BioCypherNode))
def test_node(node):
    assert isinstance(node.get_id(), str)
    assert isinstance(node.get_label(), str)
    assert isinstance(node.get_properties(), dict)
    assert isinstance(node.get_dict(), dict)

    assert 'id' in node.get_properties().keys()


@given(st.builds(BioCypherEdge))
def test_edge(edge):
    assert isinstance(edge.get_id(), str) or edge.get_id() == None
    assert isinstance(edge.get_source_id(), str)
    assert isinstance(edge.get_target_id(), str)
    assert isinstance(edge.get_label(), str)
    assert isinstance(edge.get_properties(), dict)
    assert isinstance(edge.get_dict(), dict)


@given(st.builds(BioCypherRelAsNode))
def test_rel_as_node(rel_as_node):
    assert isinstance(rel_as_node.get_node(), BioCypherNode)
    assert isinstance(rel_as_node.get_source_edge(), BioCypherEdge)
    assert isinstance(rel_as_node.get_target_edge(), BioCypherEdge)


def test_rel_as_node_invalid_node():
    with pytest.raises(TypeError):
        BioCypherRelAsNode('str', 1, 2.5122)
