(adapters)=
# Adapters

BioCypher is a modular framework, with the main purpose of avoiding redundant
maintenance work for maintainers of secondary resources and end users alike. To
achieve this, we use a collection of reusable “adapters” for the different
sources of biomedical knowledge as well as for different ontologies. To see
whether your favourite resource is already supported or currently in
development, or if you would like to contribute to the development of a new
adapter, please refer to [this GitHub projects
view](https://github.com/orgs/biocypher/projects/3/views/2). Check the tabs for
different views.

```{note}
We are currently working on adapter documentation, so the collection in the
GitHub Projects view may be less than complete. Please get in touch if you want
to make sure that your favourite resource is supported.
```

The project view is built from issues in the [BioCypher GitHub repository](
https://github.com/biocypher/biocypher/issues), which carry labels for
adapters and adapter subtypes, as well as an ``Adapter status`` label to
indicate the state of development: ``Planned``, ``In progress``, ``Existing``,
and ``Ideas``.  If you would like to add or request an adapter that is not yet
listed, please open a new issue and we will add it to the project view.

(metagraph)=
## BioCypher meta-graph

::::{grid} 2
:gutter: 2

:::{grid-item-card} Online meta-graph:
:link: https://meta.biocypher.org
:text-align: center
{octicon}`plug;3em` {octicon}`share-android;3em`
:::

:::{grid-item-card} Repo with Docker setup:
:link: https://github.com/biocypher/meta-graph
:text-align: center
{octicon}`project;3em` {octicon}`container;3em`
:::

::::

We have built a BioCypher pipeline (from the [template
repository](https://github.com/biocypher/project-template)) that fetches
information about all adapters from the BioCypher GitHub repository via the
GitHub API and builds a graph of all adapters and their dependencies.  Browsing
this graph can give an overview of the current state of the adapters supported
by BioCypher and the pipelines they are used in. It is built daily and available
at https://meta.biocypher.org. The graph can also be built locally by cloning
the repository and running the pipeline using `docker compose up`. The graph is
then available at `localhost:7474/browser/` in the Neo4j Browser.

If you're unfamiliar with Neo4j, you can use the following Cypher query to
retrieve an overview of all graph contents:

```cypher
MATCH (n)
RETURN n
```

For more information on how to use the graph, please refer to the [Neo4j
documentation](https://neo4j.com/docs/).