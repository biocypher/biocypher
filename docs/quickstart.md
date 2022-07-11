# Quickstart

The main interface for interacting with the BioCypher module to create
your own property graph consists of two components:

1. the [host module adapter](host-module-adapter), a python
   program, and
2. the [schema configuration file](schema-config), a YAML file. 

The adapter serves as a data interface between the source and BioCypher,
piping the "raw" data into BioCypher for the creation of the property
graph, while the schema configuration tells BioCypher how the graph
should be structured, detailing the names of constituents and how they
should be connected.

(host-module-adapter)=
## The host module adapter

Currently, BioCypher expects input from the user module via an adapter
module. Throughout the tutorial, we will exemplarise the use of
BioCypher using [OmniPath](https://omnipathdb.org) (more specifically,
its infrastructural backend,
[PyPath](https://github.com/saezlab/pypath)). The adapter has the job of
piping the data as it is represented in the original database into the
BioCypher input, for instance as a {py:class}`Generator` object of
single database entries, whether they be nodes or relationships in the
graph to be created. For more details, please refer to the example
[PyPath adapter](https://github.com/saezlab/pypath/blob/master/pypath/biocypher/adapter.py)
and the section on [adapter functions](adapter_functions).

(schema-config)=
## The schema configuration YAML file

The second important component of translation into a
BioCypher-compatible property graph is the specification of graph
constituents and their mode of representation in the graph. For
instance, we want to add a representation for proteins to the OmniPath
graph, and the proteins should be represented as nodes. To make this
known to the BioCypher module, we use the
[schema-config.yaml](https://github.com/saezlab/BioCypher/blob/main/biocypher/_config/schema_config.yaml),
which details *only* the immediate constituents of the desired graph.
The naming of these constituents must be equal to the ontological
category of the entity in the Biolink schema. The ontological category
(or class) of proteins in Biolink is simply
[Protein](https://biolink.github.io/biolink-model/docs/Protein.html).
However, for more complex concepts, such as - for instance - pairwise
molecular interactions, the naming must also be consistent; in this
case, [PairwiseMolecularInteraction](https://biolink.github.io/biolink-model/docs/PairwiseMolecularInteraction.html).
Similarly, if translation functionality between identifiers is desired,
the identifier used for the class of graph entity must be consistent
with the one used in the Biolink specification. For proteins, this can
be ``UniProtKB`` (but not, for instance, ``UniProt`` or ``uniprot``).
For ease of access, we provide a standard yaml file with the most common
graph constituents and identifiers, with the following basic structure:

```
Protein:
  represented_as: node 
  preferred_id: UniProtKB  
  label_in_input: protein  
```

In the protein case, we are specifying its representation as a node,
that we wish to use the UniProt identifier as the main identifier for
proteins (the Biolink designation for UniProt identifiers is
``UniProtKB``), and that proteins in the input coming from ``PyPath``
carry the label ``protein`` (in lower-case).

The other slots of a graph constituent entry contain information
BioCypher needs to receive the input data correctly and construct the
graph accordingly. For "Named Thing" entities such as the protein, this
includes the mode of representation (YAML entry ``represented_as``),
which can be ``node`` or ``edge``. Proteins can only feasibly
represented as nodes, but for other entities, such as interactions or
aggregates, representation can be both as node or as edge. In Biolink,
these belong to the super-class
[Associations](https://biolink.github.io/biolink-model/docs/associations.html).
For associations, BioCypher additionally requires the specification of
the source and target of the association; for instance, a
post-translational interaction occurs between proteins, so the source
and target attribute in the ``schema-config.yaml`` will both be
``Protein``. Again, these should adhere to the naming scheme of Biolink.

```
PostTranslationalInteraction:
  represented_as: node
  preferred_id: concat_ids
  source: Protein 
  target: Protein 
  label_in_input: post_translational 
```

For the post-translational interaction, which is an association, we are
specifying representation as a node (prompting BioCypher to create not
only the node but also two edges connecting to the proteins
participating in any particular post-translational interaction). In
other words, we are reifying the post-translational interaction in order
to have a node to which other nodes can be linked; for instance, we
might want to add a publication to a particular interaction to serve as
source of evidence, which is only possible for nodes in a property
graph, not for edges.

Since there are no systematic identifiers for post-translational
interactions, we concatenate the protein ids and relevant properties of
the interaction to a new unique id (arbitrarily named ``concat_ids``).
Note that BioCypher accepts non-Biolink IDs since not all possible
entries possess a systematic identifier system, whereas the entity class
(``Protein``, ``PostTranslationalInteraction``) has to be included in
the Biolink schema and spelled identically. For this reason, we [extend
the Biolink schema](biolink) in cases where there exists no entry for
our entity of choice. Further, we are specifying the source and target
classes of our association (both ``Protein``), the label we provide in
the input from ``PyPath`` (``post_translational``). 

If we wanted the interaction to be represented in the graph as an edge,
we would also need to supply an additional - arbitrary - property,
`label_as_edge`, which would be used as the relationship type; this
could for instance be `INTERACTS_POST_TRANSLATIONALLY`, following the
property graph database consensus that property graph edges are
represented in all upper case form and as verbs, to distinguish from
nodes that are represented in PascalCase and as nouns. This would modify
the above example to the following:

```
PostTranslationalInteraction:
  represented_as: edge
  preferred_id: concat_ids
  source: Protein 
  target: Protein 
  label_in_input: post_translational 
  label_as_edge: INTERACTS_POST_TRANSLATIONALLY
```

(biolink)=
## The Biolink model extension

### Soft extensions

In some cases that are not too complex, the Biolink model can be
extended using only implicit subclasses given in the BioCypher
schema_config.yaml file. Soft extensions can be achieved in two ways:
- via [implicit subclasses](implicit) of existing Biolink classes by supplying
  multiple preferred ids and input labels in the `schema_config.yaml`
- via [explicit subclasses](explicit) of existing Biolink classes by supplying an
  `is_a` parameter to any non-biolink class, referring to an existing
  one

(implicit)=
#### Implicit subclasses

For instance, Pathway annotations are supplied by multiple sources,
e.g., [KEGG](https://www.genome.jp/kegg/pathway.html) and
[Reactome](https://reactome.org/), which do not allow direct mapping due
to their distinct make-up. In this case, we can use the
schema_config.yaml to implicitly extend the Biolink model by specifying
more than one preferred_id and label_in_input (in a paired manner):

```
Pathway:
  represented_as: node
  preferred_id: [REACT, KEGG] 
  label_in_input: [reactome, kegg_pathway] 
```

This pattern will be parsed by BioCypher to yield two implicit children
of the Biolink entity "Pathway" by prepending the preferred ID to the
label ("REACT.Pathway" and "KEGG.Pathway"). The input labels again are
arbitrary and can be adjusted to fit the way these pathways are
represented in the raw data.

This will allow both datasets to be represented as pathways in the final
graph with granular access to each one and without information loss, but
will also enable aggregate query of all pathways by calling the parent 
entity, "Pathway".

(explicit)=
#### Explicit subclasses

For example, adding the child `Tissue` to the existing Biolink class
`GrossAnatomicalStructure` as a specification:

```
Tissue:
  is_a: GrossAnatomicalStructure
  represented_as: node
  preferred_id: UBERON
  label_in_input: tissue
```

This will create a "faux" Biolink class at BioCypher runtime, extending
the hierarchical tree to include `Tissue` as a
`GrossAnatomicalStructure`, preserving the entire inheritance of the
parent class.

### Hard-wired extensions

The post-translational interaction that we would like to model in
OmniPath has no literal counterpart in the Biolink model, due to
Biolink's design philosophy. The most granular level of interactions as
Biolink class is the
[PairwiseMolecularInteraction](https://biolink.github.io/biolink-model/docs/PairwiseMolecularInteraction.html);
all more granular relationships should be encoded in the properties of
the class, which has severe performance implications for property graph
representation, for instance in filtering for specific relationship
types. Briefly, it is the difference between being able to selectively
return only relationships of a certain class (eg, post-translational),
and having to return all relationships to filter for the ones possessing
the correct property in a second step.

Therefore, we extend the Biolink model in places where it is necessary
for the BioCypher translation and integration to work. The extended
model is the central Biolink YAML file with additions following the same
[LinkML](https://linkml.io) syntax as is used in the original model.
Depending on the extent of the modification, not only new classes are
introduced, but also new mixin categories (eg, "microRNA or siRNA" to
account for different types of small noncoding RNA). We provide [our
extended version of the Biolink
model](https://github.com/saezlab/BioCypher/blob/main/biocypher/_config/biocypher-biolink-model.yaml)
with the BioCypher repository.

Changes or additions desired by the user can be introduced locally in
this file without having to modify remote contents. Users also have the
option to create their own modified version of the Biolink YAML file
under a different file name and specify that path in the
``custom_yaml_file`` argument of the
{class}`biocypher.translate.BiolinkAdapter` class, which handles all
communication between BioCypher and Biolink.