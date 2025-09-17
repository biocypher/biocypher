"""Comprehensive tests for the BioCypherWorkflow class."""

import pytest
import json
import tempfile
import os

from biocypher import create_workflow


class TestWorkflowInitialization:
    """Test workflow initialization and basic properties."""

    def test_workflow_creation_basic(self):
        """Test basic workflow creation."""
        workflow = create_workflow("test_workflow")
        assert workflow.name == "test_workflow"
        assert len(workflow) == 0

    def test_workflow_creation_with_parameters(self):
        """Test workflow creation with all parameters."""
        workflow = create_workflow(
            name="test_workflow",
            directed=False,
            schema={"protein": {"represented_as": "node"}},
            head_ontology_url="https://example.com/ontology",
        )
        assert workflow.name == "test_workflow"
        assert workflow.graph.directed is False
        assert workflow.schema is not None
        assert workflow.head_ontology_url == "https://example.com/ontology"

    def test_workflow_creation_with_schema_dict(self):
        """Test workflow creation with schema dictionary."""
        schema = {
            "protein": {"represented_as": "node", "properties": {"name": "str", "function": "str"}},
            "interaction": {
                "represented_as": "edge",
                "source": "protein",
                "target": "protein",
                "properties": {"confidence": "float"},
            },
        }

        workflow = create_workflow("test_workflow", schema=schema)
        assert workflow.schema == schema

    def test_workflow_creation_with_schema_file(self):
        """Test workflow creation with schema file."""
        # Create temporary schema file
        schema_content = """
protein:
  represented_as: node
  properties:
    name: str
    function: str
interaction:
  represented_as: edge
  source: protein
  target: protein
  properties:
    confidence: float
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(schema_content)
            schema_file = f.name

        try:
            workflow = create_workflow("test_workflow", schema_file=schema_file)
            assert workflow.schema is not None
            assert "protein" in workflow.schema
            assert "interaction" in workflow.schema
        finally:
            os.unlink(schema_file)

    def test_workflow_repr(self):
        """Test workflow string representation."""
        workflow = create_workflow("test_workflow")
        assert "test_workflow" in str(workflow)
        assert "nodes=0" in str(workflow)


class TestNodeOperations:
    """Test node addition, querying, and management."""

    def setup_method(self):
        """Set up test workflow."""
        self.workflow = create_workflow("test_workflow")

    def test_add_node_basic(self):
        """Test basic node addition."""
        result = self.workflow.add_node("node1", "protein", name="TP53")
        assert result is True
        assert self.workflow.has_node("node1")
        assert len(self.workflow) == 1

    def test_add_node_with_properties(self):
        """Test node addition with properties."""
        result = self.workflow.add_node(
            "node1", "protein", name="TP53", function="tumor_suppressor", uniprot_id="P04637"
        )
        assert result is True

        node = self.workflow.get_node("node1")
        assert node.id == "node1"
        assert node.type == "protein"
        assert node.properties["name"] == "TP53"
        assert node.properties["function"] == "tumor_suppressor"
        assert node.properties["uniprot_id"] == "P04637"

    def test_add_duplicate_node(self):
        """Test adding duplicate node returns False."""
        self.workflow.add_node("node1", "protein")
        result = self.workflow.add_node("node1", "protein")
        assert result is False
        assert len(self.workflow) == 1

    def test_get_node(self):
        """Test getting node by ID."""
        self.workflow.add_node("node1", "protein", name="TP53")
        node = self.workflow.get_node("node1")
        assert node is not None
        assert node.id == "node1"
        assert node.type == "protein"

    def test_get_nonexistent_node(self):
        """Test getting nonexistent node returns None."""
        node = self.workflow.get_node("nonexistent")
        assert node is None

    def test_get_nodes_by_type(self):
        """Test getting nodes filtered by type."""
        self.workflow.add_node("node1", "protein", name="TP53")
        self.workflow.add_node("node2", "protein", name="BRAF")
        self.workflow.add_node("node3", "disease", name="Cancer")

        proteins = self.workflow.get_nodes("protein")
        assert len(proteins) == 2
        assert all(node.type == "protein" for node in proteins)

        diseases = self.workflow.get_nodes("disease")
        assert len(diseases) == 1
        assert diseases[0].type == "disease"

    def test_get_all_nodes(self):
        """Test getting all nodes."""
        self.workflow.add_node("node1", "protein")
        self.workflow.add_node("node2", "disease")

        all_nodes = self.workflow.get_nodes()
        assert len(all_nodes) == 2

    def test_remove_node(self):
        """Test node removal."""
        self.workflow.add_node("node1", "protein")
        assert self.workflow.has_node("node1")

        result = self.workflow.remove_node("node1")
        assert result is True
        assert not self.workflow.has_node("node1")
        assert len(self.workflow) == 0

    def test_remove_nonexistent_node(self):
        """Test removing nonexistent node returns False."""
        result = self.workflow.remove_node("nonexistent")
        assert result is False


class TestEdgeOperations:
    """Test edge addition, querying, and management."""

    def setup_method(self):
        """Set up test workflow with nodes."""
        self.workflow = create_workflow("test_workflow")
        self.workflow.add_node("node1", "protein")
        self.workflow.add_node("node2", "protein")
        self.workflow.add_node("node3", "disease")

    def test_add_edge_basic(self):
        """Test basic edge addition."""
        result = self.workflow.add_edge("edge1", "interaction", "node1", "node2")
        assert result is True
        assert self.workflow.has_edge("edge1")

    def test_add_edge_with_properties(self):
        """Test edge addition with properties."""
        result = self.workflow.add_edge(
            "edge1",
            "interaction",
            "node1",
            "node2",
            confidence=0.8,
            evidence="literature",
            method="co-immunoprecipitation",
        )
        assert result is True

        edge = self.workflow.get_edge("edge1")
        assert edge.id == "edge1"
        assert edge.type == "interaction"
        assert edge.source == "node1"
        assert edge.target == "node2"
        assert edge.properties["confidence"] == 0.8
        assert edge.properties["evidence"] == "literature"
        assert edge.properties["method"] == "co-immunoprecipitation"

    def test_add_edge_nonexistent_nodes(self):
        """Test adding edge with nonexistent nodes raises ValueError."""
        with pytest.raises(ValueError, match="Source node 'nonexistent' does not exist"):
            self.workflow.add_edge("edge1", "interaction", "nonexistent", "node2")

        with pytest.raises(ValueError, match="Target node 'nonexistent' does not exist"):
            self.workflow.add_edge("edge1", "interaction", "node1", "nonexistent")

    def test_add_duplicate_edge(self):
        """Test adding duplicate edge returns False."""
        self.workflow.add_edge("edge1", "interaction", "node1", "node2")
        result = self.workflow.add_edge("edge1", "interaction", "node1", "node2")
        assert result is False

    def test_get_edge(self):
        """Test getting edge by ID."""
        self.workflow.add_edge("edge1", "interaction", "node1", "node2")
        edge = self.workflow.get_edge("edge1")
        assert edge is not None
        assert edge.id == "edge1"

    def test_get_nonexistent_edge(self):
        """Test getting nonexistent edge returns None."""
        edge = self.workflow.get_edge("nonexistent")
        assert edge is None

    def test_get_edges_by_type(self):
        """Test getting edges filtered by type."""
        self.workflow.add_edge("edge1", "interaction", "node1", "node2")
        self.workflow.add_edge("edge2", "interaction", "node2", "node3")
        self.workflow.add_edge("edge3", "causes", "node1", "node3")

        interactions = self.workflow.get_edges("interaction")
        assert len(interactions) == 2
        assert all(edge.type == "interaction" for edge in interactions)

    def test_get_edges_between(self):
        """Test getting edges between specific nodes."""
        self.workflow.add_edge("edge1", "interaction", "node1", "node2")
        self.workflow.add_edge("edge2", "interaction", "node2", "node1")
        self.workflow.add_edge("edge3", "causes", "node1", "node3")

        edges = self.workflow.get_edges_between("node1", "node2")
        assert len(edges) == 1  # Only outgoing edge from node1 to node2

        edges = self.workflow.get_edges_between("node2", "node1")
        assert len(edges) == 1  # Only outgoing edge from node2 to node1

        edges = self.workflow.get_edges_between("node1", "node2", edge_type="interaction")
        assert len(edges) == 1

        edges = self.workflow.get_edges_between("node1", "node2", edge_type="causes")
        assert len(edges) == 0

    def test_remove_edge(self):
        """Test edge removal."""
        self.workflow.add_edge("edge1", "interaction", "node1", "node2")
        assert self.workflow.has_edge("edge1")

        result = self.workflow.remove_edge("edge1")
        assert result is True
        assert not self.workflow.has_edge("edge1")

    def test_remove_nonexistent_edge(self):
        """Test removing nonexistent edge returns False."""
        result = self.workflow.remove_edge("nonexistent")
        assert result is False


class TestHyperEdgeOperations:
    """Test hyperedge addition, querying, and management."""

    def setup_method(self):
        """Set up test workflow with nodes."""
        self.workflow = create_workflow("test_workflow")
        self.workflow.add_node("node1", "protein")
        self.workflow.add_node("node2", "protein")
        self.workflow.add_node("node3", "protein")
        self.workflow.add_node("node4", "protein")

    def test_add_hyperedge_basic(self):
        """Test basic hyperedge addition."""
        result = self.workflow.add_hyperedge("hyper1", "complex", {"node1", "node2", "node3"})
        assert result is True
        assert self.workflow.has_hyperedge("hyper1")

    def test_add_hyperedge_with_properties(self):
        """Test hyperedge addition with properties."""
        result = self.workflow.add_hyperedge(
            "hyper1", "complex", {"node1", "node2", "node3"}, function="cell_cycle_control", complex_type="regulatory"
        )
        assert result is True

        hyperedge = self.workflow.get_hyperedge("hyper1")
        assert hyperedge.id == "hyper1"
        assert hyperedge.type == "complex"
        assert hyperedge.nodes == {"node1", "node2", "node3"}
        assert hyperedge.properties["function"] == "cell_cycle_control"
        assert hyperedge.properties["complex_type"] == "regulatory"

    def test_add_hyperedge_nonexistent_nodes(self):
        """Test adding hyperedge with nonexistent nodes raises ValueError."""
        with pytest.raises(ValueError, match="Node 'nonexistent' does not exist"):
            self.workflow.add_hyperedge("hyper1", "complex", {"node1", "nonexistent"})

    def test_add_duplicate_hyperedge(self):
        """Test adding duplicate hyperedge returns False."""
        self.workflow.add_hyperedge("hyper1", "complex", {"node1", "node2"})
        result = self.workflow.add_hyperedge("hyper1", "complex", {"node1", "node2"})
        assert result is False

    def test_get_hyperedge(self):
        """Test getting hyperedge by ID."""
        self.workflow.add_hyperedge("hyper1", "complex", {"node1", "node2"})
        hyperedge = self.workflow.get_hyperedge("hyper1")
        assert hyperedge is not None
        assert hyperedge.id == "hyper1"

    def test_get_nonexistent_hyperedge(self):
        """Test getting nonexistent hyperedge returns None."""
        hyperedge = self.workflow.get_hyperedge("nonexistent")
        assert hyperedge is None

    def test_get_hyperedges_by_type(self):
        """Test getting hyperedges filtered by type."""
        self.workflow.add_hyperedge("hyper1", "complex", {"node1", "node2"})
        self.workflow.add_hyperedge("hyper2", "complex", {"node2", "node3"})
        self.workflow.add_hyperedge("hyper3", "pathway", {"node1", "node2", "node3"})

        complexes = self.workflow.get_hyperedges("complex")
        assert len(complexes) == 2
        assert all(hyperedge.type == "complex" for hyperedge in complexes)


class TestGraphTraversal:
    """Test graph traversal operations."""

    def setup_method(self):
        """Set up test workflow with nodes and edges."""
        self.workflow = create_workflow("test_workflow")
        # Add nodes
        self.workflow.add_node("A", "protein")
        self.workflow.add_node("B", "protein")
        self.workflow.add_node("C", "protein")
        self.workflow.add_node("D", "disease")
        self.workflow.add_node("E", "disease")

        # Add edges
        self.workflow.add_edge("A_B", "interaction", "A", "B")
        self.workflow.add_edge("B_C", "interaction", "B", "C")
        self.workflow.add_edge("C_D", "causes", "C", "D")
        self.workflow.add_edge("A_E", "causes", "A", "E")

    def test_get_neighbors_both(self):
        """Test getting neighbors in both directions."""
        neighbors = self.workflow.get_neighbors("B")
        assert neighbors == {"A", "C"}

    def test_get_neighbors_outgoing(self):
        """Test getting outgoing neighbors."""
        neighbors = self.workflow.get_neighbors("B", direction="out")
        assert neighbors == {"C"}

    def test_get_neighbors_incoming(self):
        """Test getting incoming neighbors."""
        neighbors = self.workflow.get_neighbors("B", direction="in")
        assert neighbors == {"A"}

    def test_get_connected_edges(self):
        """Test getting connected edges."""
        edges = self.workflow.get_connected_edges("B")
        assert len(edges) == 2
        edge_types = {edge.type for edge in edges}
        assert edge_types == {"interaction"}

    def test_find_paths(self):
        """Test path finding between nodes."""
        paths = self.workflow.find_paths("A", "D")
        assert len(paths) == 1
        path = paths[0]
        assert len(path) == 3  # A -> B -> C -> D

    def test_find_paths_max_length(self):
        """Test path finding with max length constraint."""
        paths = self.workflow.find_paths("A", "D", max_length=2)
        assert len(paths) == 0  # No path of length 2 or less

        paths = self.workflow.find_paths("A", "D", max_length=4)
        assert len(paths) == 1  # Path exists with length 3

    def test_find_paths_no_path(self):
        """Test path finding when no path exists."""
        self.workflow.add_node("F", "protein")
        paths = self.workflow.find_paths("A", "F")
        assert len(paths) == 0


class TestQueryInterface:
    """Test query interface methods."""

    def setup_method(self):
        """Set up test workflow with data."""
        self.workflow = create_workflow("test_workflow")

        # Add nodes
        self.workflow.add_node("node1", "protein", name="TP53", function="tumor_suppressor")
        self.workflow.add_node("node2", "protein", name="BRAF", function="kinase")
        self.workflow.add_node("node3", "disease", name="Cancer", description="Uncontrolled growth")

        # Add edges
        self.workflow.add_edge("edge1", "interaction", "node1", "node2", confidence=0.8)
        self.workflow.add_edge("edge2", "causes", "node1", "node3", evidence="strong")

        # Add hyperedge
        self.workflow.add_hyperedge("hyper1", "complex", {"node1", "node2"}, function="control")

    def test_query_nodes_all(self):
        """Test querying all nodes."""
        nodes = self.workflow.query_nodes()
        assert len(nodes) == 3
        node_ids = {node["id"] for node in nodes}
        assert node_ids == {"node1", "node2", "node3"}

    def test_query_nodes_by_type(self):
        """Test querying nodes by type."""
        proteins = self.workflow.query_nodes("protein")
        assert len(proteins) == 2
        assert all(node["type"] == "protein" for node in proteins)

        diseases = self.workflow.query_nodes("disease")
        assert len(diseases) == 1
        assert diseases[0]["type"] == "disease"

    def test_query_edges_all(self):
        """Test querying all edges."""
        edges = self.workflow.query_edges()
        assert len(edges) == 2
        edge_ids = {edge["id"] for edge in edges}
        assert edge_ids == {"edge1", "edge2"}

    def test_query_edges_by_type(self):
        """Test querying edges by type."""
        interactions = self.workflow.query_edges("interaction")
        assert len(interactions) == 1
        assert interactions[0]["type"] == "interaction"

        causes = self.workflow.query_edges("causes")
        assert len(causes) == 1
        assert causes[0]["type"] == "causes"

    def test_query_hyperedges_all(self):
        """Test querying all hyperedges."""
        hyperedges = self.workflow.query_hyperedges()
        assert len(hyperedges) == 1
        assert hyperedges[0]["id"] == "hyper1"

    def test_query_hyperedges_by_type(self):
        """Test querying hyperedges by type."""
        complexes = self.workflow.query_hyperedges("complex")
        assert len(complexes) == 1
        assert complexes[0]["type"] == "complex"

        pathways = self.workflow.query_hyperedges("pathway")
        assert len(pathways) == 0


class TestGraphAnalysis:
    """Test graph analysis and statistics."""

    def setup_method(self):
        """Set up test workflow."""
        self.workflow = create_workflow("test_workflow")

    def test_get_statistics_empty(self):
        """Test statistics for empty workflow."""
        stats = self.workflow.get_statistics()
        assert stats["basic"]["nodes"] == 0
        assert stats["basic"]["edges"] == 0
        assert stats["basic"]["hyperedges"] == 0

    def test_get_statistics_with_data(self):
        """Test statistics for workflow with data."""
        # Add nodes
        self.workflow.add_node("node1", "protein")
        self.workflow.add_node("node2", "protein")
        self.workflow.add_node("node3", "disease")

        # Add edges
        self.workflow.add_edge("edge1", "interaction", "node1", "node2")
        self.workflow.add_edge("edge2", "causes", "node1", "node3")

        # Add hyperedge
        self.workflow.add_hyperedge("hyper1", "complex", {"node1", "node2"})

        stats = self.workflow.get_statistics()
        assert stats["basic"]["nodes"] == 3
        assert stats["basic"]["edges"] == 2
        assert stats["basic"]["hyperedges"] == 1

    def test_get_summary(self):
        """Test getting human-readable summary."""
        self.workflow.add_node("node1", "protein", name="TP53")
        self.workflow.add_node("node2", "protein", name="BRAF")
        self.workflow.add_edge("edge1", "interaction", "node1", "node2", confidence=0.8)

        summary = self.workflow.get_summary()
        assert "name" in summary
        assert "top_node_types" in summary
        assert "top_edge_types" in summary
        assert "connectivity" in summary

    def test_find_connected_components(self):
        """Test finding connected components."""
        # Create connected component
        self.workflow.add_node("A", "protein")
        self.workflow.add_node("B", "protein")
        self.workflow.add_node("C", "protein")
        self.workflow.add_edge("A_B", "interaction", "A", "B")
        self.workflow.add_edge("B_C", "interaction", "B", "C")

        # Add isolated node
        self.workflow.add_node("D", "disease")

        components = self.workflow.find_connected_components("A", max_depth=2)
        assert len(components["nodes"]) == 3
        assert len(components["edges"]) == 2
        node_ids = [node["id"] for node in components["nodes"]]
        assert "A" in node_ids
        assert "B" in node_ids
        assert "C" in node_ids
        assert "D" not in node_ids


class TestSchemaSupport:
    """Test schema validation and support."""

    def setup_method(self):
        """Set up test workflow with schema."""
        self.schema = {
            "protein": {
                "represented_as": "node",
                "properties": {"name": "str", "function": "str", "uniprot_id": "str"},
            },
            "interaction": {
                "represented_as": "edge",
                "source": "protein",
                "target": "protein",
                "properties": {"confidence": "float", "evidence": "str"},
            },
        }
        self.workflow = create_workflow("test_workflow", schema=self.schema)

    def test_get_schema(self):
        """Test getting schema."""
        schema = self.workflow.get_schema()
        assert schema == self.schema

    def test_validate_against_schema_valid(self):
        """Test schema validation with valid data."""
        # Valid protein properties
        result = self.workflow.validate_against_schema(
            "protein", {"name": "TP53", "function": "tumor_suppressor", "uniprot_id": "P04637"}
        )
        assert result is True

    def test_validate_against_schema_invalid(self):
        """Test schema validation with invalid data."""
        # Invalid property type
        result = self.workflow.validate_against_schema(
            "protein",
            {
                "name": 123,  # Should be string
                "function": "tumor_suppressor",
            },
        )
        assert result is False

    def test_validate_against_schema_missing_property(self):
        """Test schema validation with missing required property."""
        # Missing required property
        result = self.workflow.validate_against_schema(
            "protein",
            {
                "name": "TP53"
                # Missing function
            },
        )
        assert result is False

    def test_export_schema(self):
        """Test schema export."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            schema_file = f.name

        try:
            self.workflow.export_schema(schema_file)
            assert os.path.exists(schema_file)

            # Verify file content
            with open(schema_file, "r") as f:
                content = f.read()
                assert "protein" in content
                assert "interaction" in content
        finally:
            if os.path.exists(schema_file):
                os.unlink(schema_file)


