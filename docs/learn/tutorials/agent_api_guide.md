# BioCypher Agent API Guide

## Overview

The BioCypher Agent API provides a streamlined interface for LLM agents to create and manage knowledge graphs. It was designed to address the complexity of the original BioCypher framework while maintaining its powerful capabilities for biomedical knowledge representation.

## Design Philosophy

### Core Principles

1. **Simplicity First**: Start with zero configuration and add complexity only when needed
2. **Unified Representation**: Single graph representation that works for all use cases
3. **Direct Property Assignment**: Use `**kwargs` for immediate property assignment
4. **Pure Python**: No external dependencies for basic operations
5. **Progressive Complexity**: Simple initialization with optional advanced features

### Key Innovations

- **Custom Graph Class**: Built-in unified graph representation supporting simple, directed, weighted, and hypergraphs
- **Zero Configuration**: `create_workflow()` for immediate use
- **Direct Properties**: `add_node("id", "type", name="value", confidence=0.8)`
- **Built-in Serialization**: JSON export/import for persistence
- **Optional Schema**: Schema validation when needed, not required

### Key Limitations (vs. Legacy BioCypher)

⚠️ **Important for Legacy Users**: The Agent API prioritizes simplicity over comprehensive ETL capabilities:

- **Limited Output Formats**: Only JSON, NetworkX, Pandas (vs. 15+ formats)
- **No Database Integration**: No Neo4j, PostgreSQL, or other database connectivity
- **Basic Ontology Support**: Simple URL references only (no complex mapping)
- **Memory-Bound**: In-memory only, not suitable for large datasets (>100K nodes)
- **Simplified Validation**: Basic property checking (no complex inheritance)
- **No Batch Processing**: No streaming or batch processing capabilities
- **No Data Source Integration**: No built-in adapters for external data sources

**Use Legacy BioCypher for**: Large-scale ETL pipelines, database integration, complex ontologies, production systems, or batch processing of large datasets.

## API Reference

### Core Classes

#### `BioCypherWorkflow`

The main interface for LLM agents to interact with knowledge graphs.

```python
from biocypher import create_workflow

# Simple initialization
kg = create_workflow("my_knowledge")

# With schema
kg = create_workflow("my_knowledge", schema_file="schema.yaml")

# With ontology
kg = create_workflow("my_knowledge", head_ontology_url="https://biolink.github.io/biolink-model/")
```

#### `Graph`

The unified graph representation supporting various graph types.

```python
from biocypher import Graph

graph = Graph("my_graph", directed=True)
```

#### `Node`, `Edge`, `HyperEdge`

Core data structures for graph elements.

```python
from biocypher import Node, Edge, HyperEdge

node = Node("protein_1", "protein", properties={"name": "TP53"})
edge = Edge("interaction_1", "interaction", "protein_1", "protein_2", properties={"confidence": 0.8})
hyperedge = HyperEdge("complex_1", "protein_complex", {"protein_1", "protein_2", "protein_3"})
```

### Core Methods

#### Node Operations

```python
# Add nodes with properties
kg.add_node("protein_1", "protein", name="TP53", function="tumor_suppressor")
kg.add_node("disease_1", "disease", name="Cancer", description="Uncontrolled cell growth")

# Query nodes
proteins = kg.query_nodes("protein")
all_nodes = kg.query_nodes()

# Get specific node
node = kg.get_node("protein_1")
```

#### Edge Operations

```python
# Add edges with properties
kg.add_edge("interaction_1", "interaction", "protein_1", "protein_2", confidence=0.8)
kg.add_edge("causes_1", "causes", "protein_1", "disease_1", evidence="strong")

# Query edges
interactions = kg.query_edges("interaction")
all_edges = kg.query_edges()

# Get edges between nodes
edges = kg.get_edges_between("protein_1", "protein_2")
```

#### Hyperedge Operations

```python
# Add hyperedges for complex relationships
kg.add_hyperedge("complex_1", "protein_complex", {"protein_1", "protein_2", "protein_3"}, function="cell_cycle_control")

# Query hyperedges
complexes = kg.query_hyperedges("protein_complex")
```

