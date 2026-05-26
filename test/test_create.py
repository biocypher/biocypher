import pytest

from hypothesis import (
    given,
    strategies as st,
)

from biocypher._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode


@given(st.builds(BioCypherNode))
def test_node(node):
    assert isinstance(node.get_id(), str)
    assert isinstance(node.get_label(), str)
    assert isinstance(node.get_properties(), dict)
    assert isinstance(node.get_dict(), dict)

    assert "id" in node.get_properties().keys()


@given(st.builds(BioCypherEdge))
def test_edge(edge):
    assert isinstance(edge.get_id(), str) or edge.get_id() is None
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
        BioCypherRelAsNode("str", 1, 2.5122)


def test_edge_all_reserved_keywords_removed():
    """BioCypherEdge must remove all reserved keywords, not just the first one found.

    Previously the keyword checks used elif chains, so if :TYPE was present,
    the 'id' and '_ID' checks were silently skipped.
    """
    edge = BioCypherEdge(
        source_id="s1",
        target_id="t1",
        relationship_label="rel",
        properties={":TYPE": "foo", "id": "bar", "_ID": "baz", "score": 0.9},
    )
    assert ":TYPE" not in edge.properties
    assert "id" not in edge.properties
    assert "_ID" not in edge.properties
    assert edge.properties["score"] == 0.9


def test_node_list_property_with_non_string_values():
    """BioCypherNode must not crash when a list property contains non-string values.

    Previously the newline-sanitisation loop called .replace() on every list
    element without checking the type, causing AttributeError for ints, floats,
    booleans, and None values.
    """
    node = BioCypherNode(
        node_id="n1",
        node_label="Test",
        properties={
            "int_list": [1, 2, 3],
            "float_list": [1.1, 2.2],
            "bool_list": [True, False],
            "mixed_list": ["a", 1, None],
            "str_list": ["hello\nworld", "foo\rbar"],
        },
    )
    assert node.properties["int_list"] == [1, 2, 3]
    assert node.properties["float_list"] == [1.1, 2.2]
    assert node.properties["bool_list"] == [True, False]
    assert node.properties["mixed_list"] == ["a", 1, None]
    # string entries still get newlines sanitised
    assert node.properties["str_list"] == ["hello world", "foo bar"]
