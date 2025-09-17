"""Unified Graph representation for BioCypher.

This module provides a comprehensive Graph class that can represent various
graph types including simple graphs, directed graphs, weighted graphs,
multigraphs, and hypergraphs. The design focuses on simplicity and
extensibility for knowledge representation.

TODO: examine overlap with legacy BioCypher modules, synergise where possible.
TODO: evaluate generalised graph class as consensus internal representation as
    technical intermediate for other output adapters.
TODO: validation of new entities against schema. Rollback of inconsistent operations.
TODO: retrieval of subgraphs from existing databases.
"""

import json

from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator


class EdgeType(Enum):
    """Types of edges in the graph."""

    SIMPLE = "simple"
    DIRECTED = "directed"
    WEIGHTED = "weighted"
    HYPEREDGE = "hyperedge"


@dataclass
class Node:
    """Represents a node in the graph."""

    id: str
    type: str
    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.id, str):
            raise ValueError("Node ID must be a string")
        if not isinstance(self.type, str):
            raise ValueError("Node type must be a string")

    def to_dict(self) -> dict[str, Any]:
        """Convert node to dictionary representation."""
        return {"id": self.id, "type": self.type, "properties": self.properties}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Node":
        """Create node from dictionary representation."""
        return cls(id=data["id"], type=data["type"], properties=data.get("properties", {}))


