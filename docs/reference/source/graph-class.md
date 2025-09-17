# Graph Class

The `Graph` class provides a unified graph representation supporting various graph types including simple graphs, directed graphs, weighted graphs, multigraphs, and hypergraphs. The design focuses on simplicity and extensibility for knowledge representation.

## Overview

```python
from biocypher import Graph

# Create a new graph
graph = Graph(name="my_graph", directed=True)
```

## Constructor

### `Graph.__init__()`

```python
def __init__(self, name: str = "graph", directed: bool = True) -> None
```

**Parameters:**

- `name` (str): Name of the graph (default: "graph")
- `directed` (bool): Whether the graph is directed (default: True)

## Data Structures

The Graph class uses the following core data structures:

- `_nodes`: Dictionary mapping node IDs to Node objects
- `_edges`: Dictionary mapping edge IDs to Edge objects
- `_hyperedges`: Dictionary mapping hyperedge IDs to HyperEdge objects
- `_node_types`: Index of nodes by type
- `_edge_types`: Index of edges by type
- `_hyperedge_types`: Index of hyperedges by type
- `_outgoing`: Adjacency index for outgoing edges
- `_incoming`: Adjacency index for incoming edges

## Node Operations

### `add_node()`

```python
def add_node(self, node_id: str, node_type: str, properties: dict[str, Any] | None = None) -> bool
```

Add a node to the graph.

**Parameters:**
- `node_id` (str): Unique identifier for the node
- `node_type` (str): Type/category of the node
- `properties` (dict, optional): Node properties dictionary

**Returns:**
- `bool`: True if node was added, False if it already exists

**Example:**
```python
graph.add_node("protein_1", "protein", {"name": "TP53", "function": "tumor_suppressor"})
```

### `get_node()`

```python
def get_node(self, node_id: str) -> Node | None
```

Get a node by ID.

**Parameters:**
- `node_id` (str): Node identifier

**Returns:**
- `Node | None`: Node object or None if not found

### `has_node()`

```python
def has_node(self, node_id: str) -> bool
```

Check if a node exists.

**Parameters:**
- `node_id` (str): Node identifier

**Returns:**
- `bool`: True if node exists

### `remove_node()`

```python
def remove_node(self, node_id: str) -> bool
```

Remove a node from the graph.

**Parameters:**
- `node_id` (str): Node identifier

**Returns:**
- `bool`: True if node was removed, False if not found

### `get_nodes()`

```python
def get_nodes(self, node_type: str | None = None) -> list[Node]
```

Get nodes, optionally filtered by type.

**Parameters:**
- `node_type` (str, optional): Filter by node type

**Returns:**
- `list[Node]`: List of nodes

### `get_node_ids()`

```python
def get_node_ids(self, node_type: str | None = None) -> set[str]
```

Get all node IDs, optionally filtered by type.

**Parameters:**
- `node_type` (str, optional): Filter by node type

**Returns:**
- `set[str]`: Set of node IDs

## Edge Operations

### `add_edge()`

```python
def add_edge(
    self,
    edge_id: str,
    edge_type: str,
    source: str,
    target: str,
    properties: dict[str, Any] | None = None
) -> bool
```

Add an edge to the graph.

**Parameters:**
- `edge_id` (str): Unique identifier for the edge
- `edge_type` (str): Type/category of the edge
- `source` (str): Source node ID
- `target` (str): Target node ID
- `properties` (dict, optional): Edge properties dictionary

**Returns:**
- `bool`: True if edge was added, False if it already exists

**Raises:**
- `ValueError`: If source or target node does not exist

**Example:**
```python
graph.add_edge("interaction_1", "interaction", "protein_1", "protein_2", {"confidence": 0.8})
```

### `get_edge()`

```python
def get_edge(self, edge_id: str) -> Edge | None
```

Get an edge by ID.

**Parameters:**
- `edge_id` (str): Edge identifier

**Returns:**
- `Edge | None`: Edge object or None if not found

### `has_edge()`

```python
def has_edge(self, edge_id: str) -> bool
```

Check if an edge exists.

**Parameters:**
- `edge_id` (str): Edge identifier

**Returns:**
- `bool`: True if edge exists

### `remove_edge()`

```python
def remove_edge(self, edge_id: str) -> bool
```

Remove an edge from the graph.

