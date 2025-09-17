# BioCypherWorkflow

The `BioCypherWorkflow` class provides a streamlined interface for creating and managing knowledge graphs using the unified Graph representation, with optional schema and ontology support. Designed for both agentic and deterministic workflows.

## Overview

```python
from biocypher import create_workflow

# Create a new workflow
workflow = create_workflow(
    name="my_graph",
    validation_mode="warn",
    deduplication=True
)
```

## Constructor

### `BioCypherWorkflow.__init__()`

```python
def __init__(
    self,
    name: str = "workflow_graph",
    directed: bool = True,
    schema: dict[str, Any] | None = None,
    schema_file: str | None = None,
    head_ontology_url: str | None = None,
    validation_mode: str = "none",
    deduplication: bool = False,
) -> None
```

**Parameters:**

- `name` (str): Name of the knowledge graph (default: "workflow_graph")
- `directed` (bool): Whether the graph is directed (default: True)
- `schema` (dict): Dictionary defining the knowledge graph schema
- `schema_file` (str): Path to YAML schema file
- `head_ontology_url` (str): URL to ontology file (defaults to Biolink model)
- `validation_mode` (str): Validation level - "none", "warn", or "strict" (default: "none")
- `deduplication` (bool): Whether to enable deduplication tracking (default: False)

## Validation Modes

### "none" (Default)
- No validation or deduplication overhead
- Maximum flexibility for agents
- Any node/edge types allowed

### "warn"
- Logs warnings for schema violations and duplicates
- Continues processing
- Good for debugging and development

### "strict"
- Enforces schema validation and deduplication
- Fails fast on violations
- Legacy BioCypher behavior

## Node Operations

### `add_node()`

```python
def add_node(self, node_id: str, node_type: str, **properties) -> bool
```

Add a node to the knowledge graph.

**Parameters:**
- `node_id` (str): Unique identifier for the node
- `node_type` (str): Type/category of the node
- `**properties`: Node properties as keyword arguments

**Returns:**
- `bool`: True if node was added, False if it already exists

**Example:**
```python
workflow.add_node("protein_1", "protein", name="TP53", function="tumor_suppressor")
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

### `get_nodes()`

```python
def get_nodes(self, node_type: str | None = None) -> list[Node]
```

Get nodes, optionally filtered by type.

**Parameters:**
- `node_type` (str, optional): Filter by node type

**Returns:**
- `list[Node]`: List of nodes

### `remove_node()`

```python
def remove_node(self, node_id: str) -> bool
```

Remove a node from the graph.

**Parameters:**
- `node_id` (str): Node identifier

**Returns:**
- `bool`: True if node was removed, False if not found

## Edge Operations

### `add_edge()`

```python
def add_edge(self, edge_id: str, edge_type: str, source: str, target: str, **properties) -> bool
```

Add an edge to the knowledge graph.

**Parameters:**
- `edge_id` (str): Unique identifier for the edge
- `edge_type` (str): Type/category of the edge
- `source` (str): Source node ID
- `target` (str): Target node ID
- `**properties`: Edge properties as keyword arguments

**Returns:**
- `bool`: True if edge was added, False if it already exists

**Example:**
```python
workflow.add_edge("interaction_1", "interaction", "protein_1", "protein_2", confidence=0.8)
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

### `get_edges()`

```python
def get_edges(self, edge_type: str | None = None) -> list[Edge]
```

Get edges, optionally filtered by type.

**Parameters:**
- `edge_type` (str, optional): Filter by edge type

**Returns:**
- `list[Edge]`: List of edges

### `remove_edge()`

```python
def remove_edge(self, edge_id: str) -> bool
```

Remove an edge from the graph.

**Parameters:**
- `edge_id` (str): Edge identifier

**Returns:**
- `bool`: True if edge was removed, False if not found

## HyperEdge Operations

### `add_hyperedge()`

```python
def add_hyperedge(self, hyperedge_id: str, hyperedge_type: str, nodes: set[str], **properties) -> bool
```

Add a hyperedge connecting multiple nodes.

**Parameters:**
- `hyperedge_id` (str): Unique identifier for the hyperedge
- `hyperedge_type` (str): Type/category of the hyperedge
- `nodes` (set[str]): Set of node IDs to connect
- `**properties`: Hyperedge properties as keyword arguments

**Returns:**
- `bool`: True if hyperedge was added, False if it already exists

**Example:**
```python
workflow.add_hyperedge("complex_1", "complex", {"protein_1", "protein_2", "protein_3"})
```

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

### `find_paths()`

```python
def find_paths(self, source: str, target: str, max_length: int | None = None) -> list[list[str]]
```

Find paths between two nodes.

**Parameters:**
- `source` (str): Source node ID
- `target` (str): Target node ID
- `max_length` (int, optional): Maximum path length

**Returns:**
- `list[list[str]]`: List of paths (each path is a list of node IDs)