#### Graph Analysis

```python
# Find paths between nodes
paths = kg.find_paths("protein_1", "disease_1", max_length=3)

# Get neighbors
neighbors = kg.get_neighbors("protein_1")

# Get statistics
stats = kg.get_statistics()
print(f"Nodes: {stats['basic']['nodes']}, Edges: {stats['basic']['edges']}")
```

#### Serialization

```python
# Export to JSON
json_data = kg.to_json()
kg.save("knowledge_graph.json")

# Import from JSON
new_kg = create_workflow("restored")
new_kg.from_json(json_data)
new_kg.load("knowledge_graph.json")
```

#### Compatibility Wrappers

```python
# Convert to NetworkX for analysis
nx_graph = kg.to_networkx()

# Use NetworkX algorithms
import networkx as nx
centrality = nx.degree_centrality(nx_graph)
print(f"Most central node: {max(centrality, key=centrality.get)}")

# Convert to Pandas DataFrames
nodes_df, edges_df = kg.to_pandas()

# Analyze with Pandas
print("Node types distribution:")
print(nodes_df['type'].value_counts())

print("Edge types distribution:")
print(edges_df['type'].value_counts())
```

## Getting Started

### Basic Workflow Creation

```python
from biocypher import create_workflow

# Create a simple workflow
workflow = create_workflow("my_graph")

# Add nodes
workflow.add_node("protein_1", "protein", name="TP53", function="tumor_suppressor")
workflow.add_node("protein_2", "protein", name="BRAF", function="kinase")

# Add edges
workflow.add_edge("interaction_1", "interaction", "protein_1", "protein_2", confidence=0.8)

# Check the graph
print(f"Graph has {len(workflow)} nodes")
```

### Validation Modes

The new API provides three validation modes for different use cases:

#### 1. "none" Mode (Default)
Maximum flexibility for agents and prototyping:

```python
# No validation overhead
workflow = create_workflow("agent_graph", validation_mode="none")

# Agents can add any nodes/edges dynamically
workflow.add_node("entity_1", "unknown_type", any_property="value")
workflow.add_node("entity_2", "custom_type", dynamic_data=123)
```

#### 2. "warn" Mode
Logs warnings but continues processing:

```python
workflow = create_workflow("debug_graph", validation_mode="warn", deduplication=True)

# This will warn about duplicates but continue
workflow.add_node("protein_1", "protein", name="TP53")
workflow.add_node("protein_1", "protein", name="TP53")  # Warning logged
```

#### 3. "strict" Mode
Enforces validation and fails fast:

```python
workflow = create_workflow("production_graph", validation_mode="strict", deduplication=True)

# This will raise an error for duplicates
workflow.add_node("protein_1", "protein", name="TP53")
# workflow.add_node("protein_1", "protein", name="TP53")  # Would raise ValueError
```

## Usage Examples

### Example 1: Basic Knowledge Graph

```python
from biocypher import create_workflow

# Create knowledge graph
kg = create_workflow("biomedical_knowledge")

# Add proteins
kg.add_node("TP53", "protein", name="TP53", function="tumor_suppressor")
kg.add_node("BRAF", "protein", name="BRAF", function="kinase")

# Add diseases
kg.add_node("melanoma", "disease", name="Melanoma", description="Skin cancer")

# Add interactions
kg.add_edge("TP53_BRAF", "interaction", "TP53", "BRAF", confidence=0.8)
kg.add_edge("BRAF_melanoma", "causes", "BRAF", "melanoma", evidence="strong")

# Query
proteins = kg.query_nodes("protein")
paths = kg.find_paths("TP53", "melanoma")
```

### Example 2: Reasoning Process Logging

```python
# Create reasoning graph
reasoning = create_workflow("reasoning_process")

# Log observation
reasoning.add_node("obs_1", "observation",
                  description="TP53 is frequently mutated in cancer",
                  source="literature")

# Log inference
reasoning.add_node("inf_1", "inference",
                  description="TP53 mutations likely contribute to cancer development",
                  confidence=0.9)

# Connect reasoning steps
reasoning.add_edge("obs_to_inf", "supports", "obs_1", "inf_1", strength=0.8)

# Export reasoning process
reasoning.save("reasoning_process.json")
```

