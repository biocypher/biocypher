"""Comprehensive tests for the Graph class."""

import pytest
import json

from biocypher import Graph, Node, Edge, HyperEdge


class TestGraphInitialization:
    """Test graph initialization and basic properties."""

    def test_graph_creation(self):
        """Test basic graph creation."""
        graph = Graph("test_graph")
        assert graph.name == "test_graph"
        assert graph.directed is True
        assert len(graph) == 0

    def test_graph_creation_undirected(self):
        """Test undirected graph creation."""
        graph = Graph("test_graph", directed=False)
        assert graph.directed is False

    def test_graph_repr(self):
        """Test graph string representation."""
        graph = Graph("test_graph")
        assert "test_graph" in str(graph)
        assert "nodes=0" in str(graph)


class TestNodeOperations:
    """Test node addition, querying, and management."""

    def setup_method(self):
        """Set up test graph."""
        self.graph = Graph("test_graph")

    def test_add_node_basic(self):
        """Test basic node addition."""
        result = self.graph.add_node("node1", "protein", {"name": "TP53"})
        assert result is True
        assert self.graph.has_node("node1")
        assert len(self.graph) == 1

    def test_add_node_with_properties(self):
        """Test node addition with properties."""
        properties = {"name": "TP53", "function": "tumor_suppressor"}
        result = self.graph.add_node("node1", "protein", properties)
        assert result is True

        node = self.graph.get_node("node1")
        assert node.id == "node1"
        assert node.type == "protein"
        assert node.properties == properties

    def test_add_duplicate_node(self):
        """Test adding duplicate node returns False."""
        self.graph.add_node("node1", "protein")
        result = self.graph.add_node("node1", "protein")
        assert result is False
        assert len(self.graph) == 1

    def test_get_node(self):
        """Test getting node by ID."""
        self.graph.add_node("node1", "protein", {"name": "TP53"})
        node = self.graph.get_node("node1")
        assert node is not None
        assert node.id == "node1"
        assert node.type == "protein"

    def test_get_nonexistent_node(self):
        """Test getting nonexistent node returns None."""
        node = self.graph.get_node("nonexistent")
        assert node is None

    def test_get_nodes_by_type(self):
        """Test getting nodes filtered by type."""
        self.graph.add_node("node1", "protein", {"name": "TP53"})
        self.graph.add_node("node2", "protein", {"name": "BRAF"})
        self.graph.add_node("node3", "disease", {"name": "Cancer"})

        proteins = self.graph.get_nodes("protein")
        assert len(proteins) == 2
        assert all(node.type == "protein" for node in proteins)

        diseases = self.graph.get_nodes("disease")
        assert len(diseases) == 1
        assert diseases[0].type == "disease"

    def test_get_all_nodes(self):
        """Test getting all nodes."""
        self.graph.add_node("node1", "protein")
        self.graph.add_node("node2", "disease")

        all_nodes = self.graph.get_nodes()
        assert len(all_nodes) == 2

    def test_get_node_ids(self):
        """Test getting node IDs."""
        self.graph.add_node("node1", "protein")
        self.graph.add_node("node2", "protein")

        protein_ids = self.graph.get_node_ids("protein")
        assert protein_ids == {"node1", "node2"}

    def test_remove_node(self):
        """Test node removal."""
        self.graph.add_node("node1", "protein")
        assert self.graph.has_node("node1")

        result = self.graph.remove_node("node1")
        assert result is True
        assert not self.graph.has_node("node1")
        assert len(self.graph) == 0

    def test_remove_nonexistent_node(self):
        """Test removing nonexistent node returns False."""
        result = self.graph.remove_node("nonexistent")
        assert result is False