class TestSerialization:
    """Test workflow serialization and deserialization."""

    def setup_method(self):
        """Set up test workflow."""
        self.workflow = create_workflow("test_workflow")

    def test_to_json(self):
        """Test workflow to JSON conversion."""
        # Add data
        self.workflow.add_node("node1", "protein", name="TP53")
        self.workflow.add_node("node2", "protein", name="BRAF")
        self.workflow.add_edge("edge1", "interaction", "node1", "node2", confidence=0.8)
        self.workflow.add_hyperedge("hyper1", "complex", {"node1", "node2"}, function="control")

        json_str = self.workflow.to_json()

        # Verify it's valid JSON
        data = json.loads(json_str)
        assert data["name"] == "test_workflow"
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1
        assert len(data["hyperedges"]) == 1

    def test_from_json(self):
        """Test workflow creation from JSON."""
        # Create JSON data
        json_data = {
            "name": "test_workflow",
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

        json_str = json.dumps(json_data, indent=2)
        self.workflow.from_json(json_str)

        # Verify data was loaded
        assert self.workflow.has_node("node1")
        assert self.workflow.has_edge("edge1")
        assert self.workflow.has_hyperedge("hyper1")

    def test_save_and_load(self):
        """Test saving and loading workflow to/from file."""
        # Add data
        self.workflow.add_node("node1", "protein", name="TP53")
        self.workflow.add_node("node2", "protein", name="BRAF")
        self.workflow.add_edge("edge1", "interaction", "node1", "node2", confidence=0.8)

        # Save to file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            save_file = f.name

        try:
            self.workflow.save(save_file)
            assert os.path.exists(save_file)

            # Create new workflow and load
            new_workflow = create_workflow("new_workflow")
            new_workflow.load(save_file)

            # Verify data was loaded
            assert new_workflow.has_node("node1")
            assert new_workflow.has_edge("edge1")

        finally:
            if os.path.exists(save_file):
                os.unlink(save_file)


class TestUtilityOperations:
    """Test utility operations."""

    def setup_method(self):
        """Set up test workflow."""
        self.workflow = create_workflow("test_workflow")

    def test_len(self):
        """Test workflow length (number of nodes)."""
        assert len(self.workflow) == 0
        self.workflow.add_node("node1", "protein")
        assert len(self.workflow) == 1

    def test_contains(self):
        """Test node containment."""
        self.workflow.add_node("node1", "protein")
        assert "node1" in self.workflow
        assert "nonexistent" not in self.workflow

    def test_clear(self):
        """Test clearing the workflow."""
        self.workflow.add_node("node1", "protein")
        self.workflow.add_node("node2", "protein")
        self.workflow.add_edge("edge1", "interaction", "node1", "node2")

        self.workflow.clear()
        assert len(self.workflow) == 0
        assert not self.workflow.has_edge("edge1")

    def test_copy(self):
        """Test copying the workflow."""
        self.workflow.add_node("node1", "protein", name="TP53")
        self.workflow.add_node("node2", "protein", name="BRAF")
        self.workflow.add_edge("edge1", "interaction", "node1", "node2", confidence=0.8)

        copy_workflow = self.workflow.copy()
        assert copy_workflow.name == self.workflow.name
        assert len(copy_workflow) == len(self.workflow)
        assert copy_workflow.has_node("node1")
        assert copy_workflow.has_edge("edge1")

        # Verify it's a deep copy
        copy_workflow.add_node("node3", "protein")
        assert len(copy_workflow) != len(self.workflow)

    def test_get_graph(self):
        """Test getting underlying graph."""
        self.workflow.add_node("node1", "protein")
        graph = self.workflow.get_graph()

        assert isinstance(graph, type(self.workflow.graph))
        assert len(graph) == 1
        assert graph.has_node("node1")


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test workflow."""
        self.workflow = create_workflow("test_workflow")

    def test_large_workflow_performance(self):
        """Test performance with larger workflow."""
        # Add many nodes
        for i in range(1000):
            self.workflow.add_node(f"node{i}", "protein")

        # Add many edges
        for i in range(999):
            self.workflow.add_edge(f"edge{i}", "interaction", f"node{i}", f"node{i+1}")

        # Test operations still work
        assert len(self.workflow) == 1000
        assert self.workflow.has_node("node500")
        assert self.workflow.has_edge("edge500")

        # Test statistics
        stats = self.workflow.get_statistics()
        assert stats["basic"]["nodes"] == 1000
        assert stats["basic"]["edges"] == 999

    def test_schema_validation_without_schema(self):
        """Test schema validation when no schema is set."""
        workflow = create_workflow("test_workflow")  # No schema

        # Should return True when no schema (no validation)
        result = workflow.validate_against_schema("protein", {"name": "TP53"})
        assert result is True

    def test_get_schema_without_schema(self):
        """Test getting schema when no schema is set."""
        workflow = create_workflow("test_workflow")  # No schema

        schema = workflow.get_schema()
        assert schema is None


class TestIntegration:
    """Test integration with other components."""

    def test_with_graph_class(self):
        """Test integration with Graph class."""
        workflow = create_workflow("test_workflow")

        # Add data through workflow
        workflow.add_node("protein1", "protein", name="TP53")
        workflow.add_node("protein2", "protein", name="BRAF")
        workflow.add_edge("interaction1", "interaction", "protein1", "protein2", confidence=0.8)

        # Get underlying graph
        graph = workflow.get_graph()

        # Test graph operations
        assert len(graph) == 2
        assert graph.has_node("protein1")
        assert graph.has_edge("interaction1")

        # Test statistics
        stats = graph.get_statistics()
        assert stats["basic"]["nodes"] == 2
        assert stats["basic"]["edges"] == 1

    def test_with_schema_validation(self):
        """Test integration with schema validation."""
        schema = {"protein": {"represented_as": "node", "properties": {"name": "str", "function": "str"}}}

        workflow = create_workflow("test_workflow", schema=schema)

        # Valid node
        result = workflow.add_node("protein1", "protein", name="TP53", function="tumor_suppressor")
        assert result is True

        # Invalid node (missing required property)
        # Note: Current implementation doesn't validate during add_node
        # This test documents the current behavior
        result = workflow.add_node("protein2", "protein", name="BRAF")
        assert result is True  # Currently no validation during addition


class TestValidationModes:
    """Test validation modes and deduplication functionality."""

    def setup_method(self):
        """Set up test schema."""
        self.schema = {
            "protein": {
                "represented_as": "node",
                "properties": {"name": "str", "function": "str"},
            },
            "interaction": {
                "represented_as": "edge",
                "source": "protein",
                "target": "protein",
                "properties": {"confidence": "float"},
            },
        }

    def test_validation_mode_none(self):
        """Test validation mode 'none' - no validation or deduplication."""
        workflow = create_workflow("test", validation_mode="none", deduplication=False)

        # First addition should succeed
        result1 = workflow.add_node("node1", "protein", name="TP53")
        assert result1 is True

        # Second addition should fail due to Graph's built-in deduplication
        # (Graph class always prevents duplicates, regardless of workflow settings)
        result2 = workflow.add_node("node1", "protein", name="TP53")  # Duplicate
        assert result2 is False  # Graph prevents duplicates

        # Should allow any node/edge types (no schema validation)
        result3 = workflow.add_node("node2", "unknown_type", invalid_prop=123)
        assert result3 is True

    def test_validation_mode_warn(self):
        """Test validation mode 'warn' - warnings but no failures."""
        workflow = create_workflow("test", validation_mode="warn", deduplication=True, schema=self.schema)

        # Test duplicate detection with warning
        result1 = workflow.add_node("node1", "protein", name="TP53", function="tumor_suppressor")
        assert result1 is True

        # Second duplicate should warn but return False
        result2 = workflow.add_node("node1", "protein", name="TP53", function="tumor_suppressor")
        assert result2 is False  # Deduplication prevents addition

        # Test schema validation with warning
        result3 = workflow.add_node("node2", "protein", name=123)  # Invalid type
        assert result3 is True  # Warning but continues

    def test_validation_mode_strict(self):
        """Test validation mode 'strict' - fail fast on violations."""
        workflow = create_workflow("test", validation_mode="strict", deduplication=True, schema=self.schema)

        # Test duplicate detection with strict mode
        result1 = workflow.add_node("node1", "protein", name="TP53", function="tumor_suppressor")
        assert result1 is True

        # Second duplicate should raise ValueError
        with pytest.raises(ValueError, match="Duplicate node ID 'node1' not allowed in strict mode"):
            workflow.add_node("node1", "protein", name="TP53", function="tumor_suppressor")

        # Test schema validation with strict mode
        with pytest.raises(ValueError, match="Node 'node2' of type 'protein' failed schema validation"):
            workflow.add_node("node2", "protein", name=123)  # Invalid type

    def test_deduplication_nodes(self):
        """Test node deduplication functionality."""
        workflow = create_workflow("test", deduplication=True)

        # First addition should succeed
        result1 = workflow.add_node("node1", "protein", name="TP53")
        assert result1 is True
        assert len(workflow) == 1

        # Duplicate addition should fail
        result2 = workflow.add_node("node1", "protein", name="TP53")
        assert result2 is False
        assert len(workflow) == 1  # Still only one node

        # Different node should succeed
        result3 = workflow.add_node("node2", "protein", name="BRAF")
        assert result3 is True
        assert len(workflow) == 2

    def test_deduplication_edges(self):
        """Test edge deduplication functionality."""
        workflow = create_workflow("test", deduplication=True)
        workflow.add_node("node1", "protein")
        workflow.add_node("node2", "protein")

        # First addition should succeed
        result1 = workflow.add_edge("edge1", "interaction", "node1", "node2")
        assert result1 is True

        # Duplicate addition should fail
        result2 = workflow.add_edge("edge1", "interaction", "node1", "node2")
        assert result2 is False

        # Different edge should succeed
        result3 = workflow.add_edge("edge2", "interaction", "node1", "node2")
        assert result3 is True

    def test_schema_validation_valid_data(self):
        """Test schema validation with valid data."""
        workflow = create_workflow("test", validation_mode="strict", schema=self.schema)

        # Valid protein node
        result = workflow.add_node("node1", "protein", name="TP53", function="tumor_suppressor")
        assert result is True

        # Valid interaction edge
        workflow.add_node("node2", "protein", name="BRAF", function="kinase")
        result = workflow.add_edge("edge1", "interaction", "node1", "node2", confidence=0.8)
        assert result is True

    def test_schema_validation_invalid_property_type(self):
        """Test schema validation with invalid property types."""
        workflow = create_workflow("test", validation_mode="strict", schema=self.schema)

        # Invalid property type (name should be string, not int)
        with pytest.raises(ValueError, match="Node 'node1' of type 'protein' failed schema validation"):
            workflow.add_node("node1", "protein", name=123, function="tumor_suppressor")

    def test_schema_validation_missing_required_property(self):
        """Test schema validation with missing required properties."""
        workflow = create_workflow("test", validation_mode="strict", schema=self.schema)

        # Missing required property (function)
        with pytest.raises(ValueError, match="Node 'node1' of type 'protein' failed schema validation"):
            workflow.add_node("node1", "protein", name="TP53")

    def test_schema_validation_unknown_type(self):
        """Test schema validation with unknown node/edge types."""
        workflow = create_workflow("test", validation_mode="strict", schema=self.schema)

        # Unknown node type should pass (no schema entry)
        result = workflow.add_node("node1", "unknown_type", any_prop="value")
        assert result is True

    def test_validation_mode_parameter_combinations(self):
        """Test different combinations of validation_mode and deduplication parameters."""
        # Test all combinations
        combinations = [
            ("none", False),
            ("none", True),
            ("warn", False),
            ("warn", True),
            ("strict", False),
            ("strict", True),
        ]

        for validation_mode, deduplication in combinations:
            workflow = create_workflow(
                f"test_{validation_mode}_{deduplication}",
                validation_mode=validation_mode,
                deduplication=deduplication,
                schema=self.schema,
            )

            # Basic functionality should work
            result = workflow.add_node("node1", "protein", name="TP53", function="tumor_suppressor")
            assert result is True

    def test_validation_mode_edge_cases(self):
        """Test edge cases in validation modes."""
        workflow = create_workflow("test", validation_mode="warn", deduplication=True)

        # Test with empty properties
        result = workflow.add_node("node1", "protein")
        assert result is True

        # Test with None values
        result = workflow.add_node("node2", "protein", name=None, function="tumor_suppressor")
        assert result is True

    def test_validation_with_schema_file(self):
        """Test validation with schema loaded from file."""
        import tempfile
        import yaml

        # Create temporary schema file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(self.schema, f)
            schema_file = f.name

        try:
            workflow = create_workflow("test", validation_mode="strict", deduplication=True, schema_file=schema_file)

            # Should work with valid data
            result = workflow.add_node("node1", "protein", name="TP53", function="tumor_suppressor")
            assert result is True

            # Should fail with invalid data
            with pytest.raises(ValueError):
                workflow.add_node("node2", "protein", name=123)

        finally:
            import os

            os.unlink(schema_file)

    def test_validation_mode_inheritance(self):
        """Test that validation mode is properly inherited by workflow instances."""
        workflow = create_workflow("test", validation_mode="strict", deduplication=True)

        assert workflow.validation_mode == "strict"
        assert workflow.deduplication is True

        # Test that the mode affects behavior
        workflow.add_node("node1", "protein")
        with pytest.raises(ValueError):
            workflow.add_node("node1", "protein")  # Should fail in strict mode

    def test_validation_mode_change_after_creation(self):
        """Test that validation mode can be changed after workflow creation."""
        workflow = create_workflow("test", validation_mode="none", deduplication=False)

        # Change to strict mode
        workflow.validation_mode = "strict"
        workflow.deduplication = True

        # Should now enforce validation
        workflow.add_node("node1", "protein")
        with pytest.raises(ValueError):
            workflow.add_node("node1", "protein")  # Should fail due to deduplication