### Example 3: Schema Validation

```python
# Define schema
schema = {
    "protein": {
        "represented_as": "node",
        "properties": {
            "name": "str",
            "function": "str",
            "uniprot_id": "str"
        }
    },
    "interaction": {
        "represented_as": "edge",
        "source": "protein",
        "target": "protein",
        "properties": {
            "confidence": "float",
            "evidence": "str"
        }
    }
}

# Create workflow with schema validation
workflow = create_workflow("validated_graph", schema=schema, validation_mode="strict")

# Valid node (passes validation)
workflow.add_node("TP53", "protein", name="TP53", function="tumor_suppressor", uniprot_id="P04637")

# Invalid node (fails validation in strict mode)
# workflow.add_node("BRAF", "protein", name=123)  # Wrong type for name
# workflow.add_node("MDM2", "protein", name="MDM2")  # Missing required function
```

### Example 4: Complex Relationships with Hypergraphs

```python
# Create protein complex knowledge graph
complexes = create_workflow("protein_complexes")

# Add proteins
complexes.add_node("TP53", "protein", name="TP53")
complexes.add_node("MDM2", "protein", name="MDM2")
complexes.add_node("CDKN1A", "protein", name="CDKN1A")

# Add protein complex as hyperedge
complexes.add_hyperedge("TP53_MDM2_complex", "protein_complex",
                       {"TP53", "MDM2"}, function="protein_degradation")

complexes.add_hyperedge("TP53_CDKN1A_complex", "protein_complex",
                       {"TP53", "CDKN1A"}, function="cell_cycle_control")

# Query complexes
protein_complexes = complexes.query_hyperedges("protein_complex")
```

### Example 5: Agentic Workflow Integration

```python
# Create workflow optimized for agents
workflow = create_workflow("agent_graph", validation_mode="none")

# Agent discovers entities dynamically
discovered_entities = [
    {"id": "entity_1", "type": "protein", "name": "TP53", "function": "tumor_suppressor"},
    {"id": "entity_2", "type": "protein", "name": "BRAF", "function": "kinase"},
    {"id": "entity_3", "type": "disease", "name": "Cancer", "description": "Uncontrolled growth"}
]

# Add entities dynamically
for entity in discovered_entities:
    workflow.add_node(entity["id"], entity["type"], **{k: v for k, v in entity.items() if k not in ["id", "type"]})

# Agent discovers relationships
discovered_relationships = [
    {"id": "rel_1", "type": "interaction", "source": "entity_1", "target": "entity_2", "confidence": 0.8},
    {"id": "rel_2", "type": "causes", "source": "entity_2", "target": "entity_3", "evidence": "strong"}
]

# Add relationships dynamically
for rel in discovered_relationships:
    workflow.add_edge(rel["id"], rel["type"], rel["source"], rel["target"],
                     **{k: v for k, v in rel.items() if k not in ["id", "type", "source", "target"]})

# Convert to analysis format when needed
nx_graph = workflow.to_networkx()
```

## Comparison with Original BioCypher

### Original BioCypher Approach

The original BioCypher framework was designed for large-scale biomedical knowledge graph construction with these characteristics:

#### Complexity
```python
# Complex initialization
from biocypher import BioCypher

bc = BioCypher(
    dbms="neo4j",
    offline=False,
    strict_mode=True,
    biocypher_config_path="biocypher_config.yaml",
    schema_config_path="schema_config.yaml",
    head_ontology={"url": "https://biolink.github.io/biolink-model/", "root_node": "named thing"}
)

# Complex data addition
bc.add_nodes([
    ("protein_1", "protein", {"name": "TP53", "function": "tumor_suppressor"})
])

bc.add_edges([
    ("interaction_1", "interaction", "protein_1", "protein_2", {"confidence": 0.8})
])
```

