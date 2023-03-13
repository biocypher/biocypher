
# Interacting with Neo4j
BioCypher development was initially centred around a Neo4j graph database output
due to the migration of OmniPath to a Neo4j backend. Importantly, we understand
BioCypher as an abstration of the build process of a biomedical knowledge graph,
and thus are open towards any output format for the knowledge representation. We
are currently working on other output formats, such as RDF, SQL, and ArangoDB,
and will update the documentation accordingly. In the following section, we give
an overview of interacting with Neo4j from the perspective of BioCypher, but we
refer the reader to the Neo4j documentation for more details.

## Communication via the Neo4j Python Driver

The BioCypher [Driver](driver) is the main submodule of BioCypher. It
establishes a connection with a running graph database via the
{py:class}`neo4j.GraphDatabase.driver`, integrates the funtions of the
other submodules, and serves as outside interface of BioCypher. The
``Driver`` is the main class for interacting with BioCypher in the host
module's adapter class. It handles authentification and basic database
management as well as the creation and manipulation of graph entries. It
can be instantiated and accessed like this:

```
import biocypher

# offline mode
d = biocypher.Driver(
   db_name = "neo4j",
   offline = True
)

# online mode
d = biocypher.Driver(
   db_name = "neo4j",
   db_user = "neo4j",
   db_passwd = "neo4j"
)
```

In our example, it is instantiated in the initialisation of the adapter,
and then called on for [interacting with a running graph](running) and
for exporting a complete database in CSV format for the [Neo4j
admin-import feature](admin_import). Upon instantiation, it
automatically assesses the graph database it is connected to (specified
using the ``db_name`` argument) regarding whether or not it already
contains a BioCypher graph, and, if so, what the structure of this graph
is.

If there exists no BioCypher graph in the currently active database, or
if the user explicitly specifies so using the ``wipe`` attribute of the
driver, a new BioCypher database is created using the schema
configuration specified in the [schema-config.yaml](schema-config).

(running)=
## Interacting with a running Neo4j instance

Once instantiated, the BioCypher driver can be used to modify the
current graph by adding or deleting nodes, edges, properties,
constraints, et cetera. Most commonly, the methods
{py:meth}`biocypher.driver.Driver.add_nodes()` and
{py:meth}`biocypher.driver.Driver.add_edges()` are used to introduce new
entries into the graph database.

(admin_import)=
## Exporting for the `neo4j-admin import` feature

Particularly if the data are very extensive (or performance is of the
utmost priority), BioCypher can be used to facilitate a speedy and safe
import of the data using the ``neo4j-admin import`` console command.
[Admin
Import](https://neo4j.com/docs/operations-manual/current/tutorial/neo4j-admin-import/)
is a particularly fast method of writing data to a newly created graph
database (the database needs to be completely empty) that gains most of
its performance advantage from turning off safety features regarding
input data consistency. Therefore, a sound and consistent representation
of the nodes and edges in the graph is of high importance in this
process, which is why the BioCypher export functionality has been
specifically designed to perform type and content checking for all data
to be written to the graph.

Data input from the source database is exactly as in the case of
[interacting with a running database](running), with the data
representation being converted to a series of CSV files in a designated
output folder (standard being ``biocypher-out/`` and the current datetime).
BioCypher creates separate header and data files for all node and edge
types to be represented in the graph via the driver methods
{py:meth}`biocypher.driver.Driver.write_nodes()` and
{py:meth}`biocypher.driver.Driver.write_edges()`. Additionally, it creates
a file called ``neo4j-admin-import-call.txt`` containing the console
command for creating a new database, which only has to be executed from
the directory of the currently running Neo4j database.

The name of the database to be created is given by the ``db_name``
attribute of the driver methods, ie, ``write_nodes()`` and
``write_edges()``, which should receive the same name as in the
``PyPath`` adapter example, and can be arbitrary. In case the
``db_name`` is not the default Neo4j database name, ``neo4j``, the
database needs to be created in Neo4j before or after using the
``neo4j-admin import`` statement. This can be done by executing, in the
running database (``<db_name>`` being the name assigned in the method):

1. ``:use system``
2. ``create database <db_name>``
3. ``:use <db_name>``

(translation)=
## Translating between original and BioCypher vocabulary
For quickly transitioning to BioCypher, single terms or entire queries
can be translated using the information provided in the
`schema_config.yaml`. The translation functionality can be accessed
through the driver methods {py:meth}`biocypher.driver.translate_term()`,
{py:meth}`biocypher.driver.reverse_translate_term()`,
{py:meth}`biocypher.driver.translate_query()`, and
{py:meth}`biocypher.driver.reverse_translate_query()`. For instance, to
find out the designation of "gene_gene" relationships in BioCypher, one
can call:

```
driver.translate_term("gene_gene")
# 'GeneToGeneAssociation'
```

Similarly, to discover the original naming of
"PostTranslationalInteraction" relationships, one can call the reverse
function:

```
driver.reverse_translate_term("PostTranslationalInteraction")
# 'post_translational'
```

{py:meth}`biocypher.driver.translate_query()` and
{py:meth}`biocypher.driver.reverse_translate_query()` replace all label
designations (following a ":") in entire CYPHER query strings with the
BioCypher or original versions, respectively.
