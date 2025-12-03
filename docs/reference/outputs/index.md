BioCypher development was initially centred around a Neo4j graph database output
due to the migration of OmniPath to a Neo4j backend. Importantly, we understand
BioCypher as an abstraction of the build process of a biomedical knowledge graph,
and thus are open towards any output format for the knowledge representation.

The used output format is specified via the `dbms` parameter in the
`biocypher_config.yaml` (see the [Configuration](../biocypher-config.md) for an
example).  Currently supported are:

* `neo4j`
* `arangodb`
* `rdf`
* `owl`
* `postgres`
* `sqlite`
* `tabular`
* `csv`
* `pandas`
* `networkx`

Furthermore, you can specify whether to use the `offline` or `online` mode.

- For the online mode set `offline: false`. The behavior of the online mode
  depends on the specified `dbms`. If the specified `dbms` is an in-memory
  database (e.g. `csv`, `networkx`), the in-memory Knowledge Graph can
  directly be accessed from the BioCypher instance. If the specified `dbms` is
  a database (e.g. `neo4j`), the online mode requires a running database
  instance and BioCypher will connect to this instance and directly writes the
  output to the database.

!!! note "Neo4j Driver Required for Online Mode"
    When using Neo4j in online mode, you need to install the Neo4j Python driver
    as an optional dependency: `pip install biocypher[neo4j]` or
    `uv add "biocypher[neo4j]"`. See the [Neo4j output documentation](neo4j-output.md)
    for more details.

- For the offline mode set `offline: true`. BioCypher will `write` the
  knowledge graph to files in a designated output folder (standard being
  `biocypher-out/` and the current datetime). Furthermore, you can generate a
  bash script to insert the knowledge graph files into the specified `dbms` by
  running `bc.write_import_call()`.

!!! warning "Warning"
	The `online` mode is currently only supported for `neo4j`, `tabular`,
	`csv`, `pandas`, and `networkx`.

Details about the usage of the `online` and `offline` mode and the different
supported output formats are described on individual pages for each output
format.

## Available Output formats

| Method      	| Offline mode 		|  Online mode (in-memory)	|
| :------------ | :-----------------|---------------------------|
| `Neo4j`		| :material-check:  | :material-check:  		|
| `ArangoDB`    | :material-check:	| :material-close: (pending)|
| `RDF` / `OWL`  | :material-check:	| :material-close: (pending)|
| `PostgreSQL`  | :material-check:	| :material-close: (pending)|
| `SQLite`    	| :material-check:	| :material-close: (pending)|
| `Tabular`    	| :material-check:	| :material-close:			|
| `CSV`    		| :material-check:	| :material-close:			|
| `Pandas`    	| :material-check:	| :material-check: 			|
| `NetworkX`    | :material-check:	| :material-check: 			|
