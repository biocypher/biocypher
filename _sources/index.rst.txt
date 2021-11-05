.. BioCypher documentation master file, created by
   sphinx-quickstart on Tue Oct  5 20:09:15 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

################################################################################
BioCypher: a unified language of property graph databases for biomedical science
################################################################################

Introduction
============
BioCypher is designed to serve as guideline and translation mechanism for both the 
creation of property graph databases from primary data as well as for the 
querying of these databases. Our greater aim is to combine the computational 
power of graph databases with the search for answers of our most pressing 
biological questions and facilitate interfacing with cutting edge developments 
in the areas of causal reasoning, representation learning, and natural language 
processing, all of which depend on having a consistent descriptive vocabulary. A 
side objective is the creation of human-readable graph syntax.

A short summary of how BioCypher is supposed to be used:

-  A graph database can be built from any arbitrary collection of biomedical data. 
   We here examplarise the building of a biological prior knowledge graph from the 
   OmniPath database (Türei et al. 2021), but BioCypher includes the extensive 
   translation functionality from PyPath to accommodate custom requirements for 
   graph database contents.

-  A BioCypher graph has to be instantiated as such from the beginning, an existing
   property graph cannot currently be "updated" to conform to the BioCypher format.

-  As a first step, an empty Neo4j database has to be created and started; the 
   Python database driver can then be established either through BioCypher directly
   or on the user's end and passed to BioCypher (if there is greater need for data 
   security in authentication).

-  After the database driver has been passed to BioCypher, a new database can be 
   established given the selected data structure, to be determined in the primary 
   configuration file. In this step, all constraints and indices are set to 
   conform to the selected database structure. These can also be modified afterwards.

   -  Note: if the database to be created is very extensive, BioCypher offers a 
      "secure export" method to create CSV files that can be used to instantiate
      a new graph database very quickly using the `Admin Import 
      <https://neo4j.com/docs/operations-manual/current/tutorial/neo4j-admin-import/>`_
      feature of Neo4j.


-  The database structure and version are recorded in a meta-graph that serves as 
   a versioning system and simultaneously as a means of transmitting information
   about the graph structure for the case of re-loading an existing database for 
   updating it with new information.

Pass a Neo4j driver instance
============================
.. automodule:: biocypher.driver
   :members: 

Check the active database for consistency with the BioCypher format
===================================================================
.. automodule:: biocypher.check
   :members:

Create and update entries in a database
=======================================
.. automodule:: biocypher.create
   :members: 

Translate functionality for implemented types of knowledge
==========================================================
.. automodule:: biocypher.translate
   :members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. toctree::
   :maxdepth: 2
   :caption: Contents: