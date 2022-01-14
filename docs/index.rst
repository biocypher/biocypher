.. BioCypher documentation master file, created by
   sphinx-quickstart on Tue Oct  5 20:09:15 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

################################################################################
Introduction
################################################################################

BioCypher is designed to serve as guideline and translation mechanism for both 
the creation of property graph databases from primary data as well as for the 
querying of these databases. The purpose is to combine the computational 
power of graph databases with the search for answers of our most pressing 
biological questions and facilitate interfacing with cutting edge developments 
in the areas of causal reasoning, representation learning, and natural language 
processing, all of which depend on having a consistent descriptive vocabulary.
To achieve meaningful automatic representations in the biomedical language 
space, we include the `Biolink model <https://biolink.github.io/biolink-model/>`_ 
as underlying hierarchical ontology, supplying identification, filtering, and 
mapping capabilities. A side objective is the creation of human-readable graph 
syntax.

##########
Quickstart
##########

The main interface for interacting with the BioCypher module to create your 
own property graph consists of two components:

   1. the :ref:`host module adapter <host-module-adapter>`, a python program, and
   2. the :ref:`schema configuration file <schema-config>`, a YAML file. 

The adapter serves as a data interface between the source and BioCypher, piping
the "raw" data into BioCypher for the creation of the property graph, while the
schema configuration tells BioCypher how the graph should be structured,
detailing the names of constituents and how they should be connected.

.. _host-module-adapter:

The host module adapter
=======================

Currently, BioCypher expects input from the user module via an adapter module.
Throughout the tutorial, we will exemplarise the use of BioCypher using 
OmniPath (more specifically, its infrastructural backend, PyPath). The adapter
has the job of piping the data as it is represented in the original database
into the BioCypher input, for instance as a :py:class:`Generator` object of 
single database entries, whether they be nodes or relationships in the graph
to be created. For more details, please refer to the example `PyPath adapter 
<https://github.com/saezlab/pypath/blob/master/src/pypath/biocypher/adapter.py>`_ 
and the section on adapter functions.

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
used in the Biolink specification. For proteins, this can be `UniProtKB`
(but not, for instance, `UniProt` or `uniprot`). For ease of access, we provide 
a standard yaml file with the most common graph constituents and identifiers.

The other slots of a graph constituent entry contain information BioCypher
needs to receive the input data correctly and construct the graph accordingly.
For "Named Thing" entities such as the protein, this includes the mode of 
representation (YAML entry `represented_as`), which can be `node` or `edge`. 
Proteins can only feasibly represented as nodes, but for other entities, such 
as interactions or aggregates, representation can be both as node or as edge. 
In Biolink, these belong to the super-class 
`Associations <https://biolink.github.io/biolink-model/docs/associations.html>`_.
For associations, BioCypher additionally requires the specification of the 
source and target of the association; for instance, a post-translational 
interaction occurs between proteins, so the source and target attribute in the 
`schema-config.yaml` will both be `Protein`. Again, these should adhere to the
naming scheme of Biolink. Following are two examples of `schema-config.yaml` 
entries, one for a "Named Thing", the protein, and one for an association, the 
post-translational interaction.

   Protein: 

      represented_as: node 
   
      preferred_id: UniProtKB  
   
      label_in_input: protein  

In the protein case, we are specifying its representation as a node, that we 
wish to use the UniProt identifier as the main identifier for proteins (the
Biolink designation for UniProt identifiers is `UniProtKB`), and that proteins
in the input coming from pypath carry the label `protein` (in lower-case).

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
particular post-translational interaction). Since there are no systematic 
identifiers for post-translational interactions, we concatenate the protein
ids and relevant properties of the interaction to a new unique id 
(`concat_ids`). Note that BioCypher accepts non-Biolink IDs since not all 
possible entries possess a systematic identifier system, whereas the entity 
class (`Protein`, `PostTranslationalInteraction`) has to be included in the 
Biolink schema and spelled identically. For this reason, we extend the 
Biolink schema in cases where there exists no entry for our entity of choice.

Further, we are specifying the source and target classes of our association
(both `Protein`), the label we provide in the input from pypath 
(`post_translational`), and - optionally - the label we would want the edge
in the graph to carry would the association be represented as an edge. This 
has no bearing on the current example, where we choose representation as a 
node, but is important for edge representation, as by consensus, property
graph edges are represented in all upper case form and as verbs, to distinguish
from nodes that are represented in PascalCase and as nouns.

###################
The Adapter
###################

###################
Usage Notes
###################

-  A graph database can be built from any arbitrary collection of biomedical 
   data. We here examplarise the building of a biological prior knowledge graph 
   from the OmniPath database (Türei et al. 2021), but BioCypher includes the 
   extensive translation functionality from PyPath to accommodate custom 
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

Write the graph to CSV files for quick 'admin import'
=====================================================
.. automodule:: biocypher.write
   :members:

Logging
=======
.. automodule:: biocypher.logger
   :members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. toctree::
   :maxdepth: 2
   :caption: Contents: