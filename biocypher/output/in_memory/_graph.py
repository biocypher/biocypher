"""Intermediate node and edge types compatible with BioCypher."""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, fields
from typing import Any, Dict, List, Optional, Tuple, Union

from biocypher._create import BioCypherEdge, BioCypherNode


@dataclass(frozen=True)
class GraphComponentInfo(ABC):
    """Abstract base class for Graph structures such as Nodes and Edges"""

    def __iter__(self) -> Iterator[Any]:
        """Automatically iterate over all field values."""
        return (getattr(self, field.name) for field in fields(self))

    def __len__(self) -> int:
        """Return the number of fields."""
        return len(fields(self))


@dataclass(frozen=True)
class NodeInfo(GraphComponentInfo):
    """A type safe intermediate node compatible with BioCypher."""

    id: str
    label: str
    properties: Mapping[str, Any]


@dataclass(frozen=True)
class EdgeInfo(GraphComponentInfo):
    """A type safe intermediate edge compatible with BioCypher."""

    id: str
    source_id: str
    target_id: str
    label: str
    properties: Mapping[str, Any]


class Graph:
    """
    An in-memory graph data structure to store nodes and edges.

    This class provides functionality to create and manage a graph structure
    compatible with BioCypher's data model.
    """

    def __init__(self, deduplicator=None, output_format="adj_list"):
        """Initialize an empty graph with no nodes or edges."""
        self.nodes: List[NodeInfo] = []
        self.edges: List[EdgeInfo] = []
        self._node_ids: Dict[str, int] = {}
        self.deduplicator = deduplicator
        self.output_format = output_format

    def get_kg(self):
        """Return the KG in the configured output format."""
        if self.output_format == "networkx":
            return self.to_networkx()
        elif self.output_format in ["csv", "pandas", "tabular"]:
            return self.to_pandas()
        elif self.output_format == "adj_list":
            return self.to_adj_list()
        else:
            return self 
    
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
                if len(node) != len(fields(NodeInfo)):
                    raise ValueError(f"Node tuple must have exactly {len(fields(NodeInfo))} elements, got {len(node)}")
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
                if len(edge) != len(fields(EdgeInfo)):
                    raise ValueError(f"Edge tuple must have exactly {len(fields(NodeInfo))} elements, got {len(edge)}")
                edge = EdgeInfo(id=edge[0], source_id=edge[1], target_id=edge[2], label=edge[3], properties=edge[4])

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

    def to_adj_list(self) -> Dict[str, List[str]]:
        """
        Convert the graph to an undirected adjacency list representation.

        Returns:
            A dictionary where keys are node IDs and values are lists of
            adjacent node IDs (considering edges as undirected).
        """
        adj_list = {}

        # Initialize adjacency list with all nodes
        for node in self.nodes:
            adj_list[node.id] = []

        # Add edges to adjacency list (bidirectional)
        for edge in self.edges:
            # Add forward direction
            if edge.source_id in adj_list:
                adj_list[edge.source_id].append(edge.target_id)
            else:
                adj_list[edge.source_id] = [edge.target_id]

            # Add reverse direction
            if edge.target_id in adj_list:
                adj_list[edge.target_id].append(edge.source_id)
            else:
                adj_list[edge.target_id] = [edge.source_id]

        return adj_list
    
    def to_networkx(self):
        """Convert the graph to a NetworkX DiGraph.
        
        Returns:
            networkx.DiGraph: A directed graph with nodes and edges from this graph.
            
        Raises:
            ImportError: If NetworkX is not installed.
        """
        try:
            import networkx as nx
        except ImportError:
            raise ImportError("NetworkX is required for this functionality. Install with: pip install networkx")
        
        G = nx.DiGraph()
        
        # Add nodes with their properties
        for node in self.nodes:
            G.add_node(node.id, label=node.label, **node.properties)
        
        # Add edges with their properties
        for edge in self.edges:
            G.add_edge(
                edge.source_id, 
                edge.target_id, 
                id=edge.id,
                label=edge.label, 
                **edge.properties
            )
        
        return G

    def to_pandas(self):
        """Convert the graph to pandas DataFrames.
        
        Returns:
            dict: Dictionary with 'nodes' and 'edges' keys containing DataFrames.
            
        Raises:
            ImportError: If pandas is not installed.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Pandas is required for this functionality. Install with: pip install pandas")
        
        # Convert nodes to DataFrame
        nodes_data = []
        for node in self.nodes:
            node_dict = {'id': node.id, 'label': node.label}
            node_dict.update(node.properties)
            nodes_data.append(node_dict)
        
        # Convert edges to DataFrame
        edges_data = []
        for edge in self.edges:
            edge_dict = {
                'id': edge.id,
                'source_id': edge.source_id,
                'target_id': edge.target_id,
                'label': edge.label
            }
            edge_dict.update(edge.properties)
            edges_data.append(edge_dict)
        
        return {
            'nodes': pd.DataFrame(nodes_data) if nodes_data else pd.DataFrame(),
            'edges': pd.DataFrame(edges_data) if edges_data else pd.DataFrame()
        }