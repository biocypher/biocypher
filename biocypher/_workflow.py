"""Unified BioCypher Workflow API for knowledge graph workflows.

This module provides a streamlined interface for creating and managing
knowledge graphs using the unified Graph representation, with optional
schema and ontology support. Designed for both agentic and deterministic
workflows.

## Design Philosophy

This API is designed with the following principles:
1. **Agentic-First**: Optimized for LLM agent workflows with computable functions
2. **Zero Dependencies**: Pure Python implementation for maximum compatibility
3. **Future-Proof**: Native BioCypher objects enable advanced agentic features
4. **Migration-Ready**: Wrapper methods provide compatibility with existing tools
5. **Progressive Validation**: Optional validation and deduplication with flexible modes

## Validation and Deduplication

Unlike the legacy BioCypher which enforces strict validation and deduplication,
this API provides **progressive validation** with three modes:

- **"none"** (default): No validation or deduplication - maximum flexibility for agents
- **"warn"**: Log warnings for schema violations and duplicates but continue processing
- **"strict"**: Enforce schema validation and deduplication - fail fast on violations

This approach allows:
- **Agents** to work with maximum flexibility (no validation overhead)
- **Deterministic workflows** to use validation when needed
- **Gradual migration** from legacy BioCypher (start with "none", add validation later)

## Future Migration Path

This module represents the future direction of BioCypher's in-memory graph
functionality. The plan is to:

1. **Phase 1** (Current): Keep separate from legacy code, provide compatibility wrappers
2. **Phase 2**: Replace legacy in-memory implementations (PandasKG, NetworkxKG)
3. **Phase 3**: Add advanced agentic features (computable functions, decision logging)
4. **Phase 4**: Integrate with main BioCypher class as unified interface

## Agentic Features (Future)

- Computable functions attached to nodes/edges
- Decision logging and reasoning traces
- Counterfactual inference capabilities
- MCP (Model Context Protocol) interface integration
- Local graph computation for agent workflows

"""

import json

from typing import Any

import yaml

from ._graph import Edge, Graph, HyperEdge, Node
from ._logger import logger


