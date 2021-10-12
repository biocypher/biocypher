# BioCypher
This is the development repository for BioCypher, our proposal for a [unified language of property graph databases for systems biology](unified-language-of-biological-property-graph-database-systems.md). It shall serve as guideline and translation mechanism for both the creation of property graph databases from primary data as well as for the querying of these databases. Our greater aim is to combine the computational power of graph databases with the search for answers of our most pressing biological questions and facilitate interfacing with cutting edge developments in the areas of causal reasoning, representation learning, and natural language processing, all of which depend on having a consistent descriptive vocabulary.

Ideally, BioCypher would enable "plug-and-play" functionality between participating database systems, ie, arbitrary transfer of input or output from one database to the other, and hybrid property graphs made up of subsets of different databases for specific purposes. We strive for being compliant with the [openCypher](https://opencypher.org/) project. Technically, BioCypher will be implemented as a python module, enforcing consensus nomenclature and graph structure in creation of databases while providing translation facilities between identifier systems.

![BioCypher](BioCypher.png)

## Usage
BioCypher is currently in prototype stage. To use it locally, please install it into a python environment from the cloned repo. After activating the environment and changing to a folder of your choice, do:

```
git clone https://github.com/saezlab/BioCypher.git
cd BioCypher
python setup.py install
```
