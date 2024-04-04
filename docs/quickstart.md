# Quickstart

::::{grid} 2
:gutter: 2

:::{grid-item-card} Already familiar? Here's a template:
:link: https://github.com/biocypher/project-template
:text-align: center
{octicon}`mark-github;3em` {octicon}`repo;3em` {octicon}`play;3em` {octicon}`container;3em`
:::

:::{grid-item-card} New to BioCypher? Follow the tutorial:
:link: tutorial_basic
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

The BioCypher workflow of creating your own knowledge graph consists of three
consecutive steps:

1. Clearly define the scope of your project, including the data sources you want
to use, the entities and relationships you want to represent, and the
[ontologies](tutorial_ontologies) that should inform these entities.

2. Using these definitions, find existing [adapters of data
sources](qs_input-adapter) or, if necessary, create your own. For the data
yielded by these adapters, create a [schema configuration](qs_schema-config)
file that tells BioCypher how to represent the entities and relationships in the
graph.

3. [Run BioCypher](qs_run-bc) using the adapters and schema config to create the
knowledge graph. If necessary, iterate over KG construction and configuration
until you are satisfied with the result.

(qs_input-adapter)=
## The input adapter

BioCypher follows a modular approach to data inputs; to create a knowledge
graph, we use at least one adapter module that provides a data stream to build
the graph from. Examples for current adapters can be found on the [GitHub
project adapter view](https://github.com/orgs/biocypher/projects/3/views/2).
This is the first place to look when creating your own KG; BioCypher adapters
are meant to be reusable and a centralised way of maintaining access to data
sources.

Adapters can ingest data from many different input formats, including Python
modules as in the [CROssBAR
adapter](https://github.com/HUBioDataLab/CROssBAR-BioCypher-Migration) (which
uses the OmniPath backend software, PyPath, for downloading and caching data),
advanced file management formats such as Parquet as in the [Open Targets
adapter](https://github.com/biocypher/open-targets), or simple CSV files as in
the [Dependency Map adapter](https://github.com/biocypher/dependency-map).

The main function of the adapter is to pass data into BioCypher, usually
as some form of iterable (commonly a list or generator of items). As a
minimal example, we load a list of proteins with identifiers, trivial
names, and molecular masses from a (fictional) CSV:

```{code-block} python
:caption: Adapter yielding nodes

# read data into df
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

```

For nodes, BioCypher expects a tuple containing three entries; the preferred
identifier of the node, the type of entity, and a dictionary containing all
other properties (can be empty). What BioCypher does with the received
information is determined largely by the schema configuration detailed below.

```{code-block} python
:caption: Adapter yielding edges

# read data into df
with open("file.csv", "r") as f:
  interactions = pd.read_csv(f)

# yield interactions from data frame
def edge_generator():
  for i in interactions:
    _id = i["id"]
    _source = i["source"]
    _target = i["target"]
    _type = "interaction"
    _props = {
      "type": i["relationship_type"],
      "score": i["score"],
    }

    yield (_id, _source, _target, _type, _props)

```

For edges, BioCypher expects a tuple containing five entries; the preferred
identifier of the edge (can be `None`), the identifier of the source node
(non-optional), the identifier of the target node (non-optional), the type of
relationship, and a dictionary containing all other properties (can be empty).

For advanced usage, the type of node or edge can be determined
programatically. Properties do not need to be explicitly called one by
one; they can be passed in as a complete dictionary of all entries and
filtered inside BioCypher by detailing the desired properties per node
type in the schema configuration file.

(qs_schema-config)=
## The schema configuration YAML file

The second important component of translation into a BioCypher-compatible
knowledge graph is the specification of graph constituents and their mode of
representation in the graph. To make this known to the BioCypher module, we use
the
[schema-config.yaml](https://github.com/biocypher/biocypher/blob/main/biocypher/_config/test_schema_config.yaml),
which details *only* the immediate constituents of the desired graph as the
top-level entries in the YAML file. While each of these top-level entries is
required to be found in the underlying ontology (for instance, the [Biolink
model](https://biolink.github.io/biolink-model/)), the `input_label` field is
arbitrary and has to match the `_type` yielded by the adapter (compare above).

Other fields of each entry can refer to the representation of the entity in the
KG (`represented_as: node`), and the identifier namespace chosen for each entity
type. For instance, a protein could be represented by a UniProt identifier, the
corresponding ENSEMBL identifier, or an HGNC gene symbol. We prefer the CURIE
prefix for unambiguous identification of entities. The CURIE prefix for "Uniprot
Protein" is `uniprot`, so a consistent protein schema definition would be:

```{code-block} yaml
protein:                    # top-level entry, has to match ontology
  represented_as: node      # mode of representation: node or edge
  preferred_id: uniprot     # preferred identifier namespace
  input_label: protein      # label that identifies members of this class (_type)
```

```{note}
For BioCypher classes, similar to the internal representation in the Biolink
model, we use lower sentence-case notation, e.g., `protein` and `small
molecule`. For file names and Neo4j labels, these are converted to PascalCase.
For more information, see the [Ontology tutorial](tutorial_ontologies).
```

The above configuration of the protein class specifies its representation as a
node, that we wish to use the UniProt identifier as the main identifier for
proteins, and that proteins in the data stream from the adapter carry the label
(`_type`) ``protein`` (in lowercase). Should we want to use the ENSEMBL
namespace instead of UniProt IDs, the corresponding CURIE prefix, in this case,
`ensembl`, can be substituted:

```{code-block} yaml
protein:
  represented_as: node
  preferred_id: ensembl
  input_label: protein
```

If there exists no identifier system that is suitable for coverage of the data
(which is fairly common when it comes to relationships), `preferred_id` field
can be omitted. This will lead to the creation of a generic `id` property on
this node or edge type.

(qs_run-bc)=
## BioCypher API documentation

BioCypher is instantiated using the `BioCypher()` class, which can be called
without arguments, given that the [configuration](qs_config) files are either
present in the working directory, or the pipeline should be run with default
settings.

```{code-block} python
from biocypher import BioCypher
bc = BioCypher()
```

BioCypher's main functionality is writing the graph (nodes and edges) to a
database or files for database import. We exemplarise this using the Neo4j
output format, writing CSV files formatted for the Neo4j admin import. In this
example, `node_generator()` and `edge_generator()` are the adapter functions
that yield nodes and edges, respectively (see above).

```{code-block} python
bc.write_nodes(node_generator())
bc.write_edges(edge_generator())
```

Node and edge generators can contain arbitrarily many types of nodes and edges,
which will be mapped via the schema configuration and sorted by BioCypher.
One instance of the BioCypher class keeps track of the nodes and edges that
have been written to the database, so that multiple calls to `write_nodes()`
and `write_edges()` will not lead to duplicate entries in the database.

For on-line writing to a database or a Pandas dataframe, we use the functions
with `add` instead of `write`. For instance, to add nodes and edges to a Pandas
dataframe, we can use:

```{testcode} python
:hide:
from biocypher import BioCypher
bc = BioCypher()

def check_if_function_exists(module_name, function_name):
    if hasattr(module_name, function_name):
        print("Functions exists")
    else:
        print("Function does not exist")
check_if_function_exists(bc, "add_nodes")
check_if_function_exists(bc, "add_edges")
```
```{testoutput} python
:hide:
Functions exists
Functions exists
```

```{code-block} python
bc.add_nodes(node_generator())
bc.add_edges(edge_generator())
```

To retrieve the dataframe once all entities are in the graph, we can call
`to_df()`:

```{code-block} python
df = bc.to_df()
```

For more information on the usage of these functions, please refer to the
[Tutorial](tutorial_basic) section and the [full API
documentation](api-reference).

(qs_config)=
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
:caption: biocypher_config.yaml

biocypher:
  dbms: postgresql
  output_path: postgres_out/
  schema_config: config/schema-config.yaml
  head_ontology:
    url: https://github.com/biolink/biolink-model/raw/v3.2.1/biolink-model.owl.ttl
    root_node: entity

```

You can currently select between `postgresql`, `neo4j`, `rdf` (beta), and
`arangodb` (beta) as your output format; more options will be added in the
future. The `output_path` is relative to your working directory, as is the
schema-config path. The `ontology` should be specified as a (preferably
persistent) URL to the ontology file, and a `root_node` to specify the node from
which the ontology should be traversed.  We recommend using a URL that specifies
the exact version of the ontology, as in the example above.

### DBMS-specific settings

In addition to the general settings, you can specify settings specific to each
DBMS (database management system) in the configuration file under the
`postgresql`, `arangodb`, `rdf`, or `neo4j` entry. For instance, you can specify
the database name, the host, the port, and the credentials for your database.
You can also set delimiters for the entities and arrays in your import files.
For a list of all settings, please refer to the [Configuration](config) section.

```{code-block} yaml
:caption: biocypher_config.yaml

neo4j:
  database_name: biocypher
  uri: neo4j://localhost:7687
  user: neo4j
  password: neo4j
  delimiter: ','

```