class BioCypherWorkflow:
    """Unified BioCypher interface for knowledge graph workflows.

    This class provides a clean, simple API for creating and managing
    knowledge graphs with optional schema and ontology support. Designed
    for both agentic and deterministic workflows.
    """

    def __init__(
        self,
        name: str = "workflow_graph",
        directed: bool = True,
        schema: dict[str, Any] | None = None,
        schema_file: str | None = None,
        head_ontology_url: str | None = None,
        validation_mode: str = "none",
        deduplication: bool = False,
    ):
        """Initialize the workflow with a unified graph.

        Args:
            name: Name of the knowledge graph
            directed: Whether the graph is directed (default: True)
            schema: Dictionary defining the knowledge graph schema
            schema_file: Path to YAML schema file
            head_ontology_url: URL to ontology file (defaults to Biolink model)
            validation_mode: Validation level ("none", "warn", "strict")
            deduplication: Whether to enable deduplication (default: False)
        """
        self.graph = Graph(name=name, directed=directed)
        self.name = name
        self.schema = schema
        self.schema_file = schema_file
        self.head_ontology_url = head_ontology_url
        self.validation_mode = validation_mode
        self.deduplication = deduplication

        # Track seen entities for deduplication
        self._seen_nodes = set()
        self._seen_edges = set()

        # Initialize schema if provided
        if schema_file:
            self._load_schema_from_file(schema_file)
        elif schema:
            self._load_schema_from_dict(schema)

    def _load_schema_from_file(self, schema_file: str) -> None:
        """Load schema from YAML file."""
        try:
            with open(schema_file, "r") as f:
                self.schema = yaml.safe_load(f)
            logger.info(f"Loaded schema from {schema_file}")
        except Exception as e:
            logger.warning(f"Could not load schema from {schema_file}: {e}")

    def _load_schema_from_dict(self, schema: dict[str, Any]) -> None:
        """Load schema from dictionary."""
        self.schema = schema
        logger.info("Loaded schema from dictionary")

    # ==================== NODE OPERATIONS ====================

    def add_node(self, node_id: str, node_type: str, **properties) -> bool:
        """Add a node to the knowledge graph.

        Args:
            node_id: Unique identifier for the node
            node_type: Type/category of the node
            **properties: Node properties as keyword arguments

        Returns:
            bool: True if node was added, False if it already exists

        Example:
            workflow.add_node("protein_1", "protein", name="TP53", function="tumor_suppressor")
        """
        # Check for duplicates if deduplication is enabled
        if self.deduplication:
            if node_id in self._seen_nodes:
                if self.validation_mode == "warn":
                    logger.warning(f"Duplicate node ID '{node_id}' detected")
                elif self.validation_mode == "strict":
                    raise ValueError(f"Duplicate node ID '{node_id}' not allowed in strict mode")
                return False
            self._seen_nodes.add(node_id)

        # Validate against schema if validation is enabled
        if self.validation_mode in ["warn", "strict"]:
            is_valid = self.validate_against_schema(node_type, properties)
            if not is_valid:
                if self.validation_mode == "strict":
                    raise ValueError(f"Node '{node_id}' of type '{node_type}' failed schema validation")
                elif self.validation_mode == "warn":
                    logger.warning(f"Node '{node_id}' of type '{node_type}' failed schema validation")

        # Try to add node to graph (Graph class handles its own deduplication)
        result = self.graph.add_node(node_id, node_type, properties)

        # If deduplication is enabled and we're tracking, update our tracking
        if self.deduplication and result:
            self._seen_nodes.add(node_id)

        return result

    def get_node(self, node_id: str) -> Node | None:
        """Get a node by ID.

        Args:
            node_id: Node identifier

        Returns:
            Node object or None if not found
        """
        return self.graph.get_node(node_id)

    def get_nodes(self, node_type: str | None = None) -> list[Node]:
        """Get all nodes, optionally filtered by type.

        Args:
            node_type: Optional filter by node type

        Returns:
            List of Node objects
        """
        return self.graph.get_nodes(node_type)

    def has_node(self, node_id: str) -> bool:
        """Check if a node exists.

        Args:
            node_id: Node identifier

        Returns:
            bool: True if node exists
        """
        return self.graph.has_node(node_id)

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its connected edges.

        Args:
            node_id: Node identifier

        Returns:
            bool: True if node was removed, False if not found
        """
        return self.graph.remove_node(node_id)

    # ==================== EDGE OPERATIONS ====================

    def add_edge(self, edge_id: str, edge_type: str, source: str, target: str, **properties) -> bool:
        """Add an edge to the knowledge graph.

        Args:
            edge_id: Unique identifier for the edge
            edge_type: Type/category of the edge
            source: Source node ID
            target: Target node ID
            **properties: Edge properties as keyword arguments

        Returns:
            bool: True if edge was added, False if it already exists

        Example:
            workflow.add_edge("interaction_1", "interaction", "protein_1", "protein_2",
                          confidence=0.8, method="yeast_two_hybrid")
        """
        # Check for duplicates if deduplication is enabled
        if self.deduplication:
            edge_key = (edge_id, edge_type)
            if edge_key in self._seen_edges:
                if self.validation_mode == "warn":
                    logger.warning(f"Duplicate edge ID '{edge_id}' of type '{edge_type}' detected")
                elif self.validation_mode == "strict":
                    raise ValueError(f"Duplicate edge ID '{edge_id}' not allowed in strict mode")
                return False
            self._seen_edges.add(edge_key)

        # Validate against schema if validation is enabled
        if self.validation_mode in ["warn", "strict"]:
            is_valid = self.validate_against_schema(edge_type, properties)
            if not is_valid:
                if self.validation_mode == "strict":
                    raise ValueError(f"Edge '{edge_id}' of type '{edge_type}' failed schema validation")
                elif self.validation_mode == "warn":
                    logger.warning(f"Edge '{edge_id}' of type '{edge_type}' failed schema validation")

        # Try to add edge to graph (Graph class handles its own deduplication)
        result = self.graph.add_edge(edge_id, edge_type, source, target, properties)

        # If deduplication is enabled and we're tracking, update our tracking
        if self.deduplication and result:
            edge_key = (edge_id, edge_type)
            self._seen_edges.add(edge_key)

        return result

    def get_edge(self, edge_id: str) -> Edge | None:
        """Get an edge by ID.

        Args:
            edge_id: Edge identifier

        Returns:
            Edge object or None if not found
        """
        return self.graph.get_edge(edge_id)

    def get_edges(self, edge_type: str | None = None) -> list[Edge]:
        """Get all edges, optionally filtered by type.

        Args:
            edge_type: Optional filter by edge type

        Returns:
            List of Edge objects
        """
        return self.graph.get_edges(edge_type)

    def get_edges_between(self, source: str, target: str, edge_type: str | None = None) -> list[Edge]:
        """Get edges between two nodes.

        Args:
            source: Source node ID
            target: Target node ID
            edge_type: Optional filter by edge type

        Returns:
            List of Edge objects
        """
        return self.graph.get_edges_between(source, target, edge_type)

    def has_edge(self, edge_id: str) -> bool:
        """Check if an edge exists.

        Args:
            edge_id: Edge identifier

        Returns:
            bool: True if edge exists
        """
        return self.graph.has_edge(edge_id)

    def remove_edge(self, edge_id: str) -> bool:
        """Remove an edge from the graph.

        Args:
            edge_id: Edge identifier

        Returns:
            bool: True if edge was removed, False if not found
        """
        return self.graph.remove_edge(edge_id)

    # ==================== HYPEREDGE OPERATIONS ====================

    def add_hyperedge(self, hyperedge_id: str, hyperedge_type: str, nodes: set[str], **properties) -> bool:
        """Add a hyperedge connecting multiple nodes.

        Args:
            hyperedge_id: Unique identifier for the hyperedge
            hyperedge_type: Type/category of the hyperedge
            nodes: Set of node IDs to connect
            **properties: Hyperedge properties as keyword arguments

        Returns:
            bool: True if hyperedge was added, False if it already exists

        Example:
            workflow.add_hyperedge("complex_1", "protein_complex", {"protein_1", "protein_2", "protein_3"},
                               name="transcription_factor_complex")
        """
        return self.graph.add_hyperedge(hyperedge_id, hyperedge_type, nodes, properties)

    def get_hyperedge(self, hyperedge_id: str) -> HyperEdge | None:
        """Get a hyperedge by ID.

        Args:
            hyperedge_id: Hyperedge identifier

        Returns:
            HyperEdge object or None if not found
        """
        return self.graph.get_hyperedge(hyperedge_id)

    def get_hyperedges(self, hyperedge_type: str | None = None) -> list[HyperEdge]:
        """Get all hyperedges, optionally filtered by type.

        Args:
            hyperedge_type: Optional filter by hyperedge type

        Returns:
            List of HyperEdge objects
        """
        return self.graph.get_hyperedges(hyperedge_type)

    def has_hyperedge(self, hyperedge_id: str) -> bool:
        """Check if a hyperedge exists.

        Args:
            hyperedge_id: Hyperedge identifier

        Returns:
            bool: True if hyperedge exists
        """
        return self.graph.has_hyperedge(hyperedge_id)

    # ==================== GRAPH TRAVERSAL ====================

    def get_neighbors(self, node_id: str, direction: str = "both") -> set[str]:
        """Get neighboring nodes.

        Args:
            node_id: Node identifier
            direction: "in", "out", or "both"

        Returns:
            Set of neighboring node IDs
        """
        return self.graph.get_neighbors(node_id, direction)

    def get_connected_edges(self, node_id: str, direction: str = "both") -> list[Edge]:
        """Get edges connected to a node.

        Args:
            node_id: Node identifier
            direction: "in", "out", or "both"

        Returns:
            List of connected Edge objects
        """
        return self.graph.get_connected_edges(node_id, direction)

    def find_paths(self, source: str, target: str, max_length: int = 3) -> list[list[Edge]]:
        """Find all paths between two nodes.

        Args:
            source: Source node ID
            target: Target node ID
            max_length: Maximum path length

        Returns:
            List of paths, each path is a list of Edge objects
        """
        return self.graph.find_paths(source, target, max_length)

    # ==================== QUERY INTERFACE ====================

    def query_nodes(self, node_type: str | None = None) -> list[dict[str, Any]]:
        """Query nodes in the knowledge graph.

        Args:
            node_type: Optional filter by node type

        Returns:
            List of node dictionaries
        """
        nodes = self.graph.get_nodes(node_type)
        return [node.to_dict() for node in nodes]

    def query_edges(self, edge_type: str | None = None) -> list[dict[str, Any]]:
        """Query edges in the knowledge graph.

        Args:
            edge_type: Optional filter by edge type

        Returns:
            List of edge dictionaries
        """
        edges = self.graph.get_edges(edge_type)
        return [edge.to_dict() for edge in edges]

    def query_hyperedges(self, hyperedge_type: str | None = None) -> list[dict[str, Any]]:
        """Query hyperedges in the knowledge graph.

        Args:
            hyperedge_type: Optional filter by hyperedge type

        Returns:
            List of hyperedge dictionaries
        """
        hyperedges = self.graph.get_hyperedges(hyperedge_type)
        return [hyperedge.to_dict() for hyperedge in hyperedges]

    def find_connected_components(self, node_id: str, max_depth: int = 2) -> dict[str, Any]:
        """Find connected components around a node.

        Args:
            node_id: Starting node ID
            max_depth: Maximum depth to explore

        Returns:
            Dictionary with nodes and edges in the component
        """
        if not self.graph.has_node(node_id):
            return {"nodes": [], "edges": [], "hyperedges": []}

        # Collect nodes within max_depth
        component_nodes = {node_id}
        current_level = {node_id}

        for depth in range(max_depth):
            next_level = set()
            for node in current_level:
                neighbors = self.graph.get_neighbors(node)
                next_level.update(neighbors)
            current_level = next_level - component_nodes
            component_nodes.update(current_level)

            if not current_level:
                break

        # Get subgraph
        subgraph = self.graph.get_subgraph(component_nodes)

        return {
            "nodes": [node.to_dict() for node in subgraph.get_nodes()],
            "edges": [edge.to_dict() for edge in subgraph.get_edges()],
            "hyperedges": [hyperedge.to_dict() for hyperedge in subgraph.get_hyperedges()],
            "statistics": subgraph.get_statistics(),
        }

    # ==================== GRAPH ANALYSIS ====================

    def get_statistics(self) -> dict[str, Any]:
        """Get comprehensive graph statistics.

        Returns:
            Dictionary with graph statistics
        """
        return self.graph.get_statistics()

    def get_summary(self) -> dict[str, Any]:
        """Get a human-readable summary of the graph.

        Returns:
            Dictionary with graph summary
        """
        stats = self.graph.get_statistics()

        # Get top node types
        node_types = stats["node_types"]
        top_node_types = sorted(node_types.items(), key=lambda x: x[1], reverse=True)[:5]

        # Get top edge types
        edge_types = stats["edge_types"]
        top_edge_types = sorted(edge_types.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "name": self.name,
            "total_nodes": stats["basic"]["nodes"],
            "total_edges": stats["basic"]["edges"],
            "total_hyperedges": stats["basic"]["hyperedges"],
            "top_node_types": top_node_types,
            "top_edge_types": top_edge_types,
            "connectivity": stats["connectivity"],
        }

    # ==================== SCHEMA AND ONTOLOGY SUPPORT ====================

    def get_schema(self) -> dict[str, Any] | None:
        """Get the current schema configuration.

        Returns:
            Dictionary representing the schema or None if no schema
        """
        return self.schema

    def export_schema(self, filepath: str) -> None:
        """Export the current schema to a YAML file.

        Args:
            filepath: Path to save the schema file
        """
        if self.schema:
            with open(filepath, "w") as f:
                yaml.dump(self.schema, f, default_flow_style=False)
            logger.info(f"Schema exported to {filepath}")
        else:
            logger.warning("No schema to export")

    def validate_against_schema(self, node_type: str, properties: dict[str, Any]) -> bool:
        """Validate node properties against schema (if available).

        Args:
            node_type: Type of node to validate
            properties: Properties to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not self.schema or node_type not in self.schema:
            return True  # No schema or type not in schema, assume valid

        schema_entry = self.schema[node_type]
        if "properties" not in schema_entry:
            return True  # No property constraints

        required_properties = schema_entry["properties"]

        # Check if all required properties are present and have correct types
        for prop_name, prop_type in required_properties.items():
            if prop_name not in properties:
                logger.warning(f"Missing required property '{prop_name}' for node type '{node_type}'")
                return False

            # Check property type
            actual_value = properties[prop_name]
            if not self._validate_property_type(actual_value, prop_type):
                logger.warning(
                    f"Property '{prop_name}' has wrong type. Expected {prop_type}, got {type(actual_value).__name__}"
                )
                return False

        return True

    def _validate_property_type(self, value: Any, expected_type: str) -> bool:
        """Validate that a property value matches the expected type.

        Args:
            value: The actual value
            expected_type: The expected type as string (e.g., 'str', 'int', 'float')

        Returns:
            bool: True if type matches, False otherwise
        """
        type_mapping = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
        }

        if expected_type not in type_mapping:
            return True  # Unknown type, assume valid

        expected_python_type = type_mapping[expected_type]
        return isinstance(value, expected_python_type)

    # ==================== SERIALIZATION ====================

    def to_json(self) -> str:
        """Export the knowledge graph to JSON format.

        Returns:
            JSON string representation of the graph
        """
        return self.graph.to_json()

    def from_json(self, json_data: str) -> None:
        """Import knowledge graph from JSON format.

        Args:
            json_data: JSON string containing graph data
        """
        data = json.loads(json_data)
        self.graph = Graph.from_dict(data)
        self.name = self.graph.name

    def save(self, filepath: str) -> None:
        """Save the graph to a file.

        Args:
            filepath: Path to save the graph
        """
        with open(filepath, "w") as f:
            f.write(self.to_json())
        logger.info(f"Graph saved to {filepath}")

    def load(self, filepath: str) -> None:
        """Load the graph from a file.

        Args:
            filepath: Path to load the graph from
        """
        with open(filepath, "r") as f:
            json_data = f.read()
        self.from_json(json_data)
        logger.info(f"Graph loaded from {filepath}")

    # ==================== UTILITY METHODS ====================

    def clear(self) -> None:
        """Clear all nodes and edges from the graph."""
        self.graph = Graph(name=self.name, directed=self.graph.directed)
        logger.info("Graph cleared")

    def copy(self) -> "BioCypherWorkflow":
        """Create a copy of the workflow and its graph.

        Returns:
            New BioCypherWorkflow instance
        """
        new_workflow = BioCypherWorkflow(
            name=self.name, directed=self.graph.directed, schema=self.schema, head_ontology_url=self.head_ontology_url
        )
        new_workflow.from_json(self.to_json())
        return new_workflow

    def get_graph(self) -> Graph:
        """Get the underlying Graph object.

        Returns:
            Graph object
        """
        return self.graph

    def __len__(self) -> int:
        """Return the number of nodes in the graph."""
        return len(self.graph)

    def __contains__(self, node_id: str) -> bool:
        """Check if a node exists in the graph."""
        return node_id in self.graph

    def __str__(self) -> str:
        """String representation of the workflow."""
        stats = self.get_statistics()
        return (
            f"BioCypherWorkflow(name='{self.name}', "
            f"nodes={stats['basic']['nodes']}, edges={stats['basic']['edges']}, "
            f"hyperedges={stats['basic']['hyperedges']})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    # ==================== COMPATIBILITY WRAPPER METHODS ====================

    def to_networkx(self):
        """Convert to NetworkX graph for compatibility with existing tools.

        Returns:
            networkx.DiGraph: NetworkX representation of the graph

        Note:
            This method provides compatibility with existing NetworkX-based
            tools while maintaining the native BioCypher object structure.
            Future versions may use this as the primary backend.
        """
        try:
            import networkx as nx
        except ImportError:
            raise ImportError("NetworkX is required for to_networkx() conversion. Install with: pip install networkx")

        g = nx.DiGraph() if self.graph.directed else nx.Graph()

        # Add nodes with properties
        for node in self.graph._nodes.values():
            attrs = node.properties.copy()
            attrs["node_type"] = node.type
            g.add_node(node.id, **attrs)

        # Add edges with properties
        for edge in self.graph._edges.values():
            attrs = edge.properties.copy()
            attrs["edge_type"] = edge.type
            g.add_edge(edge.source, edge.target, **attrs)

        return g

    def to_pandas(self):
        """Convert to Pandas DataFrames for compatibility with existing tools.

        Returns:
            dict[str, pd.DataFrame]: Dictionary of DataFrames, one per node/edge type

        Note:
            This method provides compatibility with existing Pandas-based
            tools while maintaining the native BioCypher object structure.
            Future versions may use this as the primary backend.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Pandas is required for to_pandas() conversion. Install with: pip install pandas")

        dfs = {}

        # Create node DataFrames by type
        for node_type, node_ids in self.graph._node_types.items():
            nodes = [self.graph._nodes[node_id] for node_id in node_ids]
            data = []
            for node in nodes:
                row = {"node_id": node.id, "node_type": node.type}
                row.update(node.properties)
                data.append(row)
            dfs[node_type] = pd.DataFrame(data)

        # Create edge DataFrames by type
        for edge_type, edge_ids in self.graph._edge_types.items():
            edges = [self.graph._edges[edge_id] for edge_id in edge_ids]
            data = []
            for edge in edges:
                row = {"edge_id": edge.id, "edge_type": edge.type, "source_id": edge.source, "target_id": edge.target}
                row.update(edge.properties)
                data.append(row)
            dfs[edge_type] = pd.DataFrame(data)

        return dfs


# Convenience function for quick workflow creation
def create_workflow(
    name: str = "knowledge_graph",
    directed: bool = True,
    schema: dict[str, Any] | None = None,
    schema_file: str | None = None,
    head_ontology_url: str | None = None,
    validation_mode: str = "none",
    deduplication: bool = False,
) -> BioCypherWorkflow:
    """Create a new knowledge graph workflow.

    Args:
        name: Name of the knowledge graph
        directed: Whether the graph is directed
        schema: Dictionary defining the knowledge graph schema
        schema_file: Path to YAML schema file
        head_ontology_url: URL to ontology file
        validation_mode: Validation level ("none", "warn", "strict")
        deduplication: Whether to enable deduplication

    Returns:
        BioCypherWorkflow instance
    """
    return BioCypherWorkflow(
        name=name,
        directed=directed,
        schema=schema,
        schema_file=schema_file,
        head_ontology_url=head_ontology_url,
        validation_mode=validation_mode,
        deduplication=deduplication,
    )
