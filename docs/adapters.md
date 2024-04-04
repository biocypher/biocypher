(adapters_info)=
# Adapters

BioCypher is a modular framework, with the main purpose of avoiding redundant
maintenance work for maintainers of secondary resources and end users alike. To
achieve this, we use a collection of reusable “adapters” for the different
sources of biomedical knowledge as well as for different ontologies. To see
whether your favourite resource is already supported or currently in
development, or if you would like to contribute to the development of a new
adapter, please refer to [this GitHub projects
view](https://github.com/orgs/biocypher/projects/3/views/2) (check the tabs for
different views) or the [meta-graph instance](metagraph).

```{note}
We are currently working on adapter documentation, so the collection in the
GitHub Projects view may be less than complete. Please get in touch if you want
to make sure that your favourite resource is supported.
```

::::{grid} 1
:gutter: 2

:::{grid-item-card} Adapter Tutorial
:link: https://biocypher.org/tutorial-adapter.html
:text-align: center
For more information on developing your own adapters, please refer to this
tutorial.
:::

::::

The project view is built from issues in the [BioCypher GitHub repository](
https://github.com/biocypher/biocypher/issues), which carry ``Fields`` (a
GitHub Projects-specific attribute) to describe their category and features. In
detail, these are as follows:

- ``Component Type``: This refers to the class of component and can be one of
``Adapter``, ``Ontology``, or ``Pipeline``.

- ``Adapter Granularity``: This is only applicable to adapters and can be either
``Primary`` (denoting an atomic resource that is represented by the adapter) or
``Secondary`` (denoting a composite resource, often pre-harmonised).

- ``Adapter Input Format`` provides a drop-down menu of the different formats
that can be ingested, such as ``Flat File``, ``API``, or ``OWL``. Select the one
that applies to the resource.

- ``Resource URL``: A free-text field to provide a link to the resource, also
used for identification purposes.

- ``Resource Type``: Currently only ``Database`` or ``Ontology``, but more
granular reporting is planned.

- ``Data Type`` provides a drop-down menu of the different data types that can
be ingested, such as ``Proteomics``, ``Genetics``, or ``Clinical``. Select the
one that applies to the resource. This field primarily makes sense for primary
adapters, but is interesting information particularly for the pipelines that use
the adapters. For that reason, when building the meta-graph (see below), we
propagate this information from the adapters to the pipelines.

```{caution}

There is currently one type of meta-information that needs to be provided via
free-text annotation in the text body of the issue: the links of pipelines to
the input adapters and ontologies they use. For the meta-graph pipeline to work
correctly, this information needs to be provided in the issue of the pipeline,
in a line that starts with ``Uses: ``, followed by a space-separated list of
issue numbers representing the used components.

To make this annotation less error-prone, we use the auto-completion GitHub
provides for referencing issues. Typing a ``#`` character and then a few
characters of the title of the issue to be linked to the pipeline will show a
list of possible matches. Select the correct one and the issue number will be
inserted automatically.

The meta-graph pipeline extracts this information and uses it to build the
meta-graph described below.

```

(metagraph)=
## BioCypher meta-graph

::::{grid} 2
:gutter: 2

:::{grid-item-card} Online meta-graph:
:link: https://meta.biocypher.org
:text-align: center
{octicon}`globe;3em` {octicon}`browser;3em` {octicon}`share-android;3em`
:::

:::{grid-item-card} Repo with Docker setup:
:link: https://github.com/biocypher/meta-graph/tree/read_only
:text-align: center
{octicon}`mark-github;3em` {octicon}`project;3em` {octicon}`container;3em`
:::

::::

We have built a BioCypher pipeline (from the [template
repository](https://github.com/biocypher/project-template)) that fetches
information about all adapters from the BioCypher GitHub repository via the
GitHub API and builds a graph of all adapters and their dependencies.  Browsing
this graph can give an overview of the current state of the adapters supported
by BioCypher and the pipelines they are used in. It is built daily and available
at [https://meta.biocypher.org](https://meta.biocypher.org). The graph can also
be built locally by cloning the repository and running the pipeline using
`docker compose up`. The graph is then available at `localhost:7474/browser/` in
the Neo4j Browser.

If you're unfamiliar with Neo4j, you can use the following Cypher query to
retrieve an overview of all graph contents:

```cypher
MATCH (n)
RETURN n
```

For more information on how to use the graph, please refer to the [Neo4j
documentation](https://neo4j.com/docs/).
