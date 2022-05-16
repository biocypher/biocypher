.. BioCypher documentation master file, created by
   sphinx-quickstart on Tue Oct  5 20:09:15 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: biocypher-open-graph.png

############
Introduction
############

BioCypher is designed to serve as guideline and translation mechanism
for both the creation of biomedical property graph databases from
primary data as well as for the querying of these databases. The purpose
is to combine the computational power of graph databases with the search
for answers of our most pressing biological questions and facilitate
interfacing with cutting edge developments in the areas of causal
reasoning, representation learning, and natural language processing, all
of which depend on having a consistent descriptive vocabulary. To
achieve meaningful automatic representations in the biomedical language
space, we include the `Biolink model
<https://biolink.github.io/biolink-model/>`_ as underlying hierarchical
ontology, supplying identification, filtering, and mapping capabilities.
We are also keeping an open mind about adding alternative ontological
systems using an opt-in philosophy. Side objectives are the creation of
human-readable graph syntax and facilitating ultra-rapid graph 
creation through the Neo4j :ref:`admin-import <admin_import>` feature.

.. Caution::

   BioCypher is currently in prototype state; we are working on a
   full-featured implementation for the migration of OmniPath at the
   moment. Functionality regarding the translation between different
   database formats and identifiers therefore is rudimentary or
   non-existent as of now.

##########
Quickstart
##########

The main interface for interacting with the BioCypher module to create
your own property graph consists of two components:

1. the :ref:`host module adapter <host-module-adapter>`, a python
   program, and
2. the :ref:`schema configuration file <schema-config>`, a YAML file. 

The adapter serves as a data interface between the source and BioCypher,
piping the "raw" data into BioCypher for the creation of the property
graph, while the schema configuration tells BioCypher how the graph
should be structured, detailing the names of constituents and how they
should be connected.

.. _host-module-adapter:

The host module adapter
=======================

Currently, BioCypher expects input from the user module via an adapter module.
Throughout the tutorial, we will exemplarise the use of BioCypher using 
`OmniPath <https://omnipathdb.org>`_ (more specifically, its infrastructural 
backend, `PyPath <https://github.com/saezlab/pypath>`_). The adapter
has the job of piping the data as it is represented in the original database
into the BioCypher input, for instance as a :py:class:`Generator` object of 
single database entries, whether they be nodes or relationships in the graph
to be created. For more details, please refer to the example `PyPath adapter 
<https://github.com/saezlab/pypath/blob/master/pypath/biocypher/adapter.py>`_ 
and the section on :ref:`adapter functions <adapter>`.

.. _schema-config:

The schema configuration YAML file
==================================

The second important component of translation into a BioCypher-compatible
property graph is the specification of graph constituents and their mode of
representation in the graph. For instance, we want to add a representation for
proteins to the OmniPath graph, and the proteins should be represented as 
nodes. To make this known to the BioCypher module, we use the 
`schema-config.yaml <https://github.com/saezlab/BioCypher/blob/main/config/schema_config.yaml>`_,
which details *only* the immediate constituents of the desired graph. The 
naming of these constituents must be equal to the ontological category of
the entity in the Biolink schema. The ontological category (or class) of 
proteins in Biolink is simply `Protein <https://biolink.github.io/biolink-model/docs/Protein.html>`_.
However, for more complex concepts, such as - for instance - pairwise
molecular interactions, the naming must also be consistent; in this case, 
`PairwiseMolecularInteraction <https://biolink.github.io/biolink-model/docs/PairwiseMolecularInteraction.html>`_.
Similarly, if translation functionality between identifiers is desired, the 
identifier used for the class of graph entity must be consistent with the one 
used in the Biolink specification. For proteins, this can be ``UniProtKB``
(but not, for instance, ``UniProt`` or ``uniprot``). For ease of access, we provide 
a standard yaml file with the most common graph constituents and identifiers,
with the following basic structure:

.. literal block

:: 

   Protein:

      represented_as: node 

      preferred_id: UniProtKB  

      label_in_input: protein  

In the protein case, we are specifying its representation as a node, that we 
wish to use the UniProt identifier as the main identifier for proteins (the
Biolink designation for UniProt identifiers is ``UniProtKB``), and that proteins
in the input coming from ``PyPath`` carry the label ``protein`` (in lower-case).

The other slots of a graph constituent entry contain information BioCypher
needs to receive the input data correctly and construct the graph accordingly.
For "Named Thing" entities such as the protein, this includes the mode of 
representation (YAML entry ``represented_as``), which can be ``node`` or ``edge``. 
Proteins can only feasibly represented as nodes, but for other entities, such 
as interactions or aggregates, representation can be both as node or as edge. 
In Biolink, these belong to the super-class 
`Associations <https://biolink.github.io/biolink-model/docs/associations.html>`_.
For associations, BioCypher additionally requires the specification of the 
source and target of the association; for instance, a post-translational 
interaction occurs between proteins, so the source and target attribute in the 
``schema-config.yaml`` will both be ``Protein``. Again, these should adhere to the
naming scheme of Biolink.

::

   PostTranslationalInteraction:
   
      represented_as: node
      
      preferred_id: concat_ids
      
      source: Protein 
      
      target: Protein 
      
      label_in_input: post_translational 
      
      label_as_edge: INTERACTS_POST_TRANSLATIONAL

For the post-translational interaction, which is an association, we are 
specifying representation as a node (prompting BioCypher to create not only
the node but also two edges connecting to the proteins participating in any
particular post-translational interaction). In other words, we are reifying
the post-translational interaction in order to have a node to which other 
nodes can be linked; for instance, we might want to add a publication to a
particular interaction to serve as source of evidence, which is only possible
for nodes in a property graph, not for edges.

Since there are no systematic identifiers for post-translational interactions, 
we concatenate the protein ids and relevant properties of the interaction to a 
new unique id (arbitrarily named ``concat_ids``). 
Note that BioCypher accepts non-Biolink IDs since not all possible entries 
possess a systematic identifier system, whereas the entity class (``Protein``, 
``PostTranslationalInteraction``) has to be included in the Biolink schema 
and spelled identically. For this reason, we :ref:`extend the Biolink schema 
<biolink>` in cases where there exists no entry for our entity of choice.

Further, we are specifying the source and target classes of our association
(both ``Protein``), the label we provide in the input from ``PyPath`` 
(``post_translational``), and - optionally - the label we would want the edge
in the graph to carry would the association be represented as an edge. This 
has no bearing on the current example, where we choose representation as a 
node, but is important for edge representation, as by consensus, property
graph edges are represented in all upper case form and as verbs, to distinguish
from nodes that are represented in PascalCase and as nouns.

.. _biolink:

The Biolink model extension
===========================

The post-translational interaction that we would like to model in OmniPath has no
literal counterpart in the Biolink model, due to its design philosophy. 
The most granular level of interactions as Biolink class is the 
`PairwiseMolecularInteraction <https://biolink.github.io/biolink-model/docs/PairwiseMolecularInteraction.html>`_;
all more granular relationships should be encoded in the properties of the 
class, which has severe performance implications for property graph 
representation, for instance in filtering for specific relationship types.
Briefly, it is the difference between being able to selectively return only 
relationships of a certain class (eg, post-translational), and having to return
all relationships to filter for the ones possessing the correct property in a 
second step.

Therefore, we extend the Biolink model in places where it is necessary for the
BioCypher translation and integration to work. The extended model is the 
central Biolink YAML file with additions following the same 
`LinkML <https://linkml.io>`_ syntax as is used in the original model.
Depending on the extent of the modification, not only new classes are 
introduced, but also new mixin categories (eg, "microRNA or siRNA" to account
for different types of small noncoding RNA). We provide `our extended version 
of the Biolink model 
<https://github.com/saezlab/BioCypher/blob/main/config/biocypher-biolink-model.yaml>`_ 
with the BioCypher repository.

Changes or additions desired by the user can be introduced locally in this file
without having to modify remote contents. Users also have the option to create
their own modified version of the Biolink YAML file under a different file name
and specify that path in the ``custom_yaml_file`` argument of the 
:class:`biocypher.translate.BiolinkAdapter` class, which handles all 
communication between BioCypher and Biolink.

.. _adapter:

##########################
The Host-BioCypher Adapter
##########################

The "BioCypher adapter" is a python program (in the case of ``PyPath``, a 
submodule) responsible for piping the data that is to be represented in the 
graph into BioCypher in a somewhat arbitrary format. 
It is an expansion tailor-made for the source database as an interface to 
BioCypher; in developing BioCypher, we strive to make its structure as simple
as possible to facilitate adaptation. Thus, the adapter usually consists of 
only few central functions needed for the transfer of data between the 
arbitrarily ordered source format and the highly "automatically compatible"
target format of BioCypher.
In our example, the adapter performs three main functions (with functions 2 
and 3 being mutually optional):

1. Load the ``PyPath`` data python object to be transferred to BioCypher
2. Pass the data to BioCypher as a stream or list to be written to the Neo4j
   database via the python driver ("online")
3. Pass the data to BioCypher as a stream or list to be written to the Neo4j
   database via admin import (batch import from CSV)

While function #2 can be performed at any time with a new or pre-existing 
BioCypher graph, function #3 can only be used to create a fresh database from
scratch with all the input data. However, since ``neo4j-admin import`` is very
fast, it can be used to combine subsets of two databases on the fly, creating
a new, combined database in the process.

Loading the Data
================

Depending on the data source, it is up to the user to find and define a 
suitable representation to be piped into BioCypher. The way we handle it in
``PyPath`` is only one of many: we load the entire ``PyPath`` object into memory, to 
be passed to BioCypher using a generator that evaluates each ``PyPath`` object
and transforms it to the tuple representation described below. This is made possible 
by the already standardised form in which the data is represented within 
``PyPath``. For more heterogeneous data representations, additional transformations
may be necessary before piping into BioCypher.

Passing the Data
================

In the `pypath example 
<https://github.com/saezlab/pypath/blob/fc4c959c168ce80427189f8dd237308707594ad0/src/pypath/biocypher/adapter.py#L189>`_, 
we are using :py:class:`Generator`-type objects to pass an unordered collection 
of ``PyPath`` contents into BioCypher. For nodes, we are specifying for each object 
an ID and label (corresponding to its unique preferred identifier and its 
ontological class), as well as a dictionary of arbitrary properties, each entry 
as a 3-tuple. For relationships, the same applies, except that we are passing 
two IDs, for source and target entities, which results in a 4-tuple.

Currently, there are two modes of interaction with the graph database 
implemented in BioCypher. The first takes place via the Neo4j python driver,
which is either loaded by BioCypher or passed from the host module. The second
generates CSV files containing node and edge data in a standardised and 
safety-checked format to be used with the ``admin import`` functionality of 
Neo4j. Safety checks are important here because Neo4j does not guarantee 
consistency of the resulting graph when using this feature; on the upside,
this mode of communication is much faster. However, it can only be used when
creating a new graph, not for changing an already existing one.

Communication via the Neo4j Python Driver
=========================================

The BioCypher :ref:`Driver <driver>` is the main submodule of BioCypher. It 
establishes a connection with a running graph database via the 
:class:`neo4j.GraphDatabase.driver`, integrates the funtions of the other 
submodules, and serves as outside interface of BioCypher. The ``Driver`` is 
the main class for interacting with BioCypher in the host module's adapter 
class. It handles authentification and basic database management as well as 
the creation and manipulation of graph entries.

In our example, it is instantiated in the initialisation of the adapter, and 
then called on for :ref:`interacting with a running graph <running>` and for 
exporting a complete database in CSV format for the 
:ref:`Neo4j admin-import feature <admin_import>`. Upon instantiation, it 
automatically assesses the graph database it is connected to (specified using 
the ``db_name`` attribute) regarding whether or not it already contains a 
BioCypher graph, and, if so, what the structure of this graph is.

If there exists no BioCypher graph in the currently active database, or if the
user explicitly specifies so using the ``wipe`` attribute of the driver, a new
BioCypher database is created using the schema configuration specified in the
:ref:`schema-config.yaml <schema-config>`.

.. _running:

Interacting with a running Neo4j instance
=========================================

Once instantiated, the BioCypher driver can be used to modify the current 
graph by adding or deleting nodes, edges, properties, constraints, et cetera.
Most commonly, the methods :meth:`biocypher.driver.Driver.add_nodes()` and 
:meth:`biocypher.driver.Driver.add_edges()` are used to introduce new entries
into the graph database.