class TestEdgeOperations:
    """Test edge addition, querying, and management."""

    def setup_method(self):
        """Set up test graph with nodes."""
        self.graph = Graph("test_graph")
        self.graph.add_node("node1", "protein")
        self.graph.add_node("node2", "protein")
        self.graph.add_node("node3", "disease")

    def test_add_edge_basic(self):
        """Test basic edge addition."""
        result = self.graph.add_edge("edge1", "interaction", "node1", "node2")
        assert result is True
        assert self.graph.has_edge("edge1")

    def test_add_edge_with_properties(self):
        """Test edge addition with properties."""
        properties = {"confidence": 0.8, "evidence": "literature"}
        result = self.graph.add_edge("edge1", "interaction", "node1", "node2", properties)
        assert result is True

        edge = self.graph.get_edge("edge1")
        assert edge.id == "edge1"
        assert edge.type == "interaction"
        assert edge.source == "node1"
        assert edge.target == "node2"
        assert edge.properties == properties

    def test_add_edge_nonexistent_nodes(self):
        """Test adding edge with nonexistent nodes raises ValueError."""
        with pytest.raises(ValueError, match="Source node 'nonexistent' does not exist"):
            self.graph.add_edge("edge1", "interaction", "nonexistent", "node2")

        with pytest.raises(ValueError, match="Target node 'nonexistent' does not exist"):
            self.graph.add_edge("edge1", "interaction", "node1", "nonexistent")

    def test_add_duplicate_edge(self):
        """Test adding duplicate edge returns False."""
        self.graph.add_edge("edge1", "interaction", "node1", "node2")
        result = self.graph.add_edge("edge1", "interaction", "node1", "node2")
        assert result is False

    def test_get_edge(self):
        """Test getting edge by ID."""
        self.graph.add_edge("edge1", "interaction", "node1", "node2")
        edge = self.graph.get_edge("edge1")
        assert edge is not None
        assert edge.id == "edge1"

    def test_get_nonexistent_edge(self):
        """Test getting nonexistent edge returns None."""
        edge = self.graph.get_edge("nonexistent")
        assert edge is None

    def test_get_edges_by_type(self):
        """Test getting edges filtered by type."""
        self.graph.add_edge("edge1", "interaction", "node1", "node2")
        self.graph.add_edge("edge2", "interaction", "node2", "node3")
        self.graph.add_edge("edge3", "causes", "node1", "node3")

        interactions = self.graph.get_edges("interaction")
        assert len(interactions) == 2
        assert all(edge.type == "interaction" for edge in interactions)

    def test_get_edges_between(self):
        """Test getting edges between specific nodes."""
        self.graph.add_edge("edge1", "interaction", "node1", "node2")
        self.graph.add_edge("edge2", "interaction", "node2", "node1")
        self.graph.add_edge("edge3", "causes", "node1", "node3")

        edges = self.graph.get_edges_between("node1", "node2")
        assert len(edges) == 1  # Only outgoing edge from node1 to node2

        edges = self.graph.get_edges_between("node2", "node1")
        assert len(edges) == 1  # Only outgoing edge from node2 to node1

        edges = self.graph.get_edges_between("node1", "node2", edge_type="interaction")
        assert len(edges) == 1

        edges = self.graph.get_edges_between("node1", "node2", edge_type="causes")
        assert len(edges) == 0

    def test_remove_edge(self):
        """Test edge removal."""
        self.graph.add_edge("edge1", "interaction", "node1", "node2")
        assert self.graph.has_edge("edge1")

        result = self.graph.remove_edge("edge1")
        assert result is True
        assert not self.graph.has_edge("edge1")

    def test_remove_nonexistent_edge(self):
        """Test removing nonexistent edge returns False."""
        result = self.graph.remove_edge("nonexistent")
        assert result is False


class TestHyperEdgeOperations:
    """Test hyperedge addition, querying, and management."""

    def setup_method(self):
        """Set up test graph with nodes."""
        self.graph = Graph("test_graph")
        self.graph.add_node("node1", "protein")
        self.graph.add_node("node2", "protein")
        self.graph.add_node("node3", "protein")
        self.graph.add_node("node4", "protein")

    def test_add_hyperedge_basic(self):
        """Test basic hyperedge addition."""
        result = self.graph.add_hyperedge("hyper1", "complex", {"node1", "node2", "node3"})
        assert result is True
        assert self.graph.has_hyperedge("hyper1")

    def test_add_hyperedge_with_properties(self):
        """Test hyperedge addition with properties."""
        properties = {"function": "cell_cycle_control", "complex_type": "regulatory"}
        result = self.graph.add_hyperedge("hyper1", "complex", {"node1", "node2", "node3"}, properties)
        assert result is True

        hyperedge = self.graph.get_hyperedge("hyper1")
        assert hyperedge.id == "hyper1"
        assert hyperedge.type == "complex"
        assert hyperedge.nodes == {"node1", "node2", "node3"}
        assert hyperedge.properties == properties

    def test_add_hyperedge_nonexistent_nodes(self):
        """Test adding hyperedge with nonexistent nodes raises ValueError."""
        with pytest.raises(ValueError, match="Node 'nonexistent' does not exist"):
            self.graph.add_hyperedge("hyper1", "complex", {"node1", "nonexistent"})

    def test_add_hyperedge_insufficient_nodes(self):
        """Test adding hyperedge with less than 2 nodes raises ValueError."""
        with pytest.raises(ValueError, match="Hyperedge must connect at least 2 nodes"):
            self.graph.add_hyperedge("hyper1", "complex", {"node1"})

    def test_add_duplicate_hyperedge(self):
        """Test adding duplicate hyperedge returns False."""
        self.graph.add_hyperedge("hyper1", "complex", {"node1", "node2"})
        result = self.graph.add_hyperedge("hyper1", "complex", {"node1", "node2"})
        assert result is False

    def test_get_hyperedge(self):
        """Test getting hyperedge by ID."""
        self.graph.add_hyperedge("hyper1", "complex", {"node1", "node2"})
        hyperedge = self.graph.get_hyperedge("hyper1")
        assert hyperedge is not None
        assert hyperedge.id == "hyper1"

    def test_get_nonexistent_hyperedge(self):
        """Test getting nonexistent hyperedge returns None."""
        hyperedge = self.graph.get_hyperedge("nonexistent")
        assert hyperedge is None

    def test_get_hyperedges_by_type(self):
        """Test getting hyperedges filtered by type."""
        self.graph.add_hyperedge("hyper1", "complex", {"node1", "node2"})
        self.graph.add_hyperedge("hyper2", "complex", {"node2", "node3"})
        self.graph.add_hyperedge("hyper3", "pathway", {"node1", "node2", "node3"})

        complexes = self.graph.get_hyperedges("complex")
        assert len(complexes) == 2
        assert all(hyperedge.type == "complex" for hyperedge in complexes)


class TestGraphTraversal:
    """Test graph traversal operations."""

    def setup_method(self):
        """Set up test graph with nodes and edges."""
        self.graph = Graph("test_graph")
        # Add nodes
        self.graph.add_node("A", "protein")
        self.graph.add_node("B", "protein")
        self.graph.add_node("C", "protein")
        self.graph.add_node("D", "disease")
        self.graph.add_node("E", "disease")

        # Add edges
        self.graph.add_edge("A_B", "interaction", "A", "B")
        self.graph.add_edge("B_C", "interaction", "B", "C")
        self.graph.add_edge("C_D", "causes", "C", "D")
        self.graph.add_edge("A_E", "causes", "A", "E")

    def test_get_neighbors_both(self):
        """Test getting neighbors in both directions."""
        neighbors = self.graph.get_neighbors("B")
        assert neighbors == {"A", "C"}

    def test_get_neighbors_outgoing(self):
        """Test getting outgoing neighbors."""
        neighbors = self.graph.get_neighbors("B", direction="out")
        assert neighbors == {"C"}

    def test_get_neighbors_incoming(self):
        """Test getting incoming neighbors."""
        neighbors = self.graph.get_neighbors("B", direction="in")
        assert neighbors == {"A"}

    def test_get_connected_edges(self):
        """Test getting connected edges."""
        edges = self.graph.get_connected_edges("B")
        assert len(edges) == 2
        edge_types = {edge.type for edge in edges}
        assert edge_types == {"interaction"}

    def test_find_paths(self):
        """Test path finding between nodes."""
        paths = self.graph.find_paths("A", "D")
        assert len(paths) == 1
        path = paths[0]
        assert len(path) == 3  # A -> B -> C -> D

    def test_find_paths_max_length(self):
        """Test path finding with max length constraint."""
        paths = self.graph.find_paths("A", "D", max_length=2)
        assert len(paths) == 0  # No path of length 2 or less

        paths = self.graph.find_paths("A", "D", max_length=4)
        assert len(paths) == 1  # Path exists with length 3

    def test_find_paths_no_path(self):
        """Test path finding when no path exists."""
        self.graph.add_node("F", "protein")
        paths = self.graph.find_paths("A", "F")
        assert len(paths) == 0


class TestGraphAnalysis:
    """Test graph analysis and statistics."""

    def setup_method(self):
        """Set up test graph."""
        self.graph = Graph("test_graph")

    def test_get_statistics_empty(self):
        """Test statistics for empty graph."""
        stats = self.graph.get_statistics()
        assert stats["basic"]["nodes"] == 0
        assert stats["basic"]["edges"] == 0
        assert stats["basic"]["hyperedges"] == 0

    def test_get_statistics_with_data(self):
        """Test statistics for graph with data."""
        # Add nodes
        self.graph.add_node("node1", "protein")
        self.graph.add_node("node2", "protein")
        self.graph.add_node("node3", "disease")

        # Add edges
        self.graph.add_edge("edge1", "interaction", "node1", "node2")
        self.graph.add_edge("edge2", "causes", "node1", "node3")

        # Add hyperedge
        self.graph.add_hyperedge("hyper1", "complex", {"node1", "node2"})

        stats = self.graph.get_statistics()
        assert stats["basic"]["nodes"] == 3
        assert stats["basic"]["edges"] == 2
        assert stats["basic"]["hyperedges"] == 1
        assert stats["basic"]["node_types"] == 2
        assert stats["basic"]["edge_types"] == 2
        assert stats["basic"]["hyperedge_types"] == 1

        # Check type breakdowns
        assert stats["node_types"]["protein"] == 2
        assert stats["node_types"]["disease"] == 1
        assert stats["edge_types"]["interaction"] == 1
        assert stats["edge_types"]["causes"] == 1
        assert stats["hyperedge_types"]["complex"] == 1

    def test_get_subgraph(self):
        """Test subgraph extraction."""
        # Add nodes and edges
        self.graph.add_node("A", "protein")
        self.graph.add_node("B", "protein")
        self.graph.add_node("C", "protein")
        self.graph.add_edge("A_B", "interaction", "A", "B")
        self.graph.add_edge("B_C", "interaction", "B", "C")
        self.graph.add_edge("A_C", "interaction", "A", "C")

        # Extract subgraph
        subgraph = self.graph.get_subgraph({"A", "B"})
        assert len(subgraph) == 2
        assert subgraph.has_node("A")
        assert subgraph.has_node("B")
        assert not subgraph.has_node("C")
        assert subgraph.has_edge("A_B")
        assert not subgraph.has_edge("B_C")

    def test_get_subgraph_without_edges(self):
        """Test subgraph extraction without edges."""
        self.graph.add_node("A", "protein")
        self.graph.add_node("B", "protein")
        self.graph.add_edge("A_B", "interaction", "A", "B")

        subgraph = self.graph.get_subgraph({"A", "B"}, include_edges=False)
        assert len(subgraph) == 2
        assert not subgraph.has_edge("A_B")


class TestSerialization:
    """Test graph serialization and deserialization."""

    def setup_method(self):
        """Set up test graph."""
        self.graph = Graph("test_graph")

    def test_to_dict(self):
        """Test graph to dictionary conversion."""
        # Add data
        self.graph.add_node("node1", "protein", {"name": "TP53"})
        self.graph.add_node("node2", "protein", {"name": "BRAF"})
        self.graph.add_edge("edge1", "interaction", "node1", "node2", {"confidence": 0.8})
        self.graph.add_hyperedge("hyper1", "complex", {"node1", "node2"}, {"function": "control"})

        # Convert to dict
        data = self.graph.to_dict()
        assert data["name"] == "test_graph"
        assert data["directed"] is True
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1
        assert len(data["hyperedges"]) == 1

    def test_from_dict(self):
        """Test graph creation from dictionary."""
        # Create data
        data = {
            "name": "test_graph",
            "directed": True,
            "nodes": [{"id": "node1", "type": "protein", "properties": {"name": "TP53"}}],
            "edges": [
                {
                    "id": "edge1",
                    "type": "interaction",
                    "source": "node1",
                    "target": "node2",
                    "properties": {"confidence": 0.8},
                }
            ],
            "hyperedges": [
                {"id": "hyper1", "type": "complex", "nodes": ["node1", "node2"], "properties": {"function": "control"}}
            ],
        }

        # Create graph from dict
        graph = Graph.from_dict(data)
        assert graph.name == "test_graph"
        assert graph.directed is True
        assert graph.has_node("node1")
        assert graph.has_edge("edge1")
        assert graph.has_hyperedge("hyper1")

    def test_to_json(self):
        """Test graph to JSON conversion."""
        self.graph.add_node("node1", "protein", {"name": "TP53"})
        json_str = self.graph.to_json()

        # Verify it's valid JSON
        data = json.loads(json_str)
        assert data["name"] == "test_graph"
        assert len(data["nodes"]) == 1

    def test_from_json(self):
        """Test graph creation from JSON."""
        # Create JSON data
        json_data = {
            "name": "test_graph",
            "directed": True,
            "nodes": [{"id": "node1", "type": "protein", "properties": {"name": "TP53"}}],
            "edges": [],
            "hyperedges": [],
        }

        json_str = json.dumps(json_data, indent=2)
        graph = Graph.from_json_string(json_str)
        assert graph.name == "test_graph"
        assert graph.has_node("node1")

    def test_from_json_into_existing(self):
        """Test loading JSON into existing graph."""
        # Add initial data
        self.graph.add_node("existing", "protein")

        # Create JSON data
        json_data = {
            "name": "new_graph",
            "directed": False,
            "nodes": [{"id": "new_node", "type": "disease", "properties": {"name": "Cancer"}}],
            "edges": [],
            "hyperedges": [],
        }

        json_str = json.dumps(json_data, indent=2)
        self.graph.from_json(json_str)

        # Should have new data
        assert self.graph.has_node("new_node")
        # Should not have old data (the from_json method replaces the entire graph)
        assert not self.graph.has_node("existing")


