# NetworkX

When setting the `dbms` parameter in the `biocypher_config.yaml` to `networkx`,
the BioCypher Knowledge Graph is transformed into a [NetworkX
DiGraph](https://networkx.org/documentation/stable/reference/classes/digraph.html)
and then written to a pickle file.

## NetworkX settings

To overwrite the standard settings of NetworkX, add a `networkx` section to the
`biocypher_config.yaml` file.  At the moment there are no configuration options
supported/implemented.  Feel free to reach out and create issues or pull
requests if you need specific configuration options.

```{code-block} yaml
:caption: biocypher_config.yaml

networkx:
  ### NetworkX configuration ###
```

## Offline mode

### Running BioCypher

After running BioCypher with the ``offline`` parameter set to ``true`` and the
``dbms`` set to ``networkx``, the output folder contains:

- ``networkx_graph.pkl``: The pickle file containing with the BioCypher
Knowledge Graph as NetworkX DiGraph.

- ``import_networkx.py``: A Python script to load the created pickle file.

```{note}
If any of the files is missing make sure to run `bc.write_import_call()`.
```
