(adapter_functions)=
# BioCypher Tutorial - Adapters

```{note}
For a list of existing and planned adapters, please see [here](adapters).
```

![BioCypher pipeline interface](figure_pipeline.png)

```{note}
To facilitate the creation of a BioCypher pipeline, we have created a template
repository that can be used as a starting point for your own adapter. It
contains a basic structure for an adapter, as well as a script that can be used
as a blueprint for a build pipeline. The repository can be found
[here](https://github.com/saezlab/biocypher-project-template).
```

A "BioCypher adapter" is a python program responsible for connecting to the
BioCypher core and providing it with the data from its associated resource.
In doing so, it should adhere to several design principles to ensure simple
interoperability between the core and multiple adapters. In essence, an adapter
should conform to an interface that is defined by the core to give information
about the nodes and edges the adapter provides to enable automatic harmonisation
of the contents. An adapter can be "primary", i.e., responsible for a single
"atomic" resource (e.g. UniProt, Reactome, etc.), or "secondary", i.e.,
connecting to a resource that is itself a combination of multiple primary
resources (e.g. OmniPath, Open Targets, etc.). Due to extensive prior
harmonisation, the latter is often easier to implement and thus is a good
starting point that can be subsequently extended to and replaced by primary
adapters.

```{caution}
The adapter interface is still under development and may change rapidly.
```

In general, one adapter fulfils the following tasks:

1. Load the data from the primary resource, for instance by using pypath
download / caching functions (as in the [UniProt example
adapter](https://github.com/HUBioDataLab/CROssBAR-BioCypher-Migration)), by
using columnar distributed data formats such as Parquet (as in the [Open Targets
example adapter](https://github.com/saezlab/OTAR-BioCypher)), by using a running
database instance (as in the [CKG example
adapter](https://github.com/saezlab/CKG-BioCypher/)), or by simply reading a
file from disk (as in the [Dependency Map example
adapter](https://github.com/saezlab/DepMap-BioCypher)). Generally, any method
that allows the efficient transfer of the data from adapter to BioCypher core is
acceptable.

2. Pass the data to BioCypher as a stream or list to be written to the Neo4j
database via the python driver ("online") or via admin import (batch import from
CSV). The latter has the advantage of high throughput and a low memory
footprint, while the former allows for a more interactive workflow but is much
slower, thus making it better suited for small incremental updates.

3. Provide or connect to additional functionality that is useful for the
creation of knowledge graphs, such as identifier translation (e.g. via
pypath.mapping as in the UniProt example adapter), or identifier and prefix
standardisation and validation (e.g. via Bioregistry as in the UniProt example
adapter and others).

```{note}
For developers: We follow a design philosophy of "separation of concerns" in
BioCypher. This means that the core should not be concerned with the details of
how data is loaded, but only with the data itself. This is why the core does not
contain any code for loading data from a resource, but only for writing it to
the database. The adapter is responsible for loading the data and passing it to
the core, which allows for a more modular design and makes it easier to
maintain, extend, and reuse the code.

For introduction of new features, we recommend to first implement them in the
adapter, and to move them to the core only if they have shown to be useful for
multiple adapters.
```

## 1. Loading the Data

Depending on the data source, it is up to the developer of the adapter to find
and define a suitable representation to be piped into BioCypher. The way we
handle it in ``PyPath`` is only one of many: we load the entire ``PyPath``
object into memory, to be passed to BioCypher using a generator that evaluates
each ``PyPath`` object and transforms it to the tuple representation described
below. This is made possible by the "pre-harmonised" form in which the data
is represented within ``PyPath``. For more heterogeneous data representations,
additional transformations may be necessary before piping into BioCypher.

For larger datasets, it can be beneficial to adopt a streaming approach or batch
processing, as demonstrated in the [Open Targets
adapter](https://github.com/saezlab/OTAR-BioCypher) and the [CKG
adapter](https://github.com/saezlab/CKG-BioCypher/). BioCypher can handle input
streams of arbitrary length via Python generators.

## 2. Passing the Data

We currently pass data into BioCypher as a collection of tuples. Nodes are
represented as 3-tuples, containing:
- the node ID (unique in the space of the knowledge graph, ideally a CURIE with
  a prefix registered in the Bioregistry)
- the node type, i.e., its label (this is the string that is mapped to an
  ontological class via the `input_label` field in the schema configuration)
- a dictionary of node attributes

While edges are represented as 5-tuples, containing:
- the (optional) relationship ID (unique in the space of the KG)
- the source node ID (referring to a unique node ID in the KG)
- the target node ID (referring to a unique node ID in the KG)
- the relationship type, i.e., its label (this is the string that is mapped to
  an ontological class via the `input_label` field in the schema configuration)
- a dictionary of relationship attributes

```{note}
This representation will probably be subject to change soon and yield to a more
standardised interface for nodes and edges, derived from a BioCypher core class.
```

## Note: Strict mode
We can activate BioCypher strict mode with the `strict_mode` parameter upon
instantiation of the driver. In strict mode, the driver will raise an error if
it encounters a node or edge without data source, version, and licence. These
currently need to be provided as part of the node and edge attribute
dictionaries, with the reserved keywords `source`, `version`, and `licence` or
`license`. However, this may change to a more rigorous implementation in the
future.
