.. BioCypher documentation master file, created by
   sphinx-quickstart on Tue Oct  5 20:09:15 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

################################################################################
BioCypher: a unified language of property graph databases for biomedical science
################################################################################

Introduction
============
BioCypher shall serve as guideline and translation mechanism for both the 
creation of property graph databases from primary data as well as for the 
querying of these databases. Our greater aim is to combine the computational 
power of graph databases with the search for answers of our most pressing 
biological questions and facilitate interfacing with cutting edge developments 
in the areas of causal reasoning, representation learning, and natural language 
processing, all of which depend on having a consistent descriptive vocabulary.

Pass a Neo4j driver instance
============================
.. automodule:: biocypher.driver_b
   :members: 

Check the active database for consistency with the BioCypher format and return chosen primary identifiers
=========================================================================================================
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