# A unified language of biological property graph database systems
### Working title: BioCypher

Property graph databases are naturally suited to represent biological data because they are inherently parsimonious in both the usage of space and the computation of complex relationships in the relatively sparse interactome of biological entities. The following outlines a unified language that can aid in large collaboration efforts based on the creation and analysis of biological property graphs.

Any biological entity that can be queried is assigned a unique consensus ID (using the system with least data loss, ie, highest coverage) and a fixed type (corresponding to the "label" in the Neo4j system, ie, the node type indicated after a colon, such as ":Protein"). Edges between entities have a source and target ID (using the same consensus ID system) and a fixed type (such as ":PHOSPHORYLATES").

All other properties of nodes and edges are optional and can have any data type, and thus should be standardised as well to facilitate interaction between the different purpose-specific applications (eg, DepMap, CROssBAR, OmniPath). The easiest way to implement this is to funnel the database creation through a translation interface, such as a python module, that accepts input from any third-party resource, including custom annotation for new or in-house datasets, and outputs a standardised data format for the property graph database (currently implemented in "OmniPath_future" as a pilot interface of "NodeFromPypath" and "EdgeFromPypath").

Further specification will probably be needed for standard situations of graph queries. If the above specifications are a "vocabulary" of biological property graph representation, the queries used can be seen as the "grammar". Together, they make up the language of property graph biological representation.

There are simple "sentences", such as finding targets of a certain set of nodes, or an intersection between perturbed pathways, and complex "sentences", such as an aggregate score of context-dependent multiple interactions or activities of protein complexes comprised of several context-dependent obligate and optional members. Particularly in the complex case, ad-hoc generation of non-permanent virtual relationships inside the graph are preferable to hard-coded information for all possible situations and queries. This is the case in which a unified grammar of biological property graphs is of most value, because it provides methodological uniformity and allows comparison and benchmarking of complex queries.

The common language should provide the following features:
- Vocabulary:
	- consensus organisation of IDs and labels
	- consensus database constraints on unique entities
	- translation of any biological input to the consensus format
- Grammar:
	- consensus grammar for biological queries of any complexity
- Convenience:
	- automated web scraping of resources for periodic updating workflows via one-command interface
	- translation facilities to interface with **natural language queries** from non-bioinformatian researchers and clinicians

## Node types
- DNA: genes, variants, methylation
- RNA: coding transcripts, small and large non-coding RNA
- Protein: proteins, phosphoproteins, transcription factors, enzymes, protein complexes
- Small molecule: drugs, non-drug chemical compounds, substances, oligonucleotides
- Annotation: resource, ontological
- Super-cellular: cell lines, tissues, in vivo, clinical

## Interaction types
- Transcriptional
	- Methylation
	- Chromatin accessibility
	- TF-gene
	- ncRNA-gene
- Post-transcriptional
	- Splicing
	- ncRNA-transcript
	- Oligonucleotide drugs
- Post-translational
	- Protein-protein
	- Complex-protein
	- Different types
	- Ligand interaction: endogenous and drugs, assays
- Super-cellular
	- Tissue interactions
