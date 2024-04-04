# Installation
## Install as a dependency for your KG pipeline

::::{grid} 1
:gutter: 2

:::{grid-item-card} Preconfigured project with BioCypher as a dependency, including docker integration:
:link: https://github.com/biocypher/project-template
:text-align: center
{octicon}`mark-github;3em` {octicon}`repo;3em` {octicon}`play;3em` {octicon}`container;3em`
:::

::::

The recommended way of installing BioCypher is through the PyPI distribution.
You can use any package manager that can install from PyPI, such as pip, conda,
poetry, etc. We recommend Poetry, you can get it
[here](https://python-poetry.org/docs/#installation). You can install BioCypher
as a dependency as follows:

```{code-block} bash
:caption: poetry install
poetry new my-awesome-kg-project
cd my-awesome-kg-project
poetry add biocypher
```

Alternatively, using conda/pip:

```{code-block} bash
:caption: pip install
conda create --name biocypher python=3.10
conda activate biocypher
pip install biocypher
```

```{note}
BioCypher generally supports the most recent three Python versions. If you
encounter any issues with a specific Python version, please open an issue on
GitHub.
```

## For developers
If you want to directly install BioCypher, here are the steps (requires
[Poetry](https://python-poetry.org/docs/#installation)):

```{code-block} bash
:caption: Execute in bash
git clone https://github.com/biocypher/biocypher
cd BioCypher
poetry install
```

Poetry creates a virtual environment for you (starting with `biocypher-`;
alternatively you can name it yourself) and installs all dependencies.

If you want to run the tests that use a local Neo4j or PostgreSQL DBMS (database
management system) instance:

- Make sure that you have a Neo4j instance with the APOC plugin installed and a
database named `test` running on standard bolt port `7687`

- A PostgreSQL instance with the psql command line tool should be installed
locally and running on standard port `5432`

- Activate the virtual environment by running `% poetry shell` and then run the
tests by running `% pytest` in the root directory of the repository with the
command line argument `--password=<your DBMS password>`.

Once this is set up, you can go through the [tutorial](tutorial_basic) or use it
in your project as a local dependency.

(config)=
# Configuration

BioCypher comes with a default set of configuration parameters. You can
overwrite them by creating a `biocypher_config.yaml` file in the root directory
or the `config` directory of your project. You only need to specify the ones you
wish to override from default. If you want to create global user settings, you
can create a `biocypher_config.yaml` in your default BioCypher user directory
(as found using `appdirs.user_config_dir('biocypher')`). For instance, on Mac
OS, this would be `~/Library/Caches/biocypher/biocypher_config.yaml`. Finally,
you can also point an instance of the
[BioCypher](https://biocypher.org/modules/biocypher.BioCypher.html#biocypher.BioCypher)
class to any YAML file using the `biocypher_config_path` parameter.

```{note}

It is important to follow the rules of indentation in the YAML file. BioCypher
module configuration is found under the top-level keyword `biocypher`, while
the settings for DBMS systems (e.g., Neo4j) are found under their respective
keywords (e.g., `neo4j`).

```

```{admonition} Quote characters
:class: warning

If possible, avoid using quote characters in your YAML files. If you need to
quote, for instance a tab delimiter (`\t`), use single quotes (`'`), since
double quotes (`"`) allow parsing of escape characters in YAML, which can cause
issues downstream. It is safe to use double quotes to quote a single quote
character (`"'"`).

```

Configuration files are read in the order `default -> user level -> project
level`, with the later ones overriding the preceding. The following parameters
are available:

## BioCypher settings
```{code-block} yaml
:caption: biocypher_config.yaml

biocypher:  ### BioCypher module configuration ###

  ### Required parameters ###
  # DBMS type
  dbms: neo4j

  # Offline mode: do not connect to a running DBMS instance
  # Can be used e.g. for writing batch import files
  offline: true

  # Strict mode: do not allow to create new nodes or relationships without
  # specifying source, version, and license parameters
  strict_mode: false

  # Schema configuration: mapping of inputs to ontology
  user_schema_config_path: biocypher/_config/test_schema_config.yaml

  # Ontology configuration
  head_ontology:
    url: https://github.com/biolink/biolink-model/raw/v3.2.1/biolink-model.owl.ttl
    root_node: entity

  ### Optional parameters ###
  # Logging granularity
  # Set debug to true if more granular logging is desired
  debug: false

  # Set to change the log directory
  log_directory: biocypher-log

  # Set to change the output directory
  output_directory: biocypher-out

  # Set to change the Resource cache directory
  cache_directory: .cache

  # Optional tail ontologies
  tail_ontologies:
    so:
      url: test/ontologies/so.owl
      head_join_node: sequence variant
      tail_join_node: sequence_variant
    mondo:
      url: test/ontologies/mondo.owl
      head_join_node: disease
      tail_join_node: disease

```
