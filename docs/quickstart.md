# Quickstart

::::{grid} 2
:gutter: 2

:::{grid-item-card} Already familiar? Here's a template:
:link: https://github.com/biocypher/project-template
:text-align: center
{octicon}`mark-github;3em` {octicon}`repo;3em` {octicon}`play;3em` {octicon}`container;3em`
:::

:::{grid-item-card} New to BioCypher? Follow the tutorial:
:link: tutorial
:link-type: ref
:text-align: center
{octicon}`package;3em` {octicon}`question;3em` {octicon}`checklist;3em` {octicon}`light-bulb;3em`
:::

::::

```{note}
If you already know how BioCypher works, we provide here a quickstart into the
knowledge graph build process. We provide a template repository on GitHub, which
you can use to get started with your own project.  You can get it
[here](https://github.com/biocypher/project-template).  To set up a new
project, simply follow the instructions in the README.

If you are new to BioCypher and would like a step-by-step introduction to the
package, please follow the [tutorial](tutorial).
```

The BioCypher workflow of creating your own knowledge graph consists of two
components:

1. the [host module adapter](qs_host-module-adapter), a python
   program, and
2. the [schema configuration file](qs_schema-config), a YAML file.

The adapter serves as a data interface between the source and BioCypher,
piping the "raw" data into BioCypher for the creation of the property
graph, while the schema configuration tells BioCypher how the graph
should be structured, detailing the names of constituents and how they
should be connected.

(qs_host-module-adapter)=
## The host module adapter

BioCypher follows a modular approach to data inputs; to create a knowledge
graph, we use at least one adapter module that provides a data stream to build
the graph from. Examples for current adapters can be found on the [GitHub
project adapter view](https://github.com/orgs/biocypher/projects/3/views/2).
Adapters can ingest data from many different input sources, including Python
modules as in the [CROssBAR
adapter](https://github.com/HUBioDataLab/CROssBAR-BioCypher-Migration) (which
uses the OmniPath backend software, PyPath, for downloading and caching data),
advanced file management formats such as Parquet as in the [Open Targets
adapter](https://github.com/biocypher/open-targets), or simple CSV files as in
the [Dependency Map adapter](https://github.com/biocypher/dependency-map).

The recommended way of interacting with BioCypher is via the
{py:class}``biocypher._driver.Driver`` class. It can be called either starting
in "offline mode" using `offline = True`, i.e., without connection to a running
Neo4j instance, or by providing authentication details via arguments or
configuration file:

```{code-block} python
import biocypher
d = biocypher.Driver(
  offline = False,
  db_uri = "bolt://localhost:7687",
  db_user = "neo4j",
  db_passwd = "password",
)
```

```{note}
We use the APOC library for Neo4j, which is not included automatically, but
needs to be installed as a plugin to the DMBS. For more information, please
refer to the [APOC documentation](https://neo4j.com/labs/apoc/).
```

```{hint}
The settings for the BioCypher driver can also be specified in a configuration
file. For more details, please refer to the [Setup instructions](config).
```

The main function of the adapter is to pass data into BioCypher, usually
as some form of iterable (commonly a list or generator of items). As a
minimal example, we load a list of proteins with identifiers, trivial
names, and molecular masses from a (fictional) CSV:

```{code-block} python
# read into data frame
with open("file.csv", "r") as f:
  proteins = pd.read_csv(f)

# yield proteins from data frame
def node_generator():
  for p in proteins:
    _id = p["uniprot_id"]
    _type = "protein"
    _props = {
      "name": p["trivial_name"]
      "mm": p["molecular_mass"]
    }

    yield (_id, _type, _props)

# write biocypher nodes
d.write_nodes(node_generator())
```

For nodes, BioCypher expects a tuple containing three entries; the preferred
identifier of the node, the type of entity, and a dictionary containing all
other properties (can be empty). What BioCypher does with the received
information is determined largely by the schema configuration detailed below.

For advanced usage, the type of node or edge can be determined
programatically. Properties do not need to be explicitly called one by
one; they can be passed in as a complete dictionary of all entries and
filtered inside BioCypher by detailing the desired properties per node
type in the schema configuration file.

(qs_schema-config)=
## The schema configuration YAML file

The second important component of translation into a BioCypher-compatible
property graph is the specification of graph constituents and their mode of
representation in the graph. For instance, we want to add a representation for
proteins to the OmniPath graph, and the proteins should be represented as nodes.
To make this known to the BioCypher module, we use the
[schema-config.yaml](https://github.com/biocypher/biocypher/blob/main/biocypher/_config/schema_config.yaml),
which details *only* the immediate constituents of the desired graph.  Since the
identifier systems in the Biolink schema are not comprehensive and offer many
alternatives, we currently use the CURIE prefixes directly as given by
[Bioregistry](https://bioregistry.io). For instance, a protein could be
represented, for instance, by a UniProt identifier, the corresponding ENSEMBL
identifier, or an HGNC gene symbol. The CURIE prefix for "Uniprot Protein" is
`uniprot`, so a consistent protein schema definition would be:

```{code-block} yaml
protein:
  represented_as: node
  preferred_id: uniprot
  input_label: protein
```

```{note}
For BioCypher classes, similar to the internal representation in the Biolink
model, we use lower sentence-case notation, e.g., `protein` and `small
molecule`. For file names and Neo4j labels, these are converted to PascalCase.
```

In the protein case, we are specifying its representation as a node,
that we wish to use the UniProt identifier as the main identifier for
proteins, and that proteins in the input coming from ``PyPath`` carry
the label ``protein`` (in lowercase). Should one wish to use ENSEMBL
notation instead of UniProt, the corresponding CURIE prefix, in this
case, `ensembl`, can be substituted.

```{code-block} yaml
protein:
  represented_as: node
  preferred_id: ensembl
  input_label: protein
```

If there exists no identifier system that is suitable for coverage of
the data, the standard field `id` can be used; this will not result in
the creation of a named property that reflects the identifier of each
node. See below for an example. The `preferred_id` field can in this case also
be omitted entirely; this will lead to the same outcome (`id`).

The other slots of a graph constituent entry contain information
BioCypher needs to receive the input data correctly and construct the
graph accordingly. For "Named Thing" entities such as the protein, this
includes the mode of representation (YAML entry ``represented_as``),
which can be ``node`` or ``edge``. Proteins can only feasibly
represented as nodes, but for other entities, such as interactions or
aggregates, representation can be both as node or as edge. In Biolink,
these belong to the super-class
[Associations](https://biolink.github.io/biolink-model/docs/associations.html).
For associations, BioCypher additionally requires the specification of
the source and target of the association; for instance, a
post-translational interaction occurs between proteins, so the source
and target attribute in the ``schema-config.yaml`` will both be
``protein``.

```{code-block} yaml
post translational interaction:
  represented_as: node
  preferred_id: id
  source: protein
  target: protein
  input_label: post_translational
```

For the post-translational interaction, which is an association, we are
specifying representation as a node (prompting BioCypher to create not
only the node but also two edges connecting to the proteins
participating in any particular post-translational interaction). In
other words, we are reifying the post-translational interaction in order
to have a node to which other nodes can be linked; for instance, we
might want to add a publication to a particular interaction to serve as
source of evidence, which is only possible for nodes in a property
graph, not for edges.

Since there are no systematic identifiers for post-translational
interactions, we concatenate the protein ids and relevant properties of
the interaction to a new unique id. We prevent creation of a specific
named property by specifying `id` as the identifier system in this case.
If a specific property name (in addition to the generic `id` field) is
desired, one can use any arbitrary string as a designation for this
identifier, which will then be a named property on the
``PostTranslationalInteraction`` nodes.

```{note}
BioCypher accepts non-Biolink IDs since not all possible entries possess a
systematic identifier system, whereas the entity class (``protein``, ``post
translational interaction``) has to be included in the Biolink schema and
spelled identically. For this reason, we [extend the Biolink
schema](tutorial_ontology_extension) in cases where there exists no entry for
our entity of choice. Further, we are specifying the source and target classes
of our association (both ``protein``), which are optional, and the label we
provide in the input from ``PyPath`` (``post_translational``).
```

If we wanted the interaction to be represented in the graph as an edge,
we would also need to supply an additional - arbitrary - property,
`label_as_edge`, which would be used as the relationship type; this
could for instance be `INTERACTS_POST_TRANSLATIONALLY`, following the
property graph database consensus that property graph edges are
represented in all upper case form and as verbs, to distinguish from
nodes that are represented in PascalCase and as nouns. This would modify
the above example to the following:

```{code-block} yaml
post translational interaction:
  represented_as: edge
  preferred_id: id
  source: protein
  target: protein
  input_label: post_translational
  label_as_edge: INTERACTS_POST_TRANSLATIONALLY
```

(quick_config)=
## The biocypher configuration YAML file
Most of the configuration options for BioCypher can and should be specified in
the configuration YAML file, `biocypher_config.yaml`. While BioCypher comes with
default settings (the ones you can see in the [Configuration](config) section),
we can override them by specifying the desired settings in the local
configuration in the root or the `config` directory of the project. The
primary BioCypher settings are found in the top-level entry `biocypher`. For
instance, you can select your output format (`dbms`) and output path, the
location of the schema configuration file, and the ontology to be used.

```{code-block} yaml

biocypher:
  dbms: postgresql
  output_path: postgres_out/
  schema_config: config/schema-config.yaml
  head_ontology:
    url: https://github.com/biolink/biolink-model/raw/v3.2.1/biolink-model.owl.ttl
    root_node: entity

```

You can currently select between `postgresql`, `neo4j`, and `arangodb` (beta) as
your output format; more options will be added in the future. The `output_path`
is relative to your working directory, as is the schema-config path. The
`ontology` should be specified as a (preferably persistent) URL to the ontology
file, and a `root_node` to specify the node from which the ontology should be
traversed.  We recommend using a URL that specifies the exact version of the
ontology, as in the example above.

### DBMS-specific settings
In addition to the general settings, you can specify DBMS-specific settings
under the `postgresql`, `arangodb`, or `neo4j` entry. For instance, you can
specify the database name, the host, the port, and the credentials for your
database. You can also set delimiters for the entities and arrays in your import
files. For a list of all settings, please refer to the [Configuration](config)
section.

```{code-block} yaml

neo4j:
  database_name: biocypher
  uri: neo4j://localhost:7687
  user: neo4j
  password: neo4j
  delimiter: ','

```
