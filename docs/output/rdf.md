# RDF

In this section, we will learn how to use and implement the output to RDF using
the `_RDFWriter` module.

## RDF settings

To write your output to RDF, you have to specify some RDF settings in the
biocypher_config.yaml. Using `rdf_format`, you can choose to export to xml,
turtle or any other format `rdflib` supports. The second configuration is the
`rdf_namespaces`, where you can specify which namespaces exist in your data. If,
for instance, your data contain SO (Sequence ontology) terms such as
`SO:0000001`, IDs will be converted into valid URIs to allow referencing. Thus,
`SO:0000001` will be converted into `http://purl.obolibrary.org/obo/SO_0000001`.
When a node cannot be converted, a default URI will be used
(`https://biocypher.org/biocypher#<node_id>`). Running the pipeline, the
`_RDFWriter` will create a file for every node and relationship type you have
specified.

```{code-block} yaml
:caption: biocypher_config.yaml

biocypher:
  strict_mode: true
  schema_config_path: config/schema_config.yaml
  dbms: rdf

### RDF configuration ###
rdf:
  rdf_format: turtle
  # options: xml, n3, turtle, nt, pretty-xml, trix, trig, nquads, json-ld
  rdf_namespaces:
    so: http://purl.obolibrary.org/obo/SO_
    efo: http://www.ebi.ac.uk/efo/EFO_

```