**Parameters:**
- `edge_id` (str): Edge identifier

**Returns:**
- `bool`: True if edge was removed, False if not found

### `get_edges()`

```python
def get_edges(self, edge_type: str | None = None) -> list[Edge]
```

Get edges, optionally filtered by type.

**Parameters:**
- `edge_type` (str, optional): Filter by edge type

**Returns:**
- `list[Edge]`: List of edges

### `get_edges_between()`

```python
def get_edges_between(self, source: str, target: str, edge_type: str | None = None) -> list[Edge]
```

Get edges between two specific nodes.

**Parameters:**
- `source` (str): Source node ID
- `target` (str): Target node ID
- `edge_type` (str, optional): Filter by edge type

**Returns:**
- `list[Edge]`: List of edges between the nodes

## HyperEdge Operations

### `add_hyperedge()`

```python
def add_hyperedge(
    self,
    hyperedge_id: str,
    hyperedge_type: str,
    nodes: set[str],
    properties: dict[str, Any] | None = None
) -> bool
```

Add a hyperedge connecting multiple nodes.

**Parameters:**
- `hyperedge_id` (str): Unique identifier for the hyperedge
- `hyperedge_type` (str): Type/category of the hyperedge
- `nodes` (set[str]): Set of node IDs to connect
- `properties` (dict, optional): Hyperedge properties dictionary

**Returns:**
- `bool`: True if hyperedge was added, False if it already exists

**Raises:**
- `ValueError`: If any node in the set does not exist

**Example:**
```python
graph.add_hyperedge("complex_1", "complex", {"protein_1", "protein_2", "protein_3"})
```

### `get_hyperedge()`

```python
def get_hyperedge(self, hyperedge_id: str) -> HyperEdge | None
```

Get a hyperedge by ID.

**Parameters:**
- `hyperedge_id` (str): Hyperedge identifier

**Returns:**
- `HyperEdge | None`: Hyperedge object or None if not found

### `has_hyperedge()`

```python
def has_hyperedge(self, hyperedge_id: str) -> bool
```

Check if a hyperedge exists.

**Parameters:**
- `hyperedge_id` (str): Hyperedge identifier

**Returns:**
- `bool`: True if hyperedge exists

### `remove_hyperedge()`

```python
def remove_hyperedge(self, hyperedge_id: str) -> bool
```

Remove a hyperedge from the graph.

**Parameters:**
- `hyperedge_id` (str): Hyperedge identifier

**Returns:**
- `bool`: True if hyperedge was removed, False if not found

### `get_hyperedges()`

```python
def get_hyperedges(self, hyperedge_type: str | None = None) -> list[HyperEdge]
```

Get hyperedges, optionally filtered by type.

**Parameters:**
- `hyperedge_type` (str, optional): Filter by hyperedge type

**Returns:**
- `list[HyperEdge]`: List of hyperedges

## Graph Traversal

### `get_neighbors()`

```python
def get_neighbors(self, node_id: str, direction: str = "both") -> set[str]
```

Get neighbors of a node.

**Parameters:**
- `node_id` (str): Node identifier
- `direction` (str): "in", "out", or "both" (default: "both")

**Returns:**
- `set[str]`: Set of neighbor node IDs

### `get_connected_edges()`

```python
def get_connected_edges(self, node_id: str) -> list[Edge]
```

Get all edges connected to a node.

**Parameters:**
- `node_id` (str): Node identifier

**Returns:**
- `list[Edge]`: List of connected edges

### `find_paths()`

```python
def find_paths(self, source: str, target: str, max_length: int | None = None) -> list[list[str]]
```

Find paths between two nodes using breadth-first search.

**Parameters:**
- `source` (str): Source node ID
- `target` (str): Target node ID
- `max_length` (int, optional): Maximum path length

**Returns:**
- `list[list[str]]`: List of paths (each path is a list of node IDs)

### `find_connected_components()`

```python
def find_connected_components(self, start_node: str, max_depth: int | None = None) -> dict[str, Any]
```

Find connected components starting from a node.

**Parameters:**
- `start_node` (str): Starting node ID
- `max_depth` (int, optional): Maximum depth to search

**Returns:**
- `dict[str, Any]`: Connected components data

## Analysis and Statistics

### `get_statistics()`

```python
def get_statistics(self) -> dict[str, Any]
```

Get comprehensive graph statistics.

**Returns:**
- `dict[str, Any]`: Statistics dictionary with the following keys:
  - `basic`: Basic counts (nodes, edges, hyperedges, types)
  - `connectivity`: Connectivity metrics (density, clustering, etc.)

### `get_summary()`

```python
def get_summary(self) -> dict[str, Any]
```

Get human-readable summary of the graph.

**Returns:**
- `dict[str, Any]`: Summary dictionary

## Serialization

### `to_dict()`

```python
def to_dict(self) -> dict[str, Any]
```

Convert the graph to a dictionary representation.

**Returns:**
- `dict[str, Any]`: Dictionary representation

### `from_dict()`

```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> "Graph"
```

Create a graph from a dictionary representation.

**Parameters:**
- `data` (dict): Dictionary representation

**Returns:**
- `Graph`: New graph instance

### `to_json()`

```python
def to_json(self) -> str
```

Export the graph to JSON format.

**Returns:**
- `str`: JSON string representation

### `from_json()`

```python
@classmethod
def from_json(cls, json_str: str) -> "Graph"
```

Create a graph from JSON string.

**Parameters:**
- `json_str` (str): JSON string representation

**Returns:**
- `Graph`: New graph instance

## Utility Methods

### `clear()`

```python
def clear(self) -> None
```

Clear all nodes, edges, and hyperedges from the graph.

### `copy()`

```python
def copy(self) -> "Graph"
```

Create a deep copy of the graph.

**Returns:**
- `Graph`: New graph instance

### `__len__()`

```python
def __len__(self) -> int
```

Return the number of nodes in the graph.

**Returns:**
- `int`: Number of nodes

### `__contains__()`

```python
def __contains__(self, node_id: str) -> bool
```

Check if a node exists in the graph.

**Parameters:**
- `node_id` (str): Node identifier

**Returns:**
- `bool`: True if node exists

## Properties

- `name` (str): Name of the graph
- `directed` (bool): Whether the graph is directed
- `_stats` (dict): Internal statistics tracking

## Built-in Deduplication

The Graph class has built-in deduplication that prevents:
- Duplicate nodes with the same ID
- Duplicate edges with the same ID
- Duplicate hyperedges with the same ID

This is a fundamental property of graphs and cannot be disabled.

## Examples

### Basic Usage

```python
from biocypher import Graph

# Create graph
graph = Graph("protein_network", directed=True)

# Add nodes
graph.add_node("TP53", "protein", {"name": "TP53", "function": "tumor_suppressor"})
graph.add_node("BRAF", "protein", {"name": "BRAF", "function": "kinase"})

# Add edge
graph.add_edge("interaction_1", "interaction", "TP53", "BRAF", {"confidence": 0.8})

# Query
proteins = graph.get_nodes("protein")
print(f"Found {len(proteins)} proteins")

# Traversal
neighbors = graph.get_neighbors("TP53")
print(f"TP53 has {len(neighbors)} neighbors")
```

### HyperEdge Usage

```python
# Add hyperedge (complex)
graph.add_hyperedge(
    "complex_1",
    "complex",
    {"TP53", "BRAF", "MDM2"},
    {"function": "cell_cycle_control"}
)

# Get complex
complex_edges = graph.get_hyperedges("complex")
print(f"Found {len(complex_edges)} complexes")
```

### Path Finding

```python
# Find paths between nodes
paths = graph.find_paths("TP53", "BRAF", max_length=3)
print(f"Found {len(paths)} paths between TP53 and BRAF")

for path in paths:
    print(f"Path: {' -> '.join(path)}")
```

### Statistics

```python
# Get comprehensive statistics
stats = graph.get_statistics()
print(f"Nodes: {stats['basic']['nodes']}")
print(f"Edges: {stats['basic']['edges']}")
print(f"Hyperedges: {stats['basic']['hyperedges']}")

# Get summary
summary = graph.get_summary()
print(f"Graph: {summary['name']}")
print(f"Top node types: {summary['top_node_types']}")
```

### Serialization

```python
# Export to JSON
json_str = graph.to_json()

# Create new graph from JSON
new_graph = Graph.from_json(json_str)

# Verify they're the same
assert len(graph) == len(new_graph)
```
