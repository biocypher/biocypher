.. _api-reference:

#############
API Reference
#############

.. _api_core:

The main BioCypher interface
============================

Create a BioCypher instance by running:

.. code-block:: python

   from biocypher import BioCypher
   bc = BioCypher()

Most of the settings should be configured by :ref:`YAML files <config>`. See
below for more information on the BioCypher class.

.. module:: biocypher
.. autosummary::
   :toctree: modules

   BioCypher

.. _api_write:

Database creation by file
=========================

Using the BioCypher instance, you can create a database by writing files by
using the :meth:`BioCypher.write_nodes` and :meth:`BioCypher.write_edges`
methods, which accept collections of nodes and edges either as :ref:`tuples
<tut_01>` or as :class:`BioCypherNode` and :class:`BioCypherEdge` :ref:`objects
<api_create>`. For example:

.. code-block:: python

   # given lists of nodes and edges
   bc.write_nodes(node_list)
   bc.write_edges(edge_list)

.. note::

      To facilitate the interaction with the various database management systems
      (DBMSs), BioCypher provides utility functions, such as writing a Neo4j
      admin import statement to be used for creating a Neo4j database
      (:meth:`BioCypher.write_import_call`). The most commonly used utility
      functions are also available in the wrapper function
      :meth:`BioCypher.summary`. See the :class:`BioCypher` :ref:`class
      <api_core>` for more information.

Details about the :mod:`biocypher._write` module responsible for these methods
can be found below.

.. module:: biocypher._write
.. autosummary::
   :toctree: modules

   get_writer
   _BatchWriter
   _Neo4jBatchWriter
   _PostgreSQLBatchWriter
   _ArangoDBBatchWriter

.. api_pandas:

In-memory Pandas knowledge graph
================================

BioCypher provides a wrapper around the :class:`pandas.DataFrame` class to
facilitate the creation of a knowledge graph in memory. This is useful for
testing, small datasets, and for workflows that should remain purely in Python.
Example usage:

.. code-block:: python

   from biocypher import BioCypher
   bc = BioCypher()
   # given lists of nodes and edges
   bc.add(node_list)
   bc.add(edge_list)
   # show list of dataframes (one per node/edge type)
   dfs = bc.to_df()

Details about the :mod:`biocypher._pandas` module responsible for these methods
can be found below.

.. module:: biocypher._pandas
.. autosummary::
   :toctree: modules

   Pandas

.. _api_connect:

Database creation and manipulation by Driver
============================================

BioCypher also provides a driver for each of the supported DBMSs. The driver can
be used to create a database and to write nodes and edges to it, as well as
allowing more subtle manipulation usually not encountered in creating a database
from scratch as in the :ref:`file-based workflow <api_write>`. This includes
merging (creation of entities only if they don't exist) and deletion. For
example:

.. code-block:: python

   from biocypher import BioCypher
   bc = BioCypher()
   # given lists of nodes and edges
   bc.merge_nodes(node_set_1)
   bc.merge_edges(edge_set_1)
   bc.merge_nodes(node_set_2)
   bc.merge_edges(edge_set_2)

Details about the :mod:`biocypher._connect` module responsible for these methods
can be found below.

.. module:: biocypher._connect
.. autosummary::
   :toctree: modules

   get_driver
   _Neo4jDriver


.. api_get:

Download and cache functionality
================================

BioCypher provides a download and cache functionality for resources. Resources
are defined via the ``Resource`` class, which have a name, a (set of) URL(s),
and a lifetime (in days, set to 0 for infinite). The ``Downloader`` can deal
with single and lists of files, compressed files, and directories (which needs
to be indicated using the ``is_dir`` parameter of the resource). It uses `Pooch
<https://www.fatiando.org/pooch/latest/>`_ under the hood to handle the
downloads. Example usage:

.. code-block:: python

   from biocypher import BioCypher, Resource
   bc = BioCypher()

   resource1 = Resource(
      name="file_list_resource",
      url_s=[
         "https://example.com/resource1.txt"
         "https://example.com/resource2.txt"
      ],
      lifetime=1
   )
   resource2 = Resource(
      name="zipped_resource",
      url_s="https://example.com/resource3.zip",
      lifetime=7
   )
   resource3 = Resource(
      name="directory_resource",
      url_s="https://example.com/resource4/",
      lifetime=7,
      is_dir=True,
   )
   paths = bc.download(resource_list)

The files will be stored in the cache directory, in subfolders according to the
names of the resources, and additionally determined by Pooch (e.g. extraction).
All paths of downloaded files are returned by the ``download`` method. The
``Downloader`` class can also be used directly, without the BioCypher instance.
You can set the cache directory in the configuration file; if not set, it will
use the ``TemporaryDirectory.name()`` method from the ``tempfile`` module. More
details about the ``Resource`` and ``Downloader`` classes can be found below.

.. module:: biocypher._get
.. autosummary::
   :toctree: modules

   Resource
   Downloader

Ontology ingestion, parsing, and manipulation
=============================================
.. module:: biocypher._ontology
.. autosummary::
   :toctree: modules

   Ontology
   OntologyAdapter

Mapping of data inputs to KG ontology
=====================================
.. module:: biocypher._mapping
.. autosummary::
   :toctree: modules

   OntologyMapping

.. _api_create:

Base classes for node and edge representations in BioCypher
===========================================================
.. module:: biocypher._create
.. autosummary::
   :toctree: modules

   BioCypherNode
   BioCypherEdge
   BioCypherRelAsNode

Translation functionality for implemented types of representation
=================================================================
.. module:: biocypher._translate
.. autosummary::
   :toctree: modules

   Translator

Logging
=======
.. module:: biocypher._logger
.. autosummary::
   :toctree: modules

   get_logger

Miscellaneous utility functions
===============================
.. module:: biocypher._misc
.. autosummary::
   :toctree: modules

   to_list
   ensure_iterable
   create_tree_visualisation
   from_pascal
   pascalcase_to_sentencecase
   snakecase_to_sentencecase
   sentencecase_to_snakecase
   sentencecase_to_pascalcase