#### Multiple Backends
- NetworkX for in-memory graphs
- Pandas for tabular data
- Neo4j for graph databases
- CSV for file output
- Each with different APIs and capabilities

#### Schema Requirements
```yaml
# schema_config.yaml
protein:
  represented_as: node
  preferred_id: uniprot
  input_label: protein
  properties:
    name: str
    function: str

interaction:
  represented_as: edge
  preferred_id: interaction_id
  input_label: interaction
  source: protein
  target: protein
  properties:
    confidence: float
```

#### Translation Layers
- Complex ontology mapping
- Schema validation
- Translation between user terms and Biolink model
- Multiple format conversions

### New Agent API Approach

The new API simplifies this dramatically:

#### Simple Initialization
```python
from biocypher import create_workflow

# Zero configuration
kg = create_workflow("my_knowledge")

# Optional schema
kg = create_workflow("my_knowledge", schema_file="schema.yaml")
```

#### Direct Property Assignment
```python
# Direct properties with **kwargs
kg.add_node("protein_1", "protein", name="TP53", function="tumor_suppressor")
kg.add_edge("interaction_1", "interaction", "protein_1", "protein_2", confidence=0.8)
```

#### Unified Representation
```python
# Single graph class handles all types
graph = kg.get_graph()
print(f"Nodes: {len(graph)}")
print(f"Statistics: {graph.get_statistics()}")
```

#### Built-in Serialization
```python
# JSON export/import
kg.save("knowledge.json")
new_kg = create_workflow("restored")
new_kg.load("knowledge.json")
```

## Key Differences

| Aspect | Original BioCypher | New Agent API |
|--------|-------------------|---------------|
| **Initialization** | Complex with many parameters | `create_workflow()` |
| **Data Addition** | Tuple-based with dictionaries | Direct `**kwargs` |
| **Backends** | Multiple (NetworkX, Pandas, Neo4j, CSV) | Single unified Graph |
| **Schema** | Required YAML configuration | Optional |
| **Dependencies** | NetworkX, Pandas, PyYAML, etc. | Pure Python (basic) |
| **Serialization** | Format-specific writers | Built-in JSON |
| **Query Interface** | Backend-specific APIs | Unified interface |
| **Hypergraphs** | Not supported | Built-in support |
| **Learning Curve** | Steep | Minimal |

## Use Cases

### When to Use the New Agent API

1. **LLM Agent Integration**: Perfect for agents that need to build knowledge graphs during reasoning
2. **Prototyping**: Quick iteration and experimentation
3. **Small to Medium Graphs**: Up to thousands of nodes/edges
4. **Reasoning Process Logging**: Track agent reasoning steps
5. **Educational**: Teaching knowledge graph concepts
6. **Sandbox Environments**: No external dependencies

### When to Use Original BioCypher

1. **Large-scale Data Integration**: Millions of nodes/edges
2. **Production Systems**: Enterprise-grade reliability
3. **Complex Ontology Mapping**: Advanced Biolink model integration
4. **Multiple Output Formats**: Need for various database backends
5. **Schema-driven Development**: Strict validation requirements

## Migration Guide

### From Original BioCypher

```python
# Old way
from biocypher import BioCypher
bc = BioCypher(dbms="networkx", offline=True)
bc.add_nodes([("node_1", "protein", {"name": "TP53"})])

# New way
from biocypher import create_workflow
kg = create_workflow("my_graph")
kg.add_node("node_1", "protein", name="TP53")
```

### From NetworkX

```python
# Old way
import networkx as nx
G = nx.DiGraph()
G.add_node("node_1", type="protein", name="TP53")

# New way
from biocypher import create_workflow
kg = create_workflow("my_graph")
kg.add_node("node_1", "protein", name="TP53")
```

## Performance Characteristics

### Memory Usage
- **Small graphs** (< 1K nodes): Minimal memory footprint
- **Medium graphs** (1K-100K nodes): Efficient in-memory representation
- **Large graphs** (> 100K nodes): Consider original BioCypher for persistence

### Speed
- **Node/Edge addition**: O(1) average case
- **Query operations**: O(n) for type-based queries
- **Path finding**: O(V + E) for BFS-based algorithms
- **Serialization**: O(n) for JSON export

