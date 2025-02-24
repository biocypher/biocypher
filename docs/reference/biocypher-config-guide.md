# BioCypher Configuration Reference

BioCypher comes with a default set of configuration parameters. You can
overwrite them by creating a `biocypher_config.yaml` file in the root
directory or the `config` directory of your project. You only need to
specify the ones you wish to override from default. If you want to
create global user settings, you can create a `biocypher_config.yaml` in your
default BioCypher user directory (as found using
`appdirs.user_config_dir('biocypher')`). For instance, on Mac OS, this would
be `~/Library/Caches/biocypher/biocypher_config.yaml`. Finally, you can also
point an instance of the BioCypher class to any YAML file using the
biocypher_config_path parameter.

!!! note "Note"
	It is important to follow the rules of indentation in the YAML file.
	BioCypher module configuration is found under the top-level keyword
	biocypher, while the settings for DBMS systems (e.g., Neo4j) are found
	under their respective keywords (e.g., neo4j).

!!! warning "Quote characters"
    If possible, avoid using quote characters in your YAML files. If you
	need to quote, for instance a tab delimiter (`\t`), use single quotes
	(`'`), since double quotes (`"`) allow parsing of escape characters in
	YAML, which can cause issues downstream. It is safe to use double quotes
	to quote a single quote character (`"'"`).

Configuration files are read in the order `default -> user level -> project level`,
with the later ones overriding the preceding. The following parameters are available:


## Purpose
The configuration in BioCypher customizes its behavior by overriding default
settings through a `biocypher_config.yaml` file. It ensures flexibility for
different use cases by allowing you to define data sources, database
connections, and output formats.


## Convention for naming
It is important to follow the rules of indentation in the YAML file. BioCypher
module configuration is found under the top-level keyword `biocypher`, while
the settings for DBMS systems (e.g., Neo4j) are found under their respective
keywords (e.g., `neo4j`).

If possible, avoid using quote characters in your YAML files. If you need to
quote, for instance a tab delimiter (`\t`), use single quotes (`'`), since
double quotes (`"`) allow parsing of escape characters in YAML, which can
cause issues downstream. It is safe to use double quotes to quote a single
quote character (`"'"`).

!!! warning "Quote characters"
    If possible, avoid using quote characters in your YAML files. If you need
	to quote, for instance a tab delimiter (`\t`), use single quotes (`'`),
	since double quotes (`"`) allow parsing of escape characters in YAML, which
	can cause issues downstream. It is safe to use double quotes to quote a
	single quote character (`"'"`).

Configuration files are read in the order `default -> user level -> project level`,
with the later ones overriding the preceding. The following parameters are available:

## YAML file Skeleton

```yaml title="biocypher_config.yaml"
biocypher:
  #---- REQUIRED PARAMETERS

  dbms: neo4j
  schema_config_path: config/schema_config.yaml
  offline: true
  strict_mode: false
  head_ontology:
    url: https://github.com/biolink/biolink-model/raw/v3.2.1/biolink-model.owl.ttl
    root_node: entity
    switch_label_and_id: true

  #---- OPTIONAL PARAMETERS
  log_to_disk: true

  debug: true

  log_directory: biocypher-log

  output_directory: biocypher-out

  cache_directory: .cache

  #---- OPTIONAL TAIL ONTOLOGIES

  # tail_ontologies:
  #   so:
  #     url: test/ontologies/so.owl
  #     head_join_node: sequence variant
  #     tail_join_node: sequence_variant
  #     switch_label_and_id: true
  #   mondo:
  #     url: test/ontologies/mondo.owl
  #     head_join_node: disease
  #     tail_join_node: disease
  #     switch_label_and_id: true

#-------------------------------------------------------------------
#-----------------       OUTPUT Configuration      -----------------
#-------------------------------------------------------------------
#---- NEO4J database management system
neo4j:
  database_name: neo4j
  wipe: true

  uri: neo4j://localhost:7687
  user: neo4j
  password: neo4j

  delimiter: ";"
  array_delimiter: "|"
  quote_character: "'"

  multi_db: true

  skip_duplicate_nodes: false
  skip_bad_relationships: false

  # import_call_bin_prefix: bin/
  # import_call_file_prefix: path/to/files/

#---- PostgreSQL database management system
postgresql:
  database_name: postgres

  host: localhost # host
  port: 5432 # port

  user: postgres
  password: postgres # password

  quote_character: '"'
  delimiter: '\t'
  # import_call_bin_prefix: '' # path to "psql"
  # import_call_file_prefix: '/path/to/files'

#---- SQLite database management system
sqlite:
  ### SQLite configuration ###

  # SQLite connection credentials
  database_name: sqlite.db # DB name

  # SQLite import batch writer settings
  quote_character: '"'
  delimiter: '\t'
  # import_call_bin_prefix: '' # path to "sqlite3"
  # import_call_file_prefix: '/path/to/files'

#---- RDF (Resource Description Framework) data model
rdf:
  ### RDF configuration ###
  rdf_format: turtle

#---- NetworkX graph data model
networkx:
  ### NetworkX configuration ###
  some_config: some_value # placeholder for technical reasons TODO

#---- CSV (Comma-Separated Values) text file format
csv:
  ### CSV/Pandas configuration ###
  delimiter: ","

```

## Fields reference:
### Biocypher section parameters
#### Required parameters
##### `dbms`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `head_ontology`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `offline`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `root_node`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `schema_config_path`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `strict_mode`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `switch_label_and_id`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `url`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

#### Optional parameters
##### `cache_directory`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `debug`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `log_directory`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `log_to_disk`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `output_directory`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `switch_label_and_id`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `tail_join_node`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `tail_ontologies`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `url`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

 ---
### Output configuration parameters
#### NEO4j DBMS
##### `array_delimiter`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `database_name`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `delimiter`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `import_call_bin_prefix`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `import_call_file_prefix`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `multi_db`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `password`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `quote_character`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `skip_duplicate_nodes`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `skip_bad_relationships`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `uri`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `user`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `wipe`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

#### PostgreSQL DBMS
##### `database_name`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `delimiter`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `host`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `import_call_bin_prefix`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `import_call_file_prefix`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `password`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `port`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `quote_character`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `user`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

#### SQLite DBMS
##### `database_name`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `delimiter`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `import_call_bin_prefix`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `import_call_file_prefix`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
##### `quote_character`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

#### RDF data model
##### `rdf_format`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

#### NetworkX graph data model
##### `some_config`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

#### NetworkX graph data model
##### `some_config`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]

#### CSV file format
##### `delimiter`
- **Description:** describe briefly the purpose of this property.
- **Possible values:**
  - possible value 1 [*datatype*]
  - possible value 2 [*datatype*]
