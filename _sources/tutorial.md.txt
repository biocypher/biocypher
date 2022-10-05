# BioCypher Tutorial - Basics
The main purpose of BioCypher is to facilitate the pre-processing of biomedical
data to save development time in the maintainance of curated knowledge graphs
and to allow the simple and efficient creation of task-specific lightweight
knowledge graphs in a user-friendly and biology-centric fashion.

We are going to use a toy example to familiarise the user with the basic
functionality of BioCypher. One central task of BioCypher is the harmonisation
of dissimilar datasets describing the same entities. Thus, in this example, the
input data - which in the real-world use case could come from any type of
interface - are represented by simulated data containing some examples of
differently formatted biomedical entities such as proteins and their
interactions.

## Section 1: Adding data
The code for this tutorial can be found at `tutorial/01_basic_import.py`. Data
generation happens in `tutorial/data_generator.py`.

### Input data stream ("adapter")
The basic operation of adding data to the knowledge graph requires two
components: an input stream of data (which we call adapter) and a configuration
for the resulting desired output (the schema configuration). The former will be
simulated by calling the `Protein` class of our data generator 10 times. 

```{code-block} python
from data_generator import Protein
proteins = [Protein() for _ in range(10)]
```

Each protein in our simulated data has a UniProt ID, a label
("uniprot_protein"), and a dictionary of properties describing it. This is -
purely by coincidence - very close to the input BioCypher expects (for nodes): 
- a unique identifier 
- an input label (to allow mapping to the ontology, see the second step below)
- a dictionary of further properties (which can be empty)

These should be presented to the BioCypher driver in the form of a tuple. To
achieve this representation, we can use a generator function that iterates
through our simulated input data and, for each entity, forms the corresponding
tuple. The use of a generator allows for efficient streaming of larger datasets
where required.

```{code-block} python
def node_generator():
    for protein in proteins:
        yield (protein.id, protein.label, protein.properties)
```

The concept of an adapter can become arbitrarily complex and involve
programmatic access to databases, API requests, asynchronous queries, context
managers, and other complicating factors. However, it always boils down to
providing the BioCypher driver with a collection of tuples, one for each entity
in the input data. As descibed above, nodes possess a mandatory ID, a mandatory
label, and a property dictionary, while edges possess an (optional) ID, two
mandatory IDs for source and target, a mandatory label, and a property
dictionary. How these entities are mapped to the ontological hierarchy
underlying a BioCypher graph is determined by their mandatory labels, which
connect the input data stream to the schema configuration. This we will see in
the following section.

<!-- Figure for ID, label, prop of nodes and edges? -->

### Schema configuration
How each BioCypher graph is structured is determined by the schema
configuration YAML file that is given to the driver. This also serves to ground
the entities of the graph in the biomedical realm by using an ontological
hierarchy. In this tutorial, we refer to the Biolink model as the general
backbone of our ontological hierarchy. The basic premise of the schema
configuration YAML file is that each component of the desired knowledge graph
output should be configured here; if (and only if) an entity is represented in
the schema configuration *and* is present in the input data stream, it will be
part of our knowledge graph. In our case, since we only import proteins, we
only require few lines of configuration:

```{code-block} yaml
protein:                            # mapping
  represented_as: node              # schema configuration
  preferred_id: uniprot             # uniqueness
  label_in_input: uniprot_protein   # connection to input stream
```