## Best Practices

### 1. Use Descriptive IDs
```python
# Good
kg.add_node("TP53_protein", "protein", name="TP53")

# Avoid
kg.add_node("n1", "protein", name="TP53")
```

### 2. Leverage Type System
```python
# Use consistent types
kg.add_node("protein_1", "protein", ...)
kg.add_node("disease_1", "disease", ...)
kg.add_edge("interaction_1", "interaction", ...)
```

### 3. Use Properties for Metadata
```python
# Include relevant properties
kg.add_node("TP53", "protein",
           name="TP53",
           function="tumor_suppressor",
           uniprot_id="P04637",
           confidence=0.95)
```

### 4. Export for Persistence
```python
# Save your work
kg.save("knowledge_graph.json")

# Load when needed
kg.load("knowledge_graph.json")
```

### 5. Use Hypergraphs for Complex Relationships
```python
# For protein complexes, pathways, etc.
kg.add_hyperedge("apoptosis_pathway", "pathway",
                {"BCL2", "BAX", "CASP9", "CASP3"},
                function="programmed_cell_death")
```

## Limitations and Trade-offs

While the Agent API provides significant advantages for LLM agent workflows, it comes with important limitations compared to the legacy BioCypher ETL pipeline:

### Current Limitations

- **Limited Output Formats**: Only JSON, NetworkX, and Pandas (vs. 15+ formats in legacy)
- **No Database Integration**: No direct Neo4j, PostgreSQL, or other database connectivity
- **Basic Ontology Support**: Simple URL references only (no complex ontology mapping)
- **Memory-Bound**: In-memory processing only, not suitable for large datasets (>100K nodes)
- **Simplified Validation**: Basic property type checking (no complex inheritance validation)
- **No Batch Processing**: No streaming or batch processing capabilities
- **Limited Metadata**: No automatic provenance tracking or metadata injection
- **No Data Source Integration**: No built-in adapters for external data sources

### When to Use Legacy BioCypher Instead

Use the original BioCypher framework for:
- **Large-scale ETL pipelines** (>100K nodes)
- **Database integration** (Neo4j, PostgreSQL, etc.)
- **Complex ontology requirements**
- **Production systems** requiring robust validation
- **Batch processing** of large datasets
- **Multiple output formats**
- **Provenance tracking** and metadata management

### Migration Path

The limitations above will be addressed in future phases:

- **Phase 2**: Enhanced ontology support, batch processing, more output formats
- **Phase 3**: Advanced validation, metadata handling, data source integration
- **Phase 4**: Unified interface with full legacy compatibility

## Future Enhancements

The Agent API is designed to be extensible. Future enhancements may include:

1. **Advanced Query Language**: GraphQL-like querying
2. **Visualization Support**: Built-in graph visualization
3. **Machine Learning Integration**: Node embeddings, graph neural networks
4. **Real-time Collaboration**: Multi-agent graph construction
5. **Advanced Analytics**: Centrality measures, community detection
6. **Database Backends**: Optional Neo4j, PostgreSQL integration

## Conclusion

The BioCypher Agent API represents a significant simplification of knowledge graph creation while maintaining the power and flexibility needed for LLM agent integration. It provides a clean, intuitive interface that reduces the cognitive load on developers while enabling sophisticated knowledge representation capabilities.

The API is particularly well-suited for:

- **LLM Agent Integration**: Seamless knowledge graph construction during reasoning
- **Educational Use**: Teaching knowledge graph concepts
- **Prototyping**: Rapid iteration and experimentation
- **Reasoning Process Logging**: Tracking agent decision-making
- **Small to Medium Datasets**: Interactive exploration and analysis
- **Research and Development**: Flexible experimentation with graph structures

However, it's important to understand the trade-offs. For large-scale production systems, complex ontology requirements, database integration, or batch processing of large datasets, the original BioCypher framework remains the appropriate choice. The Agent API is designed for agentic workflows and interactive use cases where simplicity and flexibility are prioritized over comprehensive ETL capabilities.
