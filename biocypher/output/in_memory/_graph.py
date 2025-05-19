"""Intermediate node and edge types compatible with BioCypher."""

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

from biocypher._create import BioCypherEdge, BioCypherNode


@dataclass(frozen=True)
class NodeInfo:
    """A type safe intermediate node compatible with BioCypher."""

    id: str
    label: str
    properties: Mapping[str, Any]

    def __iter__(self) -> Iterator[Any]:
        """Implement the tuple protocol for BioCypher."""
        return iter((self.id, self.label, self.properties))

    def __len__(self) -> int:
        """Implement the tuple protocol for BioCypher."""
        return 3


@dataclass(frozen=True)
class EdgeInfo:
    """A type safe intermediate edge compatible with BioCypher."""

    id: str
    source_id: str
    target_id: str
    label: str
    properties: Mapping[str, Any]

    def __iter__(self) -> Iterator[Any]:
        """Implement the tuple protocol for BioCypher."""
        return iter((self.id, self.source_id, self.target_id, self.label, self.properties))

    def __len__(self) -> int:
        """Implement the tuple protocol for BioCypher."""
        return 5


class Graph:
    """
    An in-memory graph data structure to store nodes and edges.

    This class provides functionality to create and manage a graph structure
    compatible with BioCypher's data model.
    """

    def __init__(self):
        """Initialize an empty graph with no nodes or edges."""
        self.nodes: List[NodeInfo] = []
        self.edges: List[EdgeInfo] = []
        self._node_ids: Dict[str, int] = {}  # Maps node IDs to their index in self.nodes

    def add_nodes(self, nodes: Union[NodeInfo, Tuple, Iterable[Union[NodeInfo, Tuple]]]) -> None:
        """
        Add nodes to the graph.

        Args:
            nodes: Either a single NodeInfo object, a single tuple with format (id, label, properties),
                  or an iterable of NodeInfo objects or tuples.
        """
        # Handle single node case
        if isinstance(nodes, (NodeInfo, tuple)) or not hasattr(nodes, "__iter__"):
            nodes = [nodes]

        # Process all nodes
        for node in nodes:
            if not isinstance(node, NodeInfo):
                # Convert tuple to NodeInfo if needed
                if len(node) != 3:
                    raise ValueError(f"Node tuple must have exactly 3 elements, got {len(node)}")
                node = NodeInfo(id=node[0], label=node[1], properties=node[2])

            # Only add the node if its ID is not already in the graph
            if node.id not in self._node_ids:
                self.nodes.append(node)
                self._node_ids[node.id] = len(self.nodes) - 1

    def add_edges(self, edges: Union[EdgeInfo, Tuple, Iterable[Union[EdgeInfo, Tuple]]]) -> None:
        """
        Add edges to the graph.

        Args:
            edges: Either a single EdgeInfo object, a single tuple with format
                  (id, source_id, target_id, label, properties) or an iterable of EdgeInfo objects or tuples.
        """
        # Handle single edge case
        if isinstance(edges, (NodeInfo, tuple)) or not hasattr(edges, "__iter__"):
            edges = [edges]

        for edge in edges:
            if not isinstance(edge, EdgeInfo):
                # Convert tuple to EdgeInfo if needed
                if len(edge) != 5:
                    raise ValueError(f"Edge tuple must have exactly 5 elements, got {len(edge)}")
                edge = EdgeInfo(id=edge[0], source_id=edge[1], target_id=edge[2], label=edge[3], properties=edge[4])

            # # Verify that the source and target nodes exist
            # if edge.source_id not in self._node_ids:
            #     raise ValueError(f"Source node with id {edge.source_id} does not exist in the graph")
            # if edge.target_id not in self._node_ids:
            #     raise ValueError(f"Target node with id {edge.target_id} does not exist in the graph")

            self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[NodeInfo]:
        """
        Get a node by its ID.

        Args:
            node_id: The ID of the node to retrieve.

        Returns:
            The NodeInfo object if found, None otherwise.
        """
        if node_id in self._node_ids:
            return self.nodes[self._node_ids[node_id]]
        return None

    def get_node_edges(self, node_id: str) -> List[EdgeInfo]:
        """
        Get all edges connected to a node.

        Args:
            node_id: The ID of the node.

        Returns:
            A list of EdgeInfo objects connected to the node.
        """
        return [edge for edge in self.edges if edge.source_id == node_id or edge.target_id == node_id]

    def clear(self) -> None:
        """Remove all nodes and edges from the graph."""
        self.nodes = []
        self.edges = []
        self._node_ids = {}

    def to_biocypher_nodes(self) -> List[BioCypherNode]:
        """
        Convert all nodes in the graph to BioCypherNode objects.

        Returns:
            A list of BioCypherNode objects
        """
        return [
            BioCypherNode(node_id=node.id, node_label=node.label, properties=node.properties) for node in self.nodes
        ]

    def to_biocypher_edges(self) -> List[BioCypherEdge]:
        """
        Convert all edges in the graph to BioCypherEdge objects.

        Returns:
            A list of BioCypherEdge objects
        """
        return [
            BioCypherEdge(
                relationship_id=edge.id,
                source_id=edge.source_id,
                target_id=edge.target_id,
                relationship_label=edge.label,
                properties=edge.properties,
            )
            for edge in self.edges
        ]