The first line (`protein`) identifies our entity and connects to the
ontological backbone; here we define the first class to be represented in the
graph. In the configuration YAML, we represent entities - similar to the
internal representation of Biolink - in lower sentence case (e.g., "small
molecule"). Conversely, for class names, in file names, and property graph
labels, which use PascalCase instead (e.g., "SmallMolecule") to avoid issues
with handling spaces. The transformation is done by BioCypher internally.
Following this first line are three indented values of the protein class.
BioCypher does not strictly enforce the entities allowed in this class
definition; in fact, we provide several methods of extending the existing
ontological backbone *ad hoc* by providing custom inheritance or hybridising
ontologies. However, every entity should at some point be connected to the
underlying ontology, otherwise the multiple hierarchical labels will not be
populated.

<!-- TODO link to ontology manipulation -->

The second line (`represented_as`) tells BioCypher in which way each entity
should be represented in the graph; the only options are `node` and `edge`.
Representation as an edge is only possible when source and target IDs are
provided in the input data stream.

The third line (`preferred_id`) informs the uniqueness of represented entities
by selecting an ontological namespace around which the definition of uniqueness
should revolve. In our example, if a protein has its own uniprot ID, it is
understood to be a unique entity. When there are multiple protein isoforms
carrying the same uniprot ID, they are understood to be aggregated to result in
only one unique entity in the graph. Decisions around uniqueness of graph
constituents sometimes require some consideration in task-specific
applications. Selection of a namespace also has effects in identifier mapping;
in our case, for protein nodes that do not carry a uniprot ID, identifier
mapping will attempt to find a uniprot ID given the other identifiers of that
node. To account for the broadest possible range of identifier systems while
also dealing with parsing of namespace prefixes and validation, we refer to the
[Bioregistry](https://bioregistry.io) project namespaces, which should be
preferred values for this field.

Finally, the fourth line (`label_in_input`) connects the input data stream to
the configuration; here we indicate which label to expect in the input tuple
for each class in the graph. In our case, we expect "uniprot_protein" as the
label for each protein in the input data stream; all other input entities that
do not carry this label are ignored as long as they are not in the schema
configuration.

### Creating the graph (using the BioCypher driver)
All that remains to be done now is to instantiate the BioCypher driver (as the
main means of communicating with BioCypher) and call the function to create the
graph. While this can be done "online", i.e., by connecting to a running Neo4j
instance, we will in this example use the offline mode of BioCypher, which does
not require setting up a graph database instance. The following code will use
the data stream and configuration set up above to write the files for knowledge
graph creation:

```{code-block} python
import biocypher
driver = biocypher.Driver(
    offline=True,
    user_schema_config_path="tutorial/01_schema_config.yaml",
)
driver.write_nodes(node_generator())
```

We pass our configuration file at driver instantiation, and we pass the data
stream to the `write_nodes` function. The driver will then create the graph and
write it to the output directory, which is set to `biocypher-out/` by default,
creating a subfolder with the current datetime for each driver instance.

### Importing data into Neo4j
The graph can now be imported into Neo4j using the `neo4j-admin` command line
tool. This is not necessary if the graph is created in online mode. For
convenience, BioCypher provides the command line call required to import the
data into Neo4j:

```{code-block} python
driver.write_import_call()
```

This creates an executable shell script in the output directory that can be
executed from the location of the database folder to import the graph into
Neo4j (or copied into the Neo4j terminal). Since BioCypher creates separate
header and data files for each entity type, the import call conveniently
aggregates this information into one command, detailing the location of all
files on disk, so no data need to be copied around.

## Section 2: Merging data
The code for this tutorial can be found at `tutorial/02_merge.py` and
`tutorial/03_implicit_subclass.py`. Data generation happens in
`tutorial/data_generator.py`.

### Plain merge
Using the workflow described above with minor changes, we can merge data from
different input streams. If we do not want to introduce additional ontological
subcategories, we can simply add the new input stream to the existing one and
add the new label to the schema configuration (the new label being
`entrez_protein`). In this case, we would add the following to the schema
configuration:

```{code-block} yaml
protein:
  represented_as: node
  preferred_id: uniprot
  label_in_input: [uniprot_protein, entrez_protein]
```

However, we are generating our `entrez` proteins as having entrez IDs, which 
could result in problems in querying. This issue could be resolved by mapping
the entrez IDs to uniprot IDs, but we will instead use the opportunity to
demonstrate how to merge data from different sources into the same ontological
class using *ad hoc* subclasses.

### Ad hoc subclassing
In the previous section, we saw how to merge data from different sources into
the same ontological class. However, we did not resolve the issue of the
`entrez` proteins living in a different namespace than the `uniprot` proteins,
which could result in problems in querying. In proteins, it would probably be
more appropriate to solve this problem using identifier mapping, but in other
categories, e.g., pathways, this may not be possible because of a lack of
one-to-one mapping between different data sources. Thus, if we so desire, we
can merge datasets into the same ontological class by creating *ad hoc*
subclasses implicitly through BioCypher, by providing multiple preferred
identifiers. In our case, we update our schema configuration as follows:

```{code-block} yaml
protein:
  represented_as: node
  preferred_id: [uniprot, entrez]
  label_in_input: [uniprot_protein, entrez_protein]
```

This will "implicitly" create two subclasses of the `protein` class, which will
inherit the entire hierarchy of the `protein` class. The two subclasses will be
named using a combination of their preferred namespace and the name of the
parent class, separated by a dot, i.e., `uniprot.protein` and `entrez.protein`.
In this manner, they can be identified as proteins regardless of their sources
by any queries for the generic `protein` class, while still carrying
information about their namespace and avoiding identifier conflicts.

```{note}
The only change affected upon the code from the previous section is the 
referral to the updated schema configuration file.
```

```{note}
In the output, we now generate two separate files for the `protein` class, one 
for each subclass (with names in PascalCase). 
```