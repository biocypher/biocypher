(adapter_functions)=
# The Host-BioCypher Adapter

The "BioCypher adapter" is a python program (in the case of ``PyPath``,
a submodule) responsible for piping the data that is to be represented
in the graph into BioCypher in a somewhat arbitrary format. It is an
expansion tailor-made for the source database as an interface to
BioCypher; in developing BioCypher, we strive to make its structure as
simple as possible to facilitate adaptation. Thus, the adapter usually
consists of only few central functions needed for the transfer of data
between the arbitrarily ordered source format and the highly
"automatically compatible" target format of BioCypher. In our example,
the adapter performs three main functions (with functions 2 and 3 being
mutually optional):

1. Load the ``PyPath`` data python object to be transferred to BioCypher
2. Pass the data to BioCypher as a stream or list to be written to the
   Neo4j database via the python driver ("online")
3. Pass the data to BioCypher as a stream or list to be written to the
   Neo4j database via admin import (batch import from CSV)

While function #2 can be performed at any time with a new or
pre-existing BioCypher graph, function #3 can only be used to create a
fresh database from scratch with all the input data. However, since
``neo4j-admin import`` is very fast, it can be used to combine subsets
of two databases on the fly, creating a new, combined database in the
process.

## Loading the Data

Depending on the data source, it is up to the user to find and define a
suitable representation to be piped into BioCypher. The way we handle it
in ``PyPath`` is only one of many: we load the entire ``PyPath`` object
into memory, to be passed to BioCypher using a generator that evaluates
each ``PyPath`` object and transforms it to the tuple representation
described below. This is made possible by the already standardised form
in which the data is represented within ``PyPath``. For more
heterogeneous data representations, additional transformations may be
necessary before piping into BioCypher.

## Passing the Data

In the [pypath
example](https://github.com/saezlab/pypath/blob/fc4c959c168ce80427189f8dd237308707594ad0/src/pypath/biocypher/adapter.py#L189),
we are using {py:class}`Generator`-type objects to pass an unordered
collection of ``PyPath`` contents into BioCypher. For nodes, we are
specifying for each object an ID and label (corresponding to its unique
preferred identifier and its ontological class), as well as a dictionary
of arbitrary properties, each entry as a 3-tuple. For relationships, the
same applies, except that we are passing two IDs, for source and target
entities, which results in a 4-tuple.

Currently, there are two modes of interaction with the graph database
implemented in BioCypher. The first takes place via the Neo4j python
driver, which is either loaded by BioCypher or passed from the host
module. The second generates CSV files containing node and edge data in
a standardised and safety-checked format to be used with the ``admin
import`` functionality of Neo4j. Safety checks are important here
because Neo4j does not guarantee consistency of the resulting graph when
using this feature; on the upside, this mode of communication is much
faster. However, it can only be used when creating a new graph, not for
changing an already existing one.

## Communication via the Neo4j Python Driver

The BioCypher [Driver](driver) is the main submodule of BioCypher.
It establishes a connection with a running graph database via the
{py:class}`neo4j.GraphDatabase.driver`, integrates the funtions of the
other submodules, and serves as outside interface of BioCypher. The
``Driver`` is the main class for interacting with BioCypher in the host
module's adapter class. It handles authentification and basic database
management as well as the creation and manipulation of graph entries.

In our example, it is instantiated in the initialisation of the adapter,
and then called on for [interacting with a running graph](running) and
for exporting a complete database in CSV format for the [Neo4j
admin-import feature](admin_import). Upon instantiation, it
automatically assesses the graph database it is connected to (specified
using the ``db_name`` attribute) regarding whether or not it already
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
