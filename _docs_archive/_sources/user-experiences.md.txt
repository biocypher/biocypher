![BioCypher Open Graph](biocypher-open-graph.png)
# User Experiences
To give an overview of the capabilities of the framework and possible use cases,
we have collected a number of user experiences from the community. The two major
categories of BioCypher usage are (1) creation and maintenance of knowledge
repositories ("storage") and (2) project-specific knowledge graph creation
("analysis").

## A Knowledge Graph for Impact of Genomic Variation on Function (IGVF)


:::{card} Impact of Genomic Variation on Function (IGVF)
:link: https://www.igvf.org/

The Impact of Genomic Variation on Function (IGVF) project aims to provide a
comprehensive and integrated view of the impact of genomic variation on human
health and disease.

:::

```{admonition} Testimonial
:class: hint

Our project, Impact of Genomic Variation on Function (IGVF, https://igvf.org),
is building a massive biological knowledge graph to attempt to link human
variation and disease with genomic datasets at the single-cell level. We are
creating a user-facing API (and eventually UI) that will access this graph.
BioCypher, which acts as an intermediary between Biolink and graph databases (we
are using ArangoDB) has been instrumental in helping us design the schema and
move our project forward. Specifically, it provides a framework we can use to
parse the dozens of data files and formats into a Biolink-inspired schema.

&mdash; Ben Hitz, Director of Genomics Data Resources, Project Manager ENCODE,
Stanford University

```

The BioCypher pipeline used to build the knowledge graph uses several adapters
for genetics data sources; an overview is available in our
[meta-graph](metagraph) and on the [GitHub Components
Board](https://github.com/orgs/biocypher/projects/3) (pipelines column). The
pipeline boasts a Docker Compose workflow that builds the graph and the API
(using [tRPC](https://trpc.io/)), and is available on
[GitHub](https://github.com/IGVF-DACC/igvf-catalog).

## Drug Repurposing with CROssBAR

:::{card} CROssBAR
:link: https://crossbar.kansil.org/

CROssBAR is a biomedical data integration and representation project. CROssBAR
knowledge graphs incorporate relevant genes-proteins, molecular interactions,
pathways, phenotypes, diseases, as well as known/predicted drugs and bioactive
compounds, and they are constructed on-the-fly based on simple non-programmatic
user queries.

:::

```{admonition} Testimonial
:class: hint

We built CROssBAR v1 on NoSQL since property graph databases were quite new at
the time and there was no framework to help us establish the system. We used an
available NoSQL solution to house different layers of biological/biomedical data
as independent collections. CROssBAR’s “small-scale knowledge graph (KG)
construction module” queries each collection separately, collects the data, and
merges the data points according to their mappings (which are held in the
database as well, as cross-references), eliminates redundancy, queries each and
every collection again with the entries retrieved in the previous step, and
repeats all subsequent steps. Given that user queries can start with a single or
multiple genes/proteins, compounds/drugs, diseases, phenotypes, pathways, or any
combination of those, this procedure gets extremely complicated, requiring an
average of 64 NoSQL queries to construct one single user-specific KG. The total
number of lines of code required for this procedure alone is around 8000.
This task could have been achieved significantly faster and more efficiently
if we had had BioCypher five years ago.

&mdash; Tunca Doğan, Department of Computer Engineering and Artificial Intelligence
Engineering, Hacettepe University and Protein Function Development Team (UniProt
database), European Molecular Biology Laboratory, European Bioinformatics
Institute (EMBL-EBI)

```

Using BioCypher, CROssBAR v2 will be a flexible property graph database
comprised of single input adapters for each data source. As above, you can see
its current state in the [meta-graph](metagraph) and on the [GitHub Components
Board](https://github.com/orgs/biocypher/projects/3) (pipelines column).

## Builing a Knowledge Graph for Contextualised Metabolic-Enzymatic Interactions


:::{card} metalinks
:link: https://github.com/biocypher/metalinks

The metalinks project aims to build a knowledge graph for contextualised
metabolic-enzymatic interactions.

:::

```{admonition} Testimonial
:class: hint

In the metalinks project, we build a knowledge graph (KG) that incorporates
attributes of metabolites, proteins and their interactions to ultimately study
cell-cell communication. We use two types of interaction between metabolites and
proteins, I) production and degradation of metabolites by enzymes and II)
interaction of metabolites with protein receptors. During the KG assembly we
access multiple databases that provide information in diverse formats. BioCypher
takes all of these inputs, gives them a reasonable, reproducible structure, and
facilitates proper versioning. The KG produced by BioCypher can be easily
contextualized to biological questions aiming for specific tissues, diseases or
metabolite properties, which facilitates downstream analysis and
interpretability. While spending 2.5 months to create a loose collection of
scripts and directories for the initial project, I was able to obtain a
structured result with BioCypher within 2 weeks.

&mdash; Elias Farr, Institute for Computational Biomedicine, University Hospital
Heidelberg

```

The BioCypher pipeline used to build the knowledge graph uses several adapters,
some of which overlap with the CROssBAR project, which helps synergising
maintenance efforts. An overview is available in our
[meta-graph](metagraph) and on the [GitHub Components
Board](https://github.com/orgs/biocypher/projects/3) (pipelines column).
