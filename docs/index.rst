.. image:: banner.png

############
Introduction
############

Building a knowledge graph for biomedical tasks usually takes months or years.
What if you could do it in weeks or days? We created BioCypher to make the
process of creating a biomedical knowledge graph easier than ever, but still
flexible and transparent. BioCypher is built around the concept of a "trifold
modularity": modularity of data sources, modularity of structure-giving
ontology, and modularity of output formats (see the graphical abstract below).
This design allows for a high degree of flexibility and reusability,
rationalising efforts by leveraging the biomedical community.

.. grid:: 2
   :gutter: 2

   .. grid-item-card:: Find us on GitHub
      :link: https://github.com/saezlab/BioCypher
      :text-align: center

      :octicon:`mark-github;3em` :octicon:`repo;3em`

   .. grid-item-card:: Read the paper
      :link: https://arxiv.org/abs/2212.13543
      :text-align: center

      :octicon:`book;3em` :octicon:`light-bulb;3em`

   .. grid-item-card:: Get in touch
      :link: https://biocypher.zulipchat.com/
      :text-align: center

      :octicon:`people;3em` :octicon:`comment-discussion;3em`

   .. grid-item-card:: Check out our adapters
      :link: https://github.com/orgs/saezlab/projects/5/views/6
      :text-align: center

      :octicon:`plug;3em` :octicon:`project;3em`

.. Note::

   BioCypher is an inclusive community-driven project. If you have any
   questions, specific needs, or want to contribute to the project, please
   contact us over on our `Zulip channel <https://biocypher.zulipchat.com/>`_,
   on `GitHub <https://github.com/saezlab/BioCypher>`_ or via email at
   sebastian.lobentanzer (at) uni-heidelberg.de.

.. figure:: ../graphical_abstract.png
   :width: 95%
   :align: center
   :alt: BioCypher graphical abstract

   BioCypher uses a collection of reusable “adapters” for the different sources
   of biomedical knowledge, which can be flexibly recombined to fit various
   demands, thus reducing redundant maintenance work through
   quasi-standardisation.  Integrating the controlled vocabularies of ontologies
   into the process helps to harmonise the data from individual resources and
   yields a consistent semantic basis for downstream analyses. Through
   unambiguous and simple “low-code” configuration, a reproducible knowledge
   graph can be created and shared for every specific task.
