(adapters)=
# Adapters

BioCypher is a modular framework, with the main purpose of avoiding redundant
maintenance work for maintainers of secondary resources and end users alike. To
achieve this, we use a collection of reusable “adapters” for the different
sources of biomedical knowledge as well as for different ontologies. To see
whether your favourite resource is already supported or currently in
development, or if you would like to contribute to the development of a new
adapter, please refer to [this GitHub projects
view](https://github.com/orgs/saezlab/projects/5/views/6). Check the tabs for
different views.

```{note}
We are currently working on adapter documentation, so the collection in the
GitHub Projects view may be less than complete. Please get in touch if you want
to make sure that your favourite resource is supported.
```

The project view is built from issues in the [BioCypher GitHub repository](
https://github.com/saezlab/BioCypher/issues), which carry labels for
adapters and adapter subtypes, as well as an ``Adapter status`` label to
indicate the state of development: ``Planned``, ``In progress``, ``Existing``,
and ``Ideas``.  If you would like to add or request an adapter that is not yet
listed, please open a new issue and we will add it to the project view.

## BioCypher meta-graph

::::{grid} 1
:gutter: 2

:::{grid-item-card} BioCypher meta-graph with docker setup:
:link: https://github.com/saezlab/biocypher-meta-graph
:text-align: center
{octicon}`plug;3em` {octicon}`project;3em` {octicon}`share-android;3em` {octicon}`container;3em`
:::

::::

We have built a BioCypher pipeline (from the [template
repository](https://github.com/saezlab/biocypher-project-template)) that fetches
information about all adapters from the BioCypher GitHub repository via the
GitHub API and builds a graph of all adapters and their dependencies.  Browsing
this graph can give an overview of the current state of the adapters supported
by BioCypher and the pipelines they are used in. Currently, the graph must be
built locally by cloning the repository and running the pipeline using `docker
compose up`. The graph is then available at `localhost:7474/browser/` in the
Neo4j Browser. We plan on making it available online soon.
