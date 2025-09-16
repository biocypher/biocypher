# BioCypher Graph Class Guide

## Overview

The `Graph` class is the core data structure of the BioCypher Agent API, providing a unified representation for various types of graphs including simple graphs, directed graphs, weighted graphs, multigraphs, and hypergraphs. It's designed to be a pure Python implementation with no external dependencies, making it perfect for sandbox environments and LLM agent integration.

## Design Philosophy

### Core Principles

1. **Unified Representation**: Single class handles all graph types
2. **Pure Python**: No external dependencies for basic operations
3. **Type Safety**: Comprehensive type annotations with modern syntax
4. **Extensibility**: Easy to add new features and capabilities
5. **Performance**: Optimized for common operations
6. **Serialization**: Built-in JSON export/import

### Key Features

- **Multiple Graph Types**: Simple, directed, weighted, hypergraphs
- **Property Graphs**: Rich metadata on nodes and edges
- **Efficient Indexing**: Type-based and adjacency indexes
- **Path Finding**: BFS-based path discovery
- **Statistics**: Comprehensive graph analytics
- **Serialization**: JSON export/import for persistence

## Class Structure

### Core Classes

```python
from biocypher import Graph, Node, Edge, HyperEdge

# Main graph class
graph = Graph("my_graph", directed=True)

# Data structures
node = Node("id", "type", properties={"name": "value"})
edge = Edge("id", "type", "source", "target", properties={"weight": 0.8})
hyperedge = HyperEdge("id", "type", {"node1", "node2", "node3"}, properties={"function": "complex"})
```

### Edge Types Enum

```python
from biocypher import EdgeType

EdgeType.SIMPLE      # Undirected edges
EdgeType.DIRECTED    # Directed edges
EdgeType.WEIGHTED    # Weighted edges
EdgeType.HYPEREDGE   # Hypergraph edges
```

## Data Structures

### Node Class

```python
@dataclass
class Node:
    id: str                    # Unique identifier
    type: str                  # Node category/type
    properties: dict[str, Any] # Metadata dictionary
```

**Features:**

- Immutable ID and type
- Flexible property dictionary
- Validation in `__post_init__`
- Dictionary conversion methods

**Example:**
```python
node = Node("TP53", "protein", properties={
    "name": "TP53",
    "function": "tumor_suppressor",
    "uniprot_id": "P04637"
})
```

### Edge Class

```python
@dataclass
class Edge:
    id: str                    # Unique identifier
    type: str                  # Edge category/type
    source: str                # Source node ID
    target: str                # Target node ID
    properties: dict[str, Any] # Metadata dictionary
```

**Features:**

- Directed relationship representation
- Source and target validation
- Flexible property dictionary
- Dictionary conversion methods

**Example:**
```python
edge = Edge("interaction_1", "interaction", "TP53", "BRAF", properties={
    "confidence": 0.8,
    "evidence": "literature",
    "method": "co-immunoprecipitation"
})
```

### HyperEdge Class

```python
@dataclass
class HyperEdge:
    id: str                    # Unique identifier
    type: str                  # Edge category/type
    nodes: set[str]            # Set of connected node IDs
    properties: dict[str, Any] # Metadata dictionary
```

**Features:**
- Multi-node relationship representation
- Set-based node collection
- Minimum 2 nodes validation
- Dictionary conversion methods

**Example:**
```python
hyperedge = HyperEdge("complex_1", "protein_complex",
                     {"TP53", "MDM2", "CDKN1A"},
                     properties={
                         "function": "cell_cycle_control",
                         "complex_type": "regulatory"
                     })
```

## Graph Class Architecture

### Internal Data Structures

```python
class Graph:
    def __init__(self, name: str = "graph", directed: bool = True):
        # Core data structures
        self._nodes: dict[str, Node] = {}
        self._edges: dict[str, Edge] = {}
        self._hyperedges: dict[str, HyperEdge] = {}

        # Type indexes for efficient querying
        self._node_types: dict[str, set[str]] = defaultdict(set)
        self._edge_types: dict[str, set[str]] = defaultdict(set)
        self._hyperedge_types: dict[str, set[str]] = defaultdict(set)

        # Adjacency indexes for efficient traversal
        self._outgoing: dict[str, set[str]] = defaultdict(set)
        self._incoming: dict[str, set[str]] = defaultdict(set)

        # Statistics
        self._stats = {
            "nodes": 0,
            "edges": 0,
            "hyperedges": 0,
            "node_types": 0,
            "edge_types": 0,
            "hyperedge_types": 0
        }
```