## Query Interface

### `query_nodes()`

```python
def query_nodes(self, node_type: str | None = None) -> list[dict[str, Any]]
```

Query nodes and return as dictionaries.

**Parameters:**
- `node_type` (str, optional): Filter by node type

**Returns:**
- `list[dict[str, Any]]`: List of node dictionaries

### `query_edges()`

```python
def query_edges(self, edge_type: str | None = None) -> list[dict[str, Any]]
```

Query edges and return as dictionaries.

**Parameters:**
- `edge_type` (str, optional): Filter by edge type

**Returns:**
- `list[dict[str, Any]]`: List of edge dictionaries

## Schema Support

### `validate_against_schema()`

```python
def validate_against_schema(self, node_type: str, properties: dict[str, Any]) -> bool
```

Validate node properties against schema.

**Parameters:**
- `node_type` (str): Type of node to validate
- `properties` (dict): Properties to validate

**Returns:**
- `bool`: True if valid, False otherwise

### `get_schema()`

```python
def get_schema(self) -> dict[str, Any] | None
```

Get the current schema configuration.

**Returns:**
- `dict[str, Any] | None`: Schema dictionary or None

### `export_schema()`

```python
def export_schema(self, filepath: str) -> None
```

Export the current schema to a YAML file.

**Parameters:**
- `filepath` (str): Path to save the schema file

## Serialization

### `to_json()`

```python
def to_json(self) -> str
```

Export the knowledge graph to JSON format.

**Returns:**
- `str`: JSON string representation

### `from_json()`

```python
def from_json(self, json_str: str) -> None
```

Load knowledge graph from JSON string.

**Parameters:**
- `json_str` (str): JSON string representation

### `save()`

```python
def save(self, filepath: str) -> None
```

Save the workflow to a JSON file.

**Parameters:**
- `filepath` (str): Path to save the file

### `load()`

```python
def load(self, filepath: str) -> None
```

Load the workflow from a JSON file.

**Parameters:**
- `filepath` (str): Path to load the file from

## Compatibility Wrappers

### `to_networkx()`

```python
def to_networkx(self) -> nx.Graph
```

Convert to NetworkX graph for compatibility with existing tools.

**Returns:**
- `nx.Graph`: NetworkX graph object

### `to_pandas()`

```python
def to_pandas(self) -> tuple[pd.DataFrame, pd.DataFrame]
```

Convert to Pandas DataFrames for compatibility with existing tools.

**Returns:**
- `tuple[pd.DataFrame, pd.DataFrame]`: (nodes_df, edges_df)

## Analysis and Statistics

### `get_statistics()`

```python
def get_statistics(self) -> dict[str, Any]
```

Get comprehensive graph statistics.

**Returns:**
- `dict[str, Any]`: Statistics dictionary

### `get_summary()`

```python
def get_summary(self) -> dict[str, Any]
```

Get human-readable summary of the graph.

**Returns:**
- `dict[str, Any]`: Summary dictionary

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

## Utility Methods

### `clear()`

```python
def clear(self) -> None
```

Clear all nodes and edges from the workflow.

### `copy()`

```python
def copy(self) -> "BioCypherWorkflow"
```

Create a deep copy of the workflow.

**Returns:**
- `BioCypherWorkflow`: New workflow instance

### `get_graph()`

```python
def get_graph(self) -> Graph
```

Get the underlying Graph object.

**Returns:**
- `Graph`: The underlying graph

## Properties

- `name` (str): Name of the workflow
- `validation_mode` (str): Current validation mode
- `deduplication` (bool): Whether deduplication is enabled
- `schema` (dict): Current schema configuration

## Examples

### Basic Usage

```python
from biocypher import create_workflow

# Create workflow
workflow = create_workflow("protein_network")

# Add nodes
workflow.add_node("TP53", "protein", name="TP53", function="tumor_suppressor")
workflow.add_node("BRAF", "protein", name="BRAF", function="kinase")

# Add edge
workflow.add_edge("interaction_1", "interaction", "TP53", "BRAF", confidence=0.8)

# Query
proteins = workflow.get_nodes("protein")
print(f"Found {len(proteins)} proteins")
```

### With Validation

```python
# Create workflow with validation
workflow = create_workflow(
    "validated_graph",
    validation_mode="strict",
    deduplication=True,
    schema={
        "protein": {
            "represented_as": "node",
            "properties": {"name": "str", "function": "str"}
        }
    }
)

# This will validate against schema
workflow.add_node("TP53", "protein", name="TP53", function="tumor_suppressor")
```

### Agentic Workflow

```python
# Maximum flexibility for agents
workflow = create_workflow(validation_mode="none")

# Agents can add any nodes/edges dynamically
for entity in agent_discovered_entities:
    workflow.add_node(entity.id, entity.type, **entity.properties)

# Convert to analysis format when needed
nx_graph = workflow.to_networkx()
```
