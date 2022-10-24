.. image:: biocypher-open-graph.png

############
Introduction
############

BioCypher (`GitHub <https://github.com/saezlab/BioCypher>`_) is designed
to serve as guideline and translation mechanism for both the creation of
biomedical property graph databases from primary data as well as for the
seamless integration, optimisation, and querying of these databases. The
purpose is to combine the computational power of graph databases with
the search for answers of our most pressing biological questions and
facilitate interfacing with cutting edge developments in the areas of
causal reasoning, representation learning, and natural language
processing, all of which depend on having a consistent descriptive
vocabulary. To achieve meaningful automatic representations in the
biomedical language space, we include the `Biolink model
<https://biolink.github.io/biolink-model/>`_ as underlying hierarchical
ontology, supplying identification, filtering, and mapping capabilities.
We are also keeping an open mind about adding alternative ontological
systems using an opt-in philosophy. Side objectives are the creation of
human-readable graph syntax and facilitating ultra-rapid graph creation
through the Neo4j admin-import feature.

.. Caution::

   BioCypher is currently in prototype state; we are working on a
   full-featured implementation for the migration of OmniPath at the
   moment. Functionality regarding the translation between different
   database formats and identifiers therefore is rudimentary or
   non-existent as of now.
