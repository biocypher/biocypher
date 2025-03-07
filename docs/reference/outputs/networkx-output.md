When setting the `dbms` parameter in the `biocypher_config.yaml` to `networkx`,
the BioCypher Knowledge Graph is transformed into a [NetworkX
DiGraph](https://networkx.org/documentation/stable/reference/classes/digraph.html).

## NetworkX settings

At the moment, we don't implement any specific configuration options for
NetworkX. Feel free to reach out and create issues or pull requests if you need
specific configuration options. They would be added to the configuration
similarly as for other outputs:

```yaml title="biocypher_config.yaml"

networkx:
  ### NetworkX configuration ###
```

## Offline mode

### Running BioCypher

After running BioCypher with the `offline` parameter set to `true` and the
`dbms` set to `networkx`, the output folder contains:

- `networkx_graph.pkl`: The pickle file containing with the BioCypher
Knowledge Graph as NetworkX DiGraph.

- `import_networkx.py`: A Python script to load the created pickle file.

!!! note "Note"
    If any of the files is missing make sure to run `bc.write_import_call()`.


## Online mode

After running BioCypher with the `offline` parameter set to `false` and the
`dbms` set to `networkx`, you can get the in-memory networkx representation of the
Knowledge Graph directly from BioCypher by calling the `get_kg()` function.

<!--
```python
from biocypher import BioCypher
bc = BioCypher()

def check_if_function_exists(module_name, function_name):
    if hasattr(module_name, function_name):
        print("Functions exists")
    else:
        print("Function does not exist")
check_if_function_exists(bc, "get_kg")
```

```python
Functions exists
```
-->

```python
# Initialize BioCypher
bc = BioCypher(
    biocypher_config_path="biocypher_config.yaml",
    schema_config_path="schema_config.yaml",
)

# Add nodes and edges
bc.add_nodes(nodes)
bc.add_edges(edges)

# Get the in-memory representation of the Knowledge Graph
in_memory_kg = bc.get_kg()
```