### Indexing Strategy

The Graph class uses multiple indexes for efficient operations:

1. **Primary Indexes**: Direct access to nodes, edges, hyperedges by ID
2. **Type Indexes**: Fast filtering by node/edge type
3. **Adjacency Indexes**: Efficient neighbor and path finding
4. **Statistics**: Real-time graph metrics

## Core Operations

### Node Operations

#### Adding Nodes
```python
def add_node(self, node_id: str, node_type: str, properties: dict[str, Any] | None = None) -> bool:
    """Add a node to the graph.

    Args:
        node_id: Unique identifier for the node
        node_type: Type/category of the node
        properties: Optional properties dictionary

    Returns:
        bool: True if node was added, False if it already exists
    """
```

**Example:**
```python
graph = Graph("biomedical")
graph.add_node("TP53", "protein", name="TP53", function="tumor_suppressor")
graph.add_node("BRAF", "protein", name="BRAF", function="kinase")
```

#### Querying Nodes
```python
# Get specific node
node = graph.get_node("TP53")

# Get all nodes
all_nodes = graph.get_nodes()

# Get nodes by type
proteins = graph.get_nodes("protein")

# Get node IDs
protein_ids = graph.get_node_ids("protein")
```

#### Node Management
```python
# Check if node exists
if graph.has_node("TP53"):
    print("TP53 exists")

# Remove node (and connected edges)
graph.remove_node("TP53")
```

### Edge Operations

#### Adding Edges
```python
def add_edge(self, edge_id: str, edge_type: str, source: str, target: str,
             properties: dict[str, Any] | None = None) -> bool:
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
```

**Example:**
```python
graph.add_edge("TP53_BRAF", "interaction", "TP53", "BRAF", confidence=0.8)
graph.add_edge("BRAF_cancer", "causes", "BRAF", "cancer", evidence="strong")
```

#### Querying Edges
```python
# Get specific edge
edge = graph.get_edge("TP53_BRAF")

# Get all edges
all_edges = graph.get_edges()

# Get edges by type
interactions = graph.get_edges("interaction")

# Get edges between nodes
edges = graph.get_edges_between("TP53", "BRAF")
```

#### Edge Management
```python
# Check if edge exists
if graph.has_edge("TP53_BRAF"):
    print("Interaction exists")

# Remove edge
graph.remove_edge("TP53_BRAF")
```

### Hyperedge Operations

#### Adding Hyperedges
```python
def add_hyperedge(self, hyperedge_id: str, hyperedge_type: str, nodes: set[str],
                  properties: dict[str, Any] | None = None) -> bool:
    """Add a hyperedge to the graph.

    Args:
        hyperedge_id: Unique identifier for the hyperedge
        hyperedge_type: Type/category of the hyperedge
        nodes: Set of connected node IDs
        properties: Optional properties dictionary

    Returns:
        bool: True if hyperedge was added, False if it already exists
    """
```

**Example:**
```python
graph.add_hyperedge("apoptosis_complex", "protein_complex",
                   {"BCL2", "BAX", "CASP9", "CASP3"},
                   function="programmed_cell_death")
```

#### Querying Hyperedges
```python
# Get specific hyperedge
hyperedge = graph.get_hyperedge("apoptosis_complex")

# Get all hyperedges
all_hyperedges = graph.get_hyperedges()

# Get hyperedges by type
complexes = graph.get_hyperedges("protein_complex")
```

## Graph Traversal

### Neighbor Discovery
```python
def get_neighbors(self, node_id: str, direction: str = "both") -> set[str]:
    """Get neighboring nodes.

    Args:
        node_id: Node identifier
        direction: "in", "out", or "both"

    Returns:
        set[str]: Set of neighboring node IDs
    """
```

**Example:**
```python
# Get all neighbors
neighbors = graph.get_neighbors("TP53")

# Get outgoing neighbors only
outgoing = graph.get_neighbors("TP53", direction="out")

# Get incoming neighbors only
incoming = graph.get_neighbors("TP53", direction="in")
```

### Path Finding
```python
def find_paths(self, source: str, target: str, max_length: int = 3) -> list[list[Edge]]:
    """Find all paths between two nodes.

    Args:
        source: Source node ID
        target: Target node ID
        max_length: Maximum path length

    Returns:
        list[list[Edge]]: List of paths, each path is a list of edges
    """
```

