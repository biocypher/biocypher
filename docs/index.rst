.. image:: banner.png

############
Introduction
############

Building a knowledge graph for biomedical tasks usually takes months or years.
What if you could do it in weeks or days? We created BioCypher to make the
process of creating a biomedical knowledge graph easier than ever, but still
flexible and transparent. BioCypher is built around the concept of a "trifold
modularity": modularity of data sources, modularity of structure-giving
ontology, and modularity of output formats (see the Figure below). This design
allows for a high degree of flexibility and reusability, rationalising efforts
by leveraging the biomedical community.

.. grid:: 4
   :gutter: 2 2 3 4

   .. grid-item-card::
      :link: https://github.com/saezlab/BioCypher
      :text-align: center

      On GitHub:

      :octicon:`mark-github;3em`

   .. grid-item-card::
      :link: https://arxiv.org/abs/2212.13543
      :text-align: center

      The paper:

      :octicon:`book;3em`

   .. grid-item-card::
      :link: https://biocypher.zulipchat.com/
      :text-align: center

      Get in touch:

      :octicon:`comment-discussion;3em`

   .. grid-item-card::
      :link: https://github.com/orgs/saezlab/projects/5/views/6
      :text-align: center

      Our adapters:

      :octicon:`project;3em`

On this page, you will find technical documentation, user experience reports
(soon), tutorials, and other resources for BioCypher. You can read our paper on
`arXiv <https://arxiv.org/abs/2212.13543>`_. We are an inclusive community and
welcome contributions and questions from everyone; see below for further links.

.. Note::

   BioCypher is an inclusive community-driven project. If you have any
   questions, specific needs, or want to contribute to the project, please
   contact us over on our `Zulip channel <https://biocypher.zulipchat.com/>`_,
   on `GitHub <https://github.com/saezlab/BioCypher>`_ or via email at
   sebastian.lobentanzer (at) uni-heidelberg.de.

.. figure:: ../graphical_abstract.png
   :width: 70%
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


.. _adapters:

########
Adapters
########

.. note:: Adapters overview
   We collect an overview of adapters for resources, ontologies, and output
   formats in several `BioCypher GitHub projects views
   <https://github.com/orgs/saezlab/projects/5/views/6>`_.

BioCypher is a modular framework, with the main purpose of avoiding redundant
maintenance work for maintainers of secondary resources and end users alike. To
achieve this, we use a collection of reusable “adapters” for the different
sources of biomedical knowledge as well as for different ontologies. To see
whether your favourite resource is already supported or currently in
development, or if you would like to contribute to the development of a new
adapter, please refer to `this GitHub projects view
<https://github.com/orgs/saezlab/projects/5/views/6>`_. Check the tabs for
different views.

.. warning::
   We are currently working on adapter documentation, so the collection in the
   GitHub Projects view may be less than complete.

The project view is built from issues in the `BioCypher GitHub repository
<https://github.com/saezlab/BioCypher/issues>`_, which carry labels for adapters
and adapter subtypes, as well as an ``Adapter status`` label to indicate the
state of development: ``Planned``, ``In progress``, ``Existing``, and ``Ideas``.
If you would like to add or request an adapter that is not yet listed, please
open a new issue (ideally with an ``adapter`` label) and we will add it to the
project view.