.. _admin_import:

Exporting for the `neo4j-admin import` feature
==============================================

Particularly if the data are very extensive (or performance is of the utmost
priority), BioCypher can be used to facilitate a speedy and safe import of the
data using the ``neo4j-admin import`` console command. `Admin Import 
<https://neo4j.com/docs/operations-manual/current/tutorial/neo4j-admin-import/>`_ 
is a particularly fast method of writing data to a newly created graph database
(the database needs to be completely empty) that gains most of its performance
advantage from turning off safety features regarding input data consistency.
Therefore, a sound and consistent representation of the nodes and edges in the 
graph is of high importance in this process, which is why the BioCypher export
functionality has been specifically designed to perform type and content 
checking for all data to be written to the graph.

Data input from the source database is exactly as in the case of `interacting 
with a running database <running>`_, with the data representation being 
converted to a series of CSV files in a designated output folder (standard 
being ``out/`` and the current datetime). BioCypher creates separate header and
data files for all node and edge types to be represented in the graph via the 
driver methods :meth:`biocypher.driver.Driver.write_nodes()` and 
:meth:`biocypher.driver.Driver.write_edges()`. Additionally, it creates a file
called ``neo4j-admin-import-call.txt`` containing the console command for 
creating a new database, which only has to be executed from the directory of 
the currently running Neo4j database.

The name of the database to be created is given by the ``db_name`` attribute
of the driver methods, ie, ``write_nodes()`` and ``write_edges()``, which should 
receive the same name as in the ``PyPath`` adapter example, and can be 
arbitrary. In case the ``db_name`` is not the default Neo4j database name, 
``neo4j``, the database needs to be created in Neo4j before or after using 
the ``neo4j-admin import`` statement. This can be done by executing, in the 
running database (``<db_name>`` being the name assigned in the method):

1. ``:use system``
2. ``create database <db_name>``
3. ``:use <db_name>``

###################
Usage Notes
###################

-  A graph database can be built from any arbitrary collection of biomedical 
   data. We here examplarise the building of a biological prior knowledge graph 
   from the OmniPath database (Türei et al. 2021), but BioCypher includes the 
   extensive translation functionality from ``PyPath`` to accommodate custom 
   requirements for graph database contents.

-  A BioCypher graph has to be instantiated as such from the beginning, an 
   existing property graph cannot currently be "updated" to conform to the 
   BioCypher format.

-  As a first step, an empty Neo4j database has to be created and started; the 
   Python database driver can then be established either through BioCypher 
   directly or on the user's end and passed to BioCypher (if there is greater 
   need for data security in authentication).

-  After the database driver has been passed to BioCypher, a new database can 
   be established given the selected data structure, to be determined in the 
   primary configuration file. In this step, all constraints and indices are 
   set to conform to the selected database structure. These can also be 
   modified afterwards.

   -  Note: if the database to be created is very extensive, BioCypher offers a 
      "secure export" method to create CSV files that can be used to instantiate
      a new graph database very quickly using the `Admin Import 
      <https://neo4j.com/docs/operations-manual/current/tutorial/neo4j-admin-import/>`_
      feature of Neo4j.

-  The database structure and version are recorded in a meta-graph that serves as 
   a versioning system and simultaneously as a means of transmitting information
   about the graph structure for the case of re-loading an existing database for 
   updating it with new information.


##############################
Submodule documentation
##############################

.. _driver:

`driver.py`: the BioCypher Neo4j Driver
=======================================
.. automodule:: biocypher.driver
   :members: 

`check.py`: BioCypher Format Data Representation and Consistency Checks
=======================================================================
.. automodule:: biocypher.check
   :members:

`create.py`: Base Classes for Node and Edge Representations in BioCypher
========================================================================
.. automodule:: biocypher.create
   :members: 

`translate.py`: Translation Functionality for Implemented Types of Representation
=================================================================================
.. automodule:: biocypher.translate
   :members:

`write.py`: Write the Graph to CSV Files for quick 'admin import'
=================================================================
.. automodule:: biocypher.write
   :members:

`logger.py`: Logging
====================
.. automodule:: biocypher.logger
   :members:

###########################
Indices, Tables, and Search
###########################

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. toctree::
   :maxdepth: 4