class TestGraphOperations:
    """Test graph operations and utilities."""

    def setup_method(self):
        """Set up test graph."""
        self.graph = Graph("test_graph")

    def test_len(self):
        """Test graph length (number of nodes)."""
        assert len(self.graph) == 0
        self.graph.add_node("node1", "protein")
        assert len(self.graph) == 1

    def test_contains(self):
        """Test node containment."""
        self.graph.add_node("node1", "protein")
        assert "node1" in self.graph
        assert "nonexistent" not in self.graph

    def test_iter(self):
        """Test graph iteration over nodes."""
        self.graph.add_node("node1", "protein")
        self.graph.add_node("node2", "disease")

        nodes = list(self.graph)
        assert len(nodes) == 2
        node_ids = {node.id for node in nodes}
        assert node_ids == {"node1", "node2"}

    def test_clear(self):
        """Test clearing the graph."""
        self.graph.add_node("node1", "protein")
        self.graph.add_node("node2", "protein")
        self.graph.add_edge("edge1", "interaction", "node1", "node2")

        self.graph.clear()
        assert len(self.graph) == 0
        assert not self.graph.has_edge("edge1")


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test graph."""
        self.graph = Graph("test_graph")

    def test_node_validation(self):
        """Test node validation."""
        # Test with non-string ID
        with pytest.raises(ValueError, match="Node ID must be a string"):
            Node(123, "protein")

        # Test with non-string type
        with pytest.raises(ValueError, match="Node type must be a string"):
            Node("node1", 123)

    def test_edge_validation(self):
        """Test edge validation."""
        # Test with non-string source
        with pytest.raises(ValueError, match="Edge source must be a string"):
            Edge("edge1", "interaction", 123, "target")

        # Test with non-string target
        with pytest.raises(ValueError, match="Edge target must be a string"):
            Edge("edge1", "interaction", "source", 123)

    def test_hyperedge_validation(self):
        """Test hyperedge validation."""
        # Test with non-set nodes
        with pytest.raises(ValueError, match="HyperEdge nodes must be a set"):
            HyperEdge("hyper1", "complex", ["node1", "node2"])

        # Test with insufficient nodes
        with pytest.raises(ValueError, match="HyperEdge must connect at least 2 nodes"):
            HyperEdge("hyper1", "complex", {"node1"})

    def test_large_graph_performance(self):
        """Test performance with larger graph."""
        # Add many nodes
        for i in range(1000):
            self.graph.add_node(f"node{i}", "protein")

        # Add many edges
        for i in range(999):
            self.graph.add_edge(f"edge{i}", "interaction", f"node{i}", f"node{i+1}")

        # Test operations still work
        assert len(self.graph) == 1000
        assert self.graph.has_node("node500")
        assert self.graph.has_edge("edge500")

        # Test statistics
        stats = self.graph.get_statistics()
        assert stats["basic"]["nodes"] == 1000
        assert stats["basic"]["edges"] == 999


class TestIntegration:
    """Test integration with other components."""

    def test_with_bio_cypher_agent(self):
        """Test Graph integration with BioCypherWorkflow."""
        from biocypher import create_workflow

        # Create agent
        agent = create_workflow("test_agent")

        # Add data through agent
        result1 = agent.add_node("protein1", "protein", name="TP53")
        result2 = agent.add_node("protein2", "protein", name="BRAF")
        result3 = agent.add_edge("interaction1", "interaction", "protein1", "protein2", confidence=0.8)

        # Verify all operations succeeded
        assert result1 is True, "Failed to add first node"
        assert result2 is True, "Failed to add second node"
        assert result3 is True, "Failed to add edge"

        # Get underlying graph
        graph = agent.get_graph()

        # Test graph operations with more detailed assertions
        graph_len = len(graph)
        assert graph_len == 2, f"Expected 2 nodes, got {graph_len}"

        has_protein1 = graph.has_node("protein1")
        assert has_protein1, "Expected node 'protein1' to exist"

        has_interaction1 = graph.has_edge("interaction1")
        assert has_interaction1, "Expected edge 'interaction1' to exist"

        # Test statistics with more detailed debugging
        stats = graph.get_statistics()
        basic_stats = stats.get("basic", {})
        nodes_count = basic_stats.get("nodes", 0)
        edges_count = basic_stats.get("edges", 0)

        assert nodes_count == 2, f"Expected 2 nodes in stats, got {nodes_count}"
        assert edges_count == 1, f"Expected 1 edge in stats, got {edges_count}"