**Example:**
```python
# Find paths between nodes
paths = graph.find_paths("TP53", "cancer", max_length=4)

for i, path in enumerate(paths):
    print(f"Path {i+1}:")
    for edge in path:
        print(f"  {edge.source} --[{edge.type}]--> {edge.target}")
```

### Connected Components
```python
def get_connected_edges(self, node_id: str, direction: str = "both") -> list[Edge]:
    """Get edges connected to a node.

    Args:
        node_id: Node identifier
        direction: "in", "out", or "both"

    Returns:
        list[Edge]: List of connected edges
    """
```

## Graph Analysis

### Statistics
```python
def get_statistics(self) -> dict[str, Any]:
    """Get comprehensive graph statistics.

    Returns:
        dict[str, Any]: Statistics including basic counts, type breakdowns, and connectivity
    """
```

**Example:**
```python
stats = graph.get_statistics()

print(f"Basic stats: {stats['basic']}")
print(f"Node types: {stats['node_types']}")
print(f"Edge types: {stats['edge_types']}")
print(f"Connectivity: {stats['connectivity']}")
```

**Statistics Structure:**
```python
{
    "basic": {
        "nodes": 10,
        "edges": 15,
        "hyperedges": 2,
        "node_types": 3,
        "edge_types": 4,
        "hyperedge_types": 1
    },
    "node_types": {
        "protein": 5,
        "disease": 3,
        "drug": 2
    },
    "edge_types": {
        "interaction": 8,
        "causes": 4,
        "treats": 3
    },
    "hyperedge_types": {
        "protein_complex": 2
    },
    "connectivity": {
        "isolated_nodes": 0,
        "connected_nodes": 10
    }
}
```

### Subgraph Extraction
```python
def get_subgraph(self, node_ids: set[str], include_edges: bool = True) -> 'Graph':
    """Extract a subgraph containing specified nodes.

    Args:
        node_ids: Set of node IDs to include
        include_edges: Whether to include edges between included nodes

    Returns:
        Graph: New graph containing the subgraph
    """
```

**Example:**
```python
# Extract subgraph around TP53
tp53_neighbors = graph.get_neighbors("TP53")
subgraph = graph.get_subgraph({"TP53"} | tp53_neighbors)
```

## Serialization

### JSON Export/Import
```python
def to_json(self) -> str:
    """Convert graph to JSON string."""

def from_json(self, json_str: str) -> None:
    """Load graph from JSON string."""

@classmethod
def from_json(cls, json_str: str) -> 'Graph':
    """Create graph from JSON string."""
```

**Example:**
```python
# Export to JSON
json_data = graph.to_json()
with open("graph.json", "w") as f:
    f.write(json_data)

# Import from JSON
new_graph = Graph.from_json(json_data)

# Or load into existing graph
graph.from_json(json_data)
```

### Dictionary Conversion
```python
def to_dict(self) -> dict[str, Any]:
    """Convert graph to dictionary representation."""

@classmethod
def from_dict(cls, data: dict[str, Any]) -> 'Graph':
    """Create graph from dictionary representation."""
```

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Add node | O(1) | Average case |
| Add edge | O(1) | Average case |
| Add hyperedge | O(k) | k = number of nodes in hyperedge |
| Get node | O(1) | Hash table lookup |
| Get edge | O(1) | Hash table lookup |
| Query by type | O(n) | n = number of items of that type |
| Get neighbors | O(deg(v)) | deg(v) = degree of node v |
| Path finding | O(V + E) | BFS-based |
| Serialization | O(n) | n = total number of nodes/edges |

### Memory Usage

- **Small graphs** (< 1K nodes): ~1-10 MB
- **Medium graphs** (1K-100K nodes): ~10-100 MB
- **Large graphs** (> 100K nodes): Consider external storage

### Optimization Features

1. **Hash-based Indexes**: O(1) node/edge lookup
2. **Type Indexes**: Fast filtering by type
3. **Adjacency Indexes**: Efficient neighbor discovery
4. **Lazy Statistics**: Computed on-demand
5. **Memory-efficient**: No redundant data storage

## Advanced Features

### Custom Node/Edge Types
```python
# Define custom types
graph.add_node("pathway_1", "biological_pathway",
               name="Apoptosis",
               pathway_type="cell_death")

graph.add_edge("regulates_1", "regulates",
              "TP53", "apoptosis_pathway",
              regulation_type="activation")
```

### Complex Properties
```python
# Rich metadata
graph.add_node("TP53", "protein",
               name="TP53",
               function="tumor_suppressor",
               uniprot_id="P04637",
               molecular_weight=43653,
               amino_acid_count=393,
               confidence=0.95,
               sources=["UniProt", "PubMed"],
               last_updated="2024-01-15")
```

### Hypergraph Applications
```python
# Protein complexes
graph.add_hyperedge("TP53_complex", "protein_complex",
                   {"TP53", "MDM2", "CDKN1A"},
                   function="cell_cycle_control",
                   complex_type="regulatory")

# Biological pathways
graph.add_hyperedge("apoptosis_pathway", "biological_pathway",
                   {"BCL2", "BAX", "CASP9", "CASP3", "CASP7"},
                   pathway_type="cell_death",
                   regulation="extrinsic_and_intrinsic")

# Drug targets
graph.add_hyperedge("cancer_treatment", "drug_target_set",
                   {"TP53", "BRAF", "EGFR", "PIK3CA"},
                   drug_class="targeted_therapy",
                   cancer_type="multiple")
```

## Best Practices

### 1. Use Descriptive IDs
```python
# Good
graph.add_node("TP53_protein", "protein", name="TP53")
graph.add_edge("TP53_regulates_BRAF", "regulates", "TP53", "BRAF")

# Avoid
graph.add_node("n1", "protein", name="TP53")
graph.add_edge("e1", "regulates", "n1", "n2")
```

### 2. Leverage Type System
```python
# Use consistent types
graph.add_node("protein_1", "protein", ...)
graph.add_node("disease_1", "disease", ...)
graph.add_edge("interaction_1", "interaction", ...)
```

### 3. Use Properties for Metadata
```python
# Include relevant properties
graph.add_node("TP53", "protein",
               name="TP53",
               function="tumor_suppressor",
               confidence=0.95,
               sources=["UniProt", "PubMed"])
```

### 4. Validate Data Integrity
```python
# Check for required nodes before adding edges
if not graph.has_node("TP53"):
    graph.add_node("TP53", "protein", name="TP53")

graph.add_edge("interaction_1", "interaction", "TP53", "BRAF")
```

### 5. Use Hyperedges for Complex Relationships
```python
# For multi-node relationships
graph.add_hyperedge("complex_1", "protein_complex",
                   {"protein_1", "protein_2", "protein_3"},
                   function="cell_cycle_control")
```

## Integration with BioCypher Agent

The Graph class is the underlying data structure for the `BioCypherWorkflow`:

```python
from biocypher import create_workflow

# Create agent (uses Graph internally)
agent = create_workflow("my_knowledge")

# Access underlying graph
graph = agent.get_graph()

# Use graph methods directly
stats = graph.get_statistics()
paths = graph.find_paths("node1", "node2")
```

## Future Enhancements

The Graph class is designed to be extensible. Future enhancements may include
(if reasonable to implement and not covered by other packages already):

1. **Schema Validation and Persistence**:

    - Agent-in-the-loop schema validation of entities
    - Automatic rollback of inconsistent operations
    - Namespace management for alignment with ontologies

1. **Connectivity with Pre-existing Databases**:

    - Connect to and extract consistent subgraphs from existing databases (such as Open Targets)
    - Automatically adapt to external schema configurations
    - Encode meta-level workflows as a reasoning graph

1. **Query Language**:

    - GraphQL-like querying
    - Pattern matching
    - Complex graph queries

1. **Visualization**:

    - Built-in graph plotting
    - Interactive visualizations
    - Export to visualization formats

1. **Machine Learning**:

    - Connect graph representation to ML / DL libraries
    - Node embeddings
    - Graph neural networks
    - Graph-based ML algorithms

1. **Performance Optimizations**:

    - Parallel processing
    - Memory-mapped storage
    - Distributed graph operations

## Conclusion

The Graph class provides a powerful, flexible foundation for knowledge graph representation. Its unified design supports various graph types while maintaining simplicity and performance. The pure Python implementation makes it ideal for sandbox environments and LLM agent integration, while the comprehensive API enables sophisticated graph operations and analysis.

Key strengths:

- **Unified Design**: Single class for all graph types
- **Pure Python**: No external dependencies
- **Type Safety**: Modern type annotations
- **Performance**: Optimized for common operations
- **Extensibility**: Easy to add new features
- **Serialization**: Built-in persistence

The Graph class serves as the core data structure for the BioCypher Agent API, providing the foundation for LLM agent knowledge graph construction and reasoning.
