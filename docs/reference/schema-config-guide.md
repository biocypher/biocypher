# Schema Configuration Reference

## Purpose:

## Convention for naming:

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

### `exclude_properties`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

### `inherit_properties`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

### `input_label`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

### `is_a`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

### `label_as_edge`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

### `preferred_id`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

### `properties`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

### `represented_as`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

### `source`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

### `synonym_for`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

### `target`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

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
