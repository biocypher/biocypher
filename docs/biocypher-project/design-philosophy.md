# BioCypher design philosophy

At its core, BioCypher is designed around the principle of **threefold modularity**:

1. Modular data sources – Seamlessly integrate diverse biomedical datasets.
2. Modular ontology structures – Define flexible, structured knowledge representations.
3. Modular output formats – Adapt results to various applications and tools.

## Design Principles

### 1. Modular data sources

#### Resources

Resources are diverse data inputs and sources that feed into the knowledge graph
through "adapters." A Resource could be a file, a list of files, an API request,
or a list of API requests. BioCypher can download resources from a given URL,
cache them, and manage their lifecycle.

#### Adapters

BioCypher is a modular framework, with the main purpose of avoiding redundant
maintenance work for maintainers of secondary resources and end users alike. To
achieve this, we use a collection of reusable "adapters" for the different
sources of biomedical knowledge as well as for different ontologies.

### 2. Modular ontology structures

#### Ontologies

An ontology is a formal, hierarchical representation of knowledge within a
specific domain, organizing concepts and their relationships. It structures
concepts into subclasses of more general categories, such as a *wardrobe* being
a subclass of *furniture*. BioCypher requires a certain amount of knowledge
about ontologies and how to use them. We try to make dealing with ontologies as
easy as possible, but some basic understanding is required.

Philosophically, a lot has changed since the introduction of current-generation
large language models (LLMs). For instance, LLMs bring a sophisticated world
model without explicitly modelling concepts, which is in stark contrast to the
modelling decisions of traditional ontologies. We need to critically re-evaluate
the future role of ontologies in the modern scientific knowledge management
ecosystem. They provide valuable context via the thousands of hours of human
curation, but they also come with many intricacies and inconsistencies.

!!! tip "Our Philosophy"

    BioCypher aims to disrupt the traditional workflow to boost knowledge
    management into the AI era. While we hope to preserve the benefits of human
    curation, we also want to critically re-evaluate the role of all parts of
    the knowledge representation pipeline.

### 3. Modular output formats

#### Outputs

Initially focused on Neo4j due to OmniPath's migration, BioCypher now supports
multiple output formats, including RDF, SQL, ArangoDB, CSV, PostgreSQL, SQLite,
and NetworkX, specified via the dbms parameter in the `biocypher_config.yaml`
file. Users can choose between online mode (manipulation of a running database)
or offline mode.

#### Configuration

Configuration in BioCypher involves setting up and customizing the system to
meet specific needs. BioCypher provides default configuration parameters, which
can be overridden by creating a `biocypher_config.yaml` file in your project's
root or config directory, specifying the parameters you wish to change.
