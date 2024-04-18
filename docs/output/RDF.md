# Output to RDF

In this section, we will learn how to use and implement the output to RDF using the `_RDFWriter` module.


## RDF settings

To write your output to RDF, you have to specify some RDF settings in the biocypher_config.yaml. Using `rdf_format`, you can choose to export to xml, turtle or any other format `rdflib` supports. The second configuration is the `rdf_namespaces` where you can specify which namespaces exist in your data. if e.g. your data contains SO (Sequence ontology) terms, like `SO:0000001`, it will convert the id to a working URI to allow referencing. Thus `SO:0000001` will be converted into `http://purl.obolibrary.org/obo/SO_0000001`.
When a node cannot be converted, it will use a default uri `https://biocypher.org/biocypher#<node_id>`.

```{code-block} yaml
:caption: biocypher_config.yaml

biocypher:
  strict_mode: true
  schema_config_path: config/schema_config.yaml
  dbms: rdf

### RDF configuration ###
rdf:
  rdf_format: turtle # choose: xml, n3, turtle, nt, pretty-xml, trix, trig, nquads, json-ld
  rdf_namespaces:
    so: http://purl.obolibrary.org/obo/SO_
    efo: http://www.ebi.ac.uk/efo/EFO_

```

## Output
The `_RDFWriter` will create a file for every node and relationship type you have specified.
