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
`biocypher_config_path` parameter.

!!! note "Note"
	It is important to follow the rules of indentation in the YAML file.
	BioCypher module configuration is found under the top-level keyword
	`biocypher`, while the settings for DBMS systems (e.g., Neo4j) are found
	under their respective keywords (e.g., `neo4j`).

!!! warning "Quote characters"
    If possible, avoid using quote characters in your YAML files. If you
	need to quote, for instance a tab delimiter (`\t`), use single quotes
	(`'`), since double quotes (`"`) allow parsing of escape characters in
	YAML, which can cause issues downstream. It is safe to use double quotes
	to quote a single quote character (`"'"`).

Configuration files are read in the order `default -> user level -> project level`,
with the later ones overriding the preceding.

## Configuration Structure

The configuration file is structured into several sections:

1. **BioCypher Core Settings** (`biocypher:`) - Core settings for BioCypher functionality
    - choose `dbms` to select one of either the available DBMSs (2.) or data models (3.)
2. **Database Management Systems** - Settings specific to each supported DBMS:
    - Neo4j (`neo4j:`)
    - PostgreSQL (`postgresql:`)
    - SQLite (`sqlite:`)
3. **Data Models** - Settings for different data models:
    - RDF (`rdf:`)
    - NetworkX (`networkx:`)
    - CSV (`csv:`)

## Default Configuration

Below is the default configuration that comes with BioCypher. This represents all available options with their default values. Some options (like tail ontologies) are commented out in the default configuration as they are optional and specific to certain use cases.

```yaml title="Default biocypher_config.yaml"
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

## Configuration Parameters Reference

### BioCypher Core Parameters

| Parameter | Description | Type | Default |
|-----------|-------------|------|---------|
| `dbms` | Specifies which database management system to use | string | `"neo4j"` |
| `schema_config_path` | Path to the schema configuration file | string | `"config/schema_config.yaml"` |
| `offline` | Whether to run in offline mode (no running DBMS or in-memory object) | boolean | `true` |
| `strict_mode` | Whether to enforce strict schema validation | boolean | `false` |
| `head_ontology.url` | URL or file path to the main ontology file | string | Biolink model URL |
| `head_ontology.root_node` | The root node of the ontology to use | string | `"entity"` |
| `head_ontology.switch_label_and_id` | Whether to switch label and ID in the ontology | boolean | `true` |
| `log_to_disk` | Whether to save logs to disk | boolean | `true` |
| `debug` | Whether to enable debug logging | boolean | `true` |
| `log_directory` | Directory for log files | string | `"biocypher-log"` |
| `output_directory` | Directory for output files | string | `"biocypher-out"` |
| `cache_directory` | Directory for cache files | string | `".cache"` |
| `tail_ontologies` | Additional ontologies to use (optional) | object | - |

### Neo4j Configuration

| Parameter | Description | Type | Default |
|-----------|-------------|------|---------|
| `database_name` | Name of the Neo4j database | string | `"neo4j"` |
| `wipe` | Whether to wipe the database before import | boolean | `true` |
| `uri` | Connection URI for Neo4j | string | `"neo4j://localhost:7687"` |
| `user` | Username for Neo4j authentication | string | `"neo4j"` |
| `password` | Password for Neo4j authentication | string | `"neo4j"` |
| `delimiter` | Field delimiter for CSV import files | string | `";"` |
| `array_delimiter` | Delimiter for array values | string | `"\|"` |
| `quote_character` | Character used for quoting string values | string | `"'"` |
| `multi_db` | Whether to use multi-database support | boolean | `true` |
| `skip_duplicate_nodes` | Whether to skip duplicate nodes during import | boolean | `false` |
| `skip_bad_relationships` | Whether to skip relationships with missing endpoints | boolean | `false` |
| `import_call_bin_prefix` | Prefix for the import command binary (optional) | string | - |
| `import_call_file_prefix` | Prefix for import files (optional) | string | - |

### PostgreSQL Configuration

| Parameter | Description | Type | Default |
|-----------|-------------|------|---------|
| `database_name` | Name of the PostgreSQL database | string | `"postgres"` |
| `host` | Host address for PostgreSQL server | string | `"localhost"` |
| `port` | Port for PostgreSQL server | integer | `5432` |
| `user` | Username for PostgreSQL authentication | string | `"postgres"` |
| `password` | Password for PostgreSQL authentication | string | `"postgres"` |
| `quote_character` | Character used for quoting identifiers | string | `"\""` |
| `delimiter` | Field delimiter for import files | string | `"\t"` |
| `import_call_bin_prefix` | Path to psql (optional) | string | - |
| `import_call_file_prefix` | Prefix for import files (optional) | string | - |

### SQLite Configuration

| Parameter | Description | Type | Default |
|-----------|-------------|------|---------|
| `database_name` | Name of the SQLite database file | string | `"sqlite.db"` |
| `quote_character` | Character used for quoting identifiers | string | `"\""` |
| `delimiter` | Field delimiter for import files | string | `"\t"` |
| `import_call_bin_prefix` | Path to sqlite3 (optional) | string | - |
| `import_call_file_prefix` | Prefix for import files (optional) | string | - |

### RDF Configuration

| Parameter | Description | Type | Default |
|-----------|-------------|------|---------|
| `rdf_format` | Format for RDF output | string | `"turtle"` |

### NetworkX Configuration

| Parameter | Description | Type | Default |
|-----------|-------------|------|---------|
| `some_config` | Placeholder configuration | string | `"some_value"` |

### CSV Configuration

| Parameter | Description | Type | Default |
|-----------|-------------|------|---------|
| `delimiter` | Field delimiter for CSV files | string | `","` |