@dataclass
class Edge:
    """Represents an edge in the graph."""

    id: str
    type: str
    source: str
    target: str
    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.id, str):
            raise ValueError("Edge ID must be a string")
        if not isinstance(self.type, str):
            raise ValueError("Edge type must be a string")
        if not isinstance(self.source, str):
            raise ValueError("Edge source must be a string")
        if not isinstance(self.target, str):
            raise ValueError("Edge target must be a string")

    def to_dict(self) -> dict[str, Any]:
        """Convert edge to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "target": self.target,
            "properties": self.properties,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Edge":
        """Create edge from dictionary representation."""
        return cls(
            id=data["id"],
            type=data["type"],
            source=data["source"],
            target=data["target"],
            properties=data.get("properties", {}),
        )


@dataclass
class HyperEdge:
    """Represents a hyperedge connecting multiple nodes."""

    id: str
    type: str
    nodes: set[str]
    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.id, str):
            raise ValueError("HyperEdge ID must be a string")
        if not isinstance(self.type, str):
            raise ValueError("HyperEdge type must be a string")
        if not isinstance(self.nodes, set):
            raise ValueError("HyperEdge nodes must be a set")
        if len(self.nodes) < 2:
            raise ValueError("HyperEdge must connect at least 2 nodes")

    def to_dict(self) -> dict[str, Any]:
        """Convert hyperedge to dictionary representation."""
        return {"id": self.id, "type": self.type, "nodes": list(self.nodes), "properties": self.properties}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HyperEdge":
        """Create hyperedge from dictionary representation."""
        return cls(id=data["id"], type=data["type"], nodes=set(data["nodes"]), properties=data.get("properties", {}))


class Graph:
    """Unified graph representation supporting various graph types.

    This class provides a comprehensive graph representation that can handle:
    - Simple undirected graphs
    - Directed graphs
    - Weighted graphs
    - Multigraphs (multiple edges between same nodes)
    - Hypergraphs (edges connecting multiple nodes)
    - Property graphs (nodes and edges with properties)

    The design prioritizes simplicity and extensibility for knowledge representation.
    """

    def __init__(self, name: str = "graph", directed: bool = True):
        """Initialize a new graph.

        Args:
            name: Name of the graph
            directed: Whether the graph is directed (default: True)
        """
        self.name = name
        self.directed = directed

        # Core data structures
        self._nodes: dict[str, Node] = {}
        self._edges: dict[str, Edge] = {}
        self._hyperedges: dict[str, HyperEdge] = {}

        # Indexes for efficient querying
        self._node_types: dict[str, set[str]] = defaultdict(set)
        self._edge_types: dict[str, set[str]] = defaultdict(set)
        self._hyperedge_types: dict[str, set[str]] = defaultdict(set)

        # Adjacency indexes
        self._outgoing: dict[str, set[str]] = defaultdict(set)
        self._incoming: dict[str, set[str]] = defaultdict(set)

        # Statistics
        self._stats = {"nodes": 0, "edges": 0, "hyperedges": 0, "node_types": 0, "edge_types": 0, "hyperedge_types": 0}

    # ==================== NODE OPERATIONS ====================

    def add_node(self, node_id: str, node_type: str, properties: dict[str, Any] | None = None) -> bool:
        """Add a node to the graph.

        Args:
            node_id: Unique identifier for the node
            node_type: Type/category of the node
            properties: Optional properties dictionary

        Returns:
            bool: True if node was added, False if it already exists
        """
        if node_id in self._nodes:
            return False

        node = Node(id=node_id, type=node_type, properties=properties or {})

        self._nodes[node_id] = node
        self._node_types[node_type].add(node_id)
        self._stats["nodes"] += 1
        self._stats["node_types"] = len(self._node_types)

        return True

    def get_node(self, node_id: str) -> Node | None:
        """Get a node by ID.

        Args:
            node_id: Node identifier

        Returns:
            Node object or None if not found
        """
        return self._nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        """Check if a node exists.

        Args:
            node_id: Node identifier

        Returns:
            bool: True if node exists
        """
        return node_id in self._nodes

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its connected edges.

        Args:
            node_id: Node identifier

        Returns:
            bool: True if node was removed, False if not found
        """
        if node_id not in self._nodes:
            return False

        node = self._nodes[node_id]

        # Remove from type index
        self._node_types[node.type].discard(node_id)
        if not self._node_types[node.type]:
            del self._node_types[node.type]

        # Remove connected edges
        edges_to_remove = []
        for edge_id, edge in self._edges.items():
            if edge.source == node_id or edge.target == node_id:
                edges_to_remove.append(edge_id)

        for edge_id in edges_to_remove:
            self.remove_edge(edge_id)

        # Remove from adjacency indexes
        if node_id in self._outgoing:
            del self._outgoing[node_id]
        if node_id in self._incoming:
            del self._incoming[node_id]

        # Remove node
        del self._nodes[node_id]
        self._stats["nodes"] -= 1
        self._stats["node_types"] = len(self._node_types)

        return True

    def get_nodes(self, node_type: str | None = None) -> list[Node]:
        """Get all nodes, optionally filtered by type.

        Args:
            node_type: Optional filter by node type

        Returns:
            List of Node objects
        """
        if node_type is None:
            return list(self._nodes.values())

        node_ids = self._node_types.get(node_type, set())
        return [self._nodes[node_id] for node_id in node_ids]

    def get_node_ids(self, node_type: str | None = None) -> set[str]:
        """Get all node IDs, optionally filtered by type.

        Args:
            node_type: Optional filter by node type

        Returns:
            Set of node IDs
        """
        if node_type is None:
            return set(self._nodes.keys())

        return self._node_types.get(node_type, set()).copy()

    # ==================== EDGE OPERATIONS ====================

    def add_edge(
        self, edge_id: str, edge_type: str, source: str, target: str, properties: dict[str, Any] | None = None
    ) -> bool:
        """Add an edge to the graph.

        Args:
            edge_id: Unique identifier for the edge
            edge_type: Type/category of the edge
            source: Source node ID
            target: Target node ID
            properties: Optional properties dictionary

        Returns:
            bool: True if edge was added, False if it already exists
        """
        if edge_id in self._edges:
            return False

        # Check if nodes exist
        if source not in self._nodes:
            raise ValueError(f"Source node '{source}' does not exist")
        if target not in self._nodes:
            raise ValueError(f"Target node '{target}' does not exist")

        edge = Edge(id=edge_id, type=edge_type, source=source, target=target, properties=properties or {})

        self._edges[edge_id] = edge
        self._edge_types[edge_type].add(edge_id)

        # Update adjacency indexes
        self._outgoing[source].add(edge_id)
        self._incoming[target].add(edge_id)

        self._stats["edges"] += 1
        self._stats["edge_types"] = len(self._edge_types)

        return True

    def get_edge(self, edge_id: str) -> Edge | None:
        """Get an edge by ID.

        Args:
            edge_id: Edge identifier

        Returns:
            Edge object or None if not found
        """
        return self._edges.get(edge_id)

    def has_edge(self, edge_id: str) -> bool:
        """Check if an edge exists.

        Args:
            edge_id: Edge identifier

        Returns:
            bool: True if edge exists
        """
        return edge_id in self._edges

    def remove_edge(self, edge_id: str) -> bool:
        """Remove an edge from the graph.

        Args:
            edge_id: Edge identifier

        Returns:
            bool: True if edge was removed, False if not found
        """
        if edge_id not in self._edges:
            return False

        edge = self._edges[edge_id]

        # Remove from type index
        self._edge_types[edge.type].discard(edge_id)
        if not self._edge_types[edge.type]:
            del self._edge_types[edge.type]

        # Remove from adjacency indexes
        self._outgoing[edge.source].discard(edge_id)
        self._incoming[edge.target].discard(edge_id)

        # Remove edge
        del self._edges[edge_id]
        self._stats["edges"] -= 1
        self._stats["edge_types"] = len(self._edge_types)

        return True

    def get_edges(self, edge_type: str | None = None) -> list[Edge]:
        """Get all edges, optionally filtered by type.

        Args:
            edge_type: Optional filter by edge type

        Returns:
            List of Edge objects
        """
        if edge_type is None:
            return list(self._edges.values())

        edge_ids = self._edge_types.get(edge_type, set())
        return [self._edges[edge_id] for edge_id in edge_ids]

    def get_edges_between(self, source: str, target: str, edge_type: str | None = None) -> list[Edge]:
        """Get edges between two nodes.

        Args:
            source: Source node ID
            target: Target node ID
            edge_type: Optional filter by edge type

        Returns:
            List of Edge objects
        """
        edges = []
        source_edges = self._outgoing.get(source, set())

        for edge_id in source_edges:
            edge = self._edges[edge_id]
            if edge.target == target and (edge_type is None or edge.type == edge_type):
                edges.append(edge)

        return edges

    # ==================== HYPEREDGE OPERATIONS ====================

    def add_hyperedge(
        self, hyperedge_id: str, hyperedge_type: str, nodes: set[str], properties: dict[str, Any] | None = None
    ) -> bool:
        """Add a hyperedge to the graph.

        Args:
            hyperedge_id: Unique identifier for the hyperedge
            hyperedge_type: Type/category of the hyperedge
            nodes: Set of node IDs to connect
            properties: Optional properties dictionary

        Returns:
            bool: True if hyperedge was added, False if it already exists
        """
        if hyperedge_id in self._hyperedges:
            return False

        # Check if all nodes exist
        for node_id in nodes:
            if node_id not in self._nodes:
                raise ValueError(f"Node '{node_id}' does not exist")

        if len(nodes) < 2:
            raise ValueError("Hyperedge must connect at least 2 nodes")

        hyperedge = HyperEdge(id=hyperedge_id, type=hyperedge_type, nodes=nodes, properties=properties or {})

        self._hyperedges[hyperedge_id] = hyperedge
        self._hyperedge_types[hyperedge_type].add(hyperedge_id)

        self._stats["hyperedges"] += 1
        self._stats["hyperedge_types"] = len(self._hyperedge_types)

        return True

    def get_hyperedge(self, hyperedge_id: str) -> HyperEdge | None:
        """Get a hyperedge by ID.

        Args:
            hyperedge_id: Hyperedge identifier

        Returns:
            HyperEdge object or None if not found
        """
        return self._hyperedges.get(hyperedge_id)

    def has_hyperedge(self, hyperedge_id: str) -> bool:
        """Check if a hyperedge exists.

        Args:
            hyperedge_id: Hyperedge identifier

        Returns:
            bool: True if hyperedge exists
        """
        return hyperedge_id in self._hyperedges

    def get_hyperedges(self, hyperedge_type: str | None = None) -> list[HyperEdge]:
        """Get all hyperedges, optionally filtered by type.

        Args:
            hyperedge_type: Optional filter by hyperedge type

        Returns:
            List of HyperEdge objects
        """
        if hyperedge_type is None:
            return list(self._hyperedges.values())

        hyperedge_ids = self._hyperedge_types.get(hyperedge_type, set())
        return [self._hyperedges[hyperedge_id] for hyperedge_id in hyperedge_ids]

    # ==================== GRAPH TRAVERSAL ====================
    # These methods are placeholders. I am not sure it is useful to focus on traversal,
    # retrieval, analysis, etc. in this module. May be better to focus on the agentic
    # creation of the graph here, and figure out if graph traversal is needed in the
    # use cases we want to support.

    def get_neighbors(self, node_id: str, direction: str = "both") -> set[str]:
        """Get neighboring nodes.

        Args:
            node_id: Node identifier
            direction: "in", "out", or "both"

        Returns:
            Set of neighboring node IDs
        """
        if node_id not in self._nodes:
            return set()

        neighbors = set()

        if direction in ["out", "both"]:
            for edge_id in self._outgoing.get(node_id, set()):
                edge = self._edges[edge_id]
                neighbors.add(edge.target)

        if direction in ["in", "both"]:
            for edge_id in self._incoming.get(node_id, set()):
                edge = self._edges[edge_id]
                neighbors.add(edge.source)

        return neighbors

    def get_connected_edges(self, node_id: str, direction: str = "both") -> list[Edge]:
        """Get edges connected to a node.

        Args:
            node_id: Node identifier
            direction: "in", "out", or "both"

        Returns:
            List of connected Edge objects
        """
        edges = []

        if direction in ["out", "both"]:
            for edge_id in self._outgoing.get(node_id, set()):
                edges.append(self._edges[edge_id])

        if direction in ["in", "both"]:
            for edge_id in self._incoming.get(node_id, set()):
                edges.append(self._edges[edge_id])

        return edges

    def find_paths(self, source: str, target: str, max_length: int = 3) -> list[list[Edge]]:
        """Find all paths between two nodes.

        Args:
            source: Source node ID
            target: Target node ID
            max_length: Maximum path length

        Returns:
            List of paths, each path is a list of Edge objects
        """
        if source not in self._nodes or target not in self._nodes:
            return []

        paths = []
        queue = deque([([], source)])
        visited = set()

        while queue:
            path, current = queue.popleft()

            if current == target and path:
                paths.append(path)
                continue

            if len(path) >= max_length:
                continue

            state = (current, len(path))
            if state in visited:
                continue
            visited.add(state)

            # Explore outgoing edges
            for edge_id in self._outgoing.get(current, set()):
                edge = self._edges[edge_id]
                new_path = path + [edge]
                queue.append((new_path, edge.target))

        return paths

    # ==================== GRAPH ANALYSIS ====================
    # These methods are placeholders. Similar to the traversal methods, not fully clear if
    # these are needed.

    def get_statistics(self) -> dict[str, Any]:
        """Get comprehensive graph statistics.

        Returns:
            Dictionary with graph statistics
        """
        # Ensure we have the latest counts by recalculating from actual data
        actual_nodes = len(self._nodes)
        actual_edges = len(self._edges)
        actual_hyperedges = len(self._hyperedges)

        # Update internal stats to match actual counts
        self._stats["nodes"] = actual_nodes
        self._stats["edges"] = actual_edges
        self._stats["hyperedges"] = actual_hyperedges
        self._stats["node_types"] = len(self._node_types)
        self._stats["edge_types"] = len(self._edge_types)
        self._stats["hyperedge_types"] = len(self._hyperedge_types)

        # Node type distribution
        node_type_dist = {node_type: len(nodes) for node_type, nodes in self._node_types.items()}

        # Edge type distribution
        edge_type_dist = {edge_type: len(edges) for edge_type, edges in self._edge_types.items()}

        # Hyperedge type distribution
        hyperedge_type_dist = {
            hyperedge_type: len(hyperedges) for hyperedge_type, hyperedges in self._hyperedge_types.items()
        }

        # Connectivity analysis
        isolated_nodes = 0
        for node_id in self._nodes:
            if not self.get_neighbors(node_id):
                isolated_nodes += 1

        return {
            "basic": self._stats.copy(),
            "node_types": node_type_dist,
            "edge_types": edge_type_dist,
            "hyperedge_types": hyperedge_type_dist,
            "connectivity": {"isolated_nodes": isolated_nodes, "connected_nodes": actual_nodes - isolated_nodes},
        }

    def get_subgraph(self, node_ids: set[str], include_edges: bool = True) -> "Graph":
        """Extract a subgraph containing specified nodes.

        Args:
            node_ids: Set of node IDs to include
            include_edges: Whether to include edges between included nodes

        Returns:
            New Graph object containing the subgraph
        """
        subgraph = Graph(name=f"{self.name}_subgraph", directed=self.directed)

        # Add nodes
        for node_id in node_ids:
            if node_id in self._nodes:
                node = self._nodes[node_id]
                subgraph.add_node(node.id, node.type, node.properties)

        # Add edges (if requested)
        if include_edges:
            for edge in self._edges.values():
                if edge.source in node_ids and edge.target in node_ids:
                    subgraph.add_edge(edge.id, edge.type, edge.source, edge.target, edge.properties)

        return subgraph

    # ==================== SERIALIZATION ====================
    # Placeholder methods, as serialisation should probably be handled by the corresponding
    # legacy BioCypher modules.

    def to_dict(self) -> dict[str, Any]:
        """Convert graph to dictionary representation.

        Returns:
            Dictionary representation of the graph
        """
        return {
            "name": self.name,
            "directed": self.directed,
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "edges": [edge.to_dict() for edge in self._edges.values()],
            "hyperedges": [hyperedge.to_dict() for hyperedge in self._hyperedges.values()],
            "statistics": self.get_statistics(),
        }

    def to_json(self) -> str:
        """Convert graph to JSON string.

        Returns:
            JSON string representation of the graph
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Graph":
        """Create graph from dictionary representation.

        Args:
            data: Dictionary representation of the graph

        Returns:
            Graph object
        """
        graph = cls(name=data["name"], directed=data["directed"])

        # Add nodes
        for node_data in data["nodes"]:
            node = Node.from_dict(node_data)
            graph._nodes[node.id] = node
            graph._node_types[node.type].add(node.id)

        # Add edges
        for edge_data in data["edges"]:
            edge = Edge.from_dict(edge_data)
            graph._edges[edge.id] = edge
            graph._edge_types[edge.type].add(edge.id)
            graph._outgoing[edge.source].add(edge.id)
            graph._incoming[edge.target].add(edge.id)

        # Add hyperedges
        for hyperedge_data in data["hyperedges"]:
            hyperedge = HyperEdge.from_dict(hyperedge_data)
            graph._hyperedges[hyperedge.id] = hyperedge
            graph._hyperedge_types[hyperedge.type].add(hyperedge.id)

        # Update statistics
        graph._stats["nodes"] = len(graph._nodes)
        graph._stats["edges"] = len(graph._edges)
        graph._stats["hyperedges"] = len(graph._hyperedges)
        graph._stats["node_types"] = len(graph._node_types)
        graph._stats["edge_types"] = len(graph._edge_types)
        graph._stats["hyperedge_types"] = len(graph._hyperedge_types)

        return graph

    @classmethod
    def from_json_string(cls, json_str: str) -> "Graph":
        """Create graph from JSON string.

        Args:
            json_str: JSON string representation of the graph

        Returns:
            Graph object
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def from_json(self, json_str: str) -> None:
        """Load graph data from JSON string into this graph instance.

        This method clears the existing graph and loads new data from JSON.

        Args:
            json_str: JSON string representation of the graph
        """
        data = json.loads(json_str)

        # Clear existing data
        self.clear()

        # Update graph properties
        self.name = data["name"]
        self.directed = data["directed"]

        # Add nodes
        for node_data in data["nodes"]:
            node = Node.from_dict(node_data)
            self._nodes[node.id] = node
            self._node_types[node.type].add(node.id)

        # Add edges
        for edge_data in data["edges"]:
            edge = Edge.from_dict(edge_data)
            self._edges[edge.id] = edge
            self._edge_types[edge.type].add(edge.id)
            self._outgoing[edge.source].add(edge.id)
            self._incoming[edge.target].add(edge.id)

        # Add hyperedges
        for hyperedge_data in data["hyperedges"]:
            hyperedge = HyperEdge.from_dict(hyperedge_data)
            self._hyperedges[hyperedge.id] = hyperedge
            self._hyperedge_types[hyperedge.type].add(hyperedge.id)

        # Update statistics
        self._stats["nodes"] = len(self._nodes)
        self._stats["edges"] = len(self._edges)
        self._stats["hyperedges"] = len(self._hyperedges)
        self._stats["node_types"] = len(self._node_types)
        self._stats["edge_types"] = len(self._edge_types)
        self._stats["hyperedge_types"] = len(self._hyperedge_types)

    # ==================== UTILITY METHODS ====================

    def clear(self) -> None:
        """Clear all nodes, edges, and hyperedges from the graph."""
        self._nodes.clear()
        self._edges.clear()
        self._hyperedges.clear()
        self._node_types.clear()
        self._edge_types.clear()
        self._hyperedge_types.clear()
        self._outgoing.clear()
        self._incoming.clear()
        self._stats = {"nodes": 0, "edges": 0, "hyperedges": 0, "node_types": 0, "edge_types": 0, "hyperedge_types": 0}

    def __len__(self) -> int:
        """Return the number of nodes in the graph."""
        return len(self._nodes)

    def __contains__(self, node_id: str) -> bool:
        """Check if a node exists in the graph."""
        return node_id in self._nodes

    def __iter__(self) -> Iterator[Node]:
        """Iterate over all nodes in the graph."""
        return iter(self._nodes.values())

    def __str__(self) -> str:
        """String representation of the graph."""
        stats = self.get_statistics()
        return (
            f"Graph(name='{self.name}', nodes={stats['basic']['nodes']}, "
            f"edges={stats['basic']['edges']}, hyperedges={stats['basic']['hyperedges']})"
        )

    def __repr__(self) -> str:
        return self.__str__()
