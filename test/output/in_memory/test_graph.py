"""Test suite for the Graph class."""

import pytest

from biocypher.output.in_memory._graph import Graph


@pytest.mark.parametrize("length", [4], scope="function")
def test_graph_add_nodes(_get_nodes, length):
    """Test adding nodes to the Graph."""
    # Initialize a graph
    graph = Graph()

    # Get test nodes from fixture
    nodes = _get_nodes

    # Convert BioCypherNode objects to NodeInfo tuples
    node_tuples = []
    for node in nodes:
        node_tuple = (node.node_id, node.node_label, node.properties)
        node_tuples.append(node_tuple)

    # Add nodes to the graph
    graph.add_nodes(node_tuples)

    # Verify node count is correct (2 nodes per length unit)
    assert len(graph.nodes) == 2 * length

    # Verify some specific nodes exist
    assert graph.get_node("p1") is not None
    assert graph.get_node("m1") is not None

    # Verify node properties are correctly stored
    p1 = graph.get_node("p1")
    assert p1.label == "protein"
    assert p1.properties["score"] == 4.0
    assert p1.properties["taxon"] == 9606
    assert p1.properties["genes"] == ["gene1", "gene2"]


@pytest.mark.parametrize("length", [4], scope="function")
def test_graph_add_edges(_get_nodes, _get_edges, length):
    """Test adding edges to the Graph."""
    # Initialize a graph
    graph = Graph()

    # First, add all nodes from fixture
    nodes = _get_nodes
    node_tuples = []
    for node in nodes:
        node_tuple = (node.node_id, node.node_label, node.properties)
        node_tuples.append(node_tuple)
    graph.add_nodes(node_tuples)

    # Now add edges
    edges = _get_edges
    edge_tuples = []
    for edge in edges:
        print(edge)
        edge_tuple = (edge.relationship_id, edge.source_id, edge.target_id, edge.relationship_label, edge.properties)

        print("edge_tuple: ", len(edge_tuple))
        edge_tuples.append(edge_tuple)

    # Add edges to the graph
    print(edge_tuples)

    graph.add_edges(edge_tuples)
    print(graph.edges)

    # Verify edge count is correct (2 edges per length unit)
    print(length)

    assert len(graph.edges) == 2 * length

    # Verify edges connected to a specific node
    p1_edges = graph.get_node_edges("p1")
    assert len(p1_edges) > 0

    # Verify edge properties are correctly stored
    edge = next((e for e in graph.edges if e.id == "prel0"), None)
    assert edge is not None
    assert edge.label == "PERTURBED_IN_DISEASE"
    assert edge.properties["residue"] == "T253"
    assert edge.properties["level"] == 4


@pytest.mark.parametrize("length", [4], scope="function")
def test_graph_clear(_get_nodes):
    """Test clearing the graph."""
    # Initialize a graph
    graph = Graph()

    # Add nodes
    nodes = _get_nodes
    node_tuples = [(n.node_id, n.node_label, n.properties) for n in nodes]
    graph.add_nodes(node_tuples)

    # Verify nodes were added
    assert len(graph.nodes) > 0

    # Clear the graph
    graph.clear()

    # Verify graph is empty
    assert len(graph.nodes) == 0
    assert len(graph.edges) == 0
    assert not hasattr(graph, "_node_ids") or len(graph._node_ids) == 0
