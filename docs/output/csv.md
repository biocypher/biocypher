# CSV

When setting the `dbms` parameter in the `biocypher_config.yaml` to `csv`, the
BioCypher Knowledge Graph is written to CSV files.

## CSV settings

To overwrite the standard settings of the CSV writer, add a `csv` section to the
`biocypher_config.yaml` file. The following settings are possible:

```{code-block} yaml
:caption: biocypher_config.yaml

csv:
  ### CSV/Pandas configuration ###
  delimiter: ','  # The delimiter used in the CSV files. Default is ','.
```

## Offline mode

### Running BioCypher

After running BioCypher with the ``offline`` parameter set to ``true`` and the
``dbms`` set to ``csv``, the output folder contains:

- ``*.csv``: The CSV files containing the node/edge data.

- ``import_pandas_csv.csv``: A Python script to load the created CSV files into
Pandas DataFrames.
