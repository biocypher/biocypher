# BioPathNet

In this section, we will learn how to use the output to BioPathNet compatible files using
the `_biopathnet` module.

In Biocypher, selecting 'biopathnet' output format will call the '_BioPathNetWriter' class and
write BioCypher's property graph into a set of BioPathNet input files.

The class writes one skg as a list of lines each containing a triple.
As BioPathNet is launched with the same entity_names and entity_types file,
appends information in the entity_types and entity_names files. This way, these files can
contain the information about all the entities from learning, validation and test graphs.

## BioPathNet settings

To write your output to BioPathNet input files, you have to specify some settings in the
`biocypher_config.yaml`.
Important parameters are:
- Configuration of the ontology (url and labal of the root node)
- `file_format` must be 'txt'
-  entity_types_file_stem: the name of the file in wich the entities names are stored
-  entity_names_file_stem: the name of the file in wich the types of each entity are stored
-  background_graph_file_stem: the name of the file containing the background regulatory graph
-  skg_file_stem: the name of the fila containing the main Semantic Knowledg Graph, on wich to learn
-  targeted_relation: If specified, the main SKG will be filtered so that it contains only relations with the
  corresponding signature. The other relations are stored in the background regulatory graph
-  include_properties: True if the properties of the BioCypher's graph should be included in the export.

```yaml title="biocypher_config.yaml"
biocypher:
  debug: false
  offline: true
  dbms: biopathnet

  #Ontology configuration
  head_ontology:
    url: {{ONTOLOGY_URL}}
    root_node: Biocypherroot

### BioPathNet configuration ###
biopathnet:
  file_format: txt
  entity_types_file_stem: entity_types
  entity_names_file_stem: entity_names
  background_graph_file_stem: brg
  skg_file_stem: skg
  targeted_relation: None
  include_properties: Trus
```
