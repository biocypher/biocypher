# Schema Configuration Reference

## Purpose:

The schema file defines the structure of a BioCypher knowledge graph, specifying which entities and relationships are included and how they are represented. It ensures alignment with biomedical ontologies like the [Biolink model](https://biolink.github.io/biolink-model/), serving as a blueprint for constructing a domain-specific knowledge graph.

## Convention for naming:

- Entities in the `schema_config.yaml` file should be represented in **lower sentence case** (e.g., `small molecule`), similar to the internal representation in Biolink.
- Class names, in file names, and property graph labels they are represented in **PascalCase** (e.g., `SmallMolecule`).


## Skeleton:

```yaml
#-------------------------------------------------------------------
#---- Title: Schema Configuration file example
#---- Authors: <author 1>, <author 2>
#---- Description: Schema to load information related to proteins, and
#                  and their interactions.
#
#-------------------------------------------------------------------

#-------------------------------------------------------------------
#-------------------------      NODES      -------------------------
#-------------------------------------------------------------------
#=========    PARENT NODES
protein:
  represented_as: node
  preferred_id: [uniprot, entrez]
  input_label: [uniprot_protein, entrez_protein]
  properties:
    sequence: str
    description: str
    taxon: str
    mass: int

#=========    INHERITED NODES
protein isoform:
  is_a: protein
  inherit_properties: true
  represented_as: node
  preferred_id: uniprot
  input_label: uniprot_isoform

#-------------------------------------------------------------------
#------------------      RELATIONSHIPS (EDGES)     -----------------
#-------------------------------------------------------------------
#=========    PARENT EDGES
protein protein interaction:
  is_a: pairwise molecular interaction
  represented_as: edge
  preferred_id: intact
  input_label: interacts_with
  properties:
      method: str
      source: str

#=========    INHERITED EDGES


#=========    EDGES AS NODES
ligand receptor interaction:
  is_a: association
  represented_as: node
  properties:
    directed: true  # Preserves directionality: creates IS_SOURCE_OF and IS_TARGET_OF edges

#--------------------------------------------------------------------
#---- Dictionary of custom keywords: add additional keywords if you
#     need it. Please document each new keyword as in the following
#     template. DO NOT DELETE the hash symbol (#) in each line.

# <keyword's name>
#    Description:
#    Possible values:
#        - possible value 1 [*datatype*]
#        - possible value 2 [*datatype*]
#

```

## Fields reference:

### `directed`
- **Description:** For relationships (edges or reified as nodes), specifies whether the relationship is directed. If `true`, directionality is preserved and two edge types are created: `IS_SOURCE_OF` and `IS_TARGET_OF`. If `false` or omitted, both edges are labeled as `IS_PART_OF`, and directionality is not preserved.
- **Possible values:**
  - `true`
  - `false`

### `exclude_properties`
- **Description:** Specifies properties that should be excluded from the current entity or relation, preventing them from being inherited or used.
- **Possible values:**
  - A list of property names to be excluded, such as `[category, references]`.

### `inherit_properties`
- **Description:**  Defines whether and which properties should be inherited from a parent entity. This applies when using `is_a`.
- **Possible values:**
  - `true`
  - `false`

### `input_label`
- **Description:** A human-readable label used when referring to this entity in a UI or input form.
- **Possible values:**
  - A string, such as `Gene Symbol`, `TF Category`, or `Regulation Type`.

### `is_a`
- **Description:** Defines a hierarchical relationship by specifying the parent class from which the current entity inherits.
- **Possible values:**
  - A reference to another entity, such as `gene` or `pairwise gene to gene interaction`.

### `label_as_edge`
- **Description:** Indicates the label to be used in the output graph if the entity is represented as an edge. Used to override the default name (PascalCase conversion of the class). Typical use case: adhere to labelled property graph naming scheme (uppercase verbs). Only applied to edges.
- **Possible values:**
  - A string describing the edge label, for instance, `PERTURBED_IN` or `TARGETS`.

### `preferred_id`
- **Description:** Specifies the primary identifier used for this entity, typically referencing a standardized database ID.
- **Possible values:**
  - A string referring to a standardized identifier, such as `hgnc.symbol`.

### `properties`
- **Description:** Defines attributes associated with an entity or relationship.
- **Possible values:**
  - String: `str` (or `string`)
  - Integer: `int` (or `integer`, `long`).
  - String: `float` (or `double`, `dbl`).
  - Boolean: `bool` (or `boolean`).
  - Arrays of any of these types (indicated by square brackets, e.g. `string[]`).

### `represented_as`
- **Description:** Specifies whether the entity should be represented as a node or an edge in a graph-based structure. An entity can be represented as an edge only if source and target IDs are provided in the input data stream. Conversely, relationships can be represented as either a node or an edge, depending on the desired output.
- **Possible values:**
  - `node`
  - `edge`

### `source`
- **Description:** [optional] For relationships (edges), defines the starting entity in the relationship.
- **Possible values:**
  - A reference to an entity, such as `transcription factor`.

### `synonym_for`
- **Description:** Indicates that this entity or property serves as a synonym for another term or entity.
- **Possible values:**
  - A string or list of strings representing alternative names, such as `[TF, transcription regulator]`.

### `target`
- **Description:** [optional] For relationships (edges), defines the destination entity in the relationship.
- **Possible values:**
  - A reference to an entity, such as `gene`.

## Add custom fields
!!! tip "Tip"
    Do not forget to document your custom keywords at the end of the schema config file, this is especially useful if you share your schema configuration file with others. They will understand what is the purpose of those new keywords.

You can use other keywords for local functionalities without interfering with the default ones. For instance, a particular user has added the `db_collection_name` field for its own purposes.

```yaml title="Example: schema configuration with a custom keyword" hl_lines="6"
#...
protein:
  represented_as: node
  preferred_id: uniprot
  input_label: protein
  db_collection_name: proteins
  properties:
    name: str
    score: float
    taxon: int
    genes: str[]
#...
```
