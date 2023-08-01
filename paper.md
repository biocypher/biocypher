---
title: "Democratizing knowledge representation with BioCypher"
tags:
  - Bioinformatics
  - Knowledge Representation
  - Computational Biology
  - Software
authors:
  - name: Sebastian Lobentanzer
    affiliation: [1]
    corresponding: true
  - name: Patrick Aloy
    affiliation: [2, 3]
  - name: Jan Baumbach
    affiliation: [4]
  - name: Balazs Bohar
    affiliation: [5, 6]
  - name: Vincent J. Carey
    affiliation: [7]
  - name: Pornpimol Charoentong
    affiliation: [8, 9]
  - name: Katharina Danhauser
    affiliation: [10]
  - name: Tunca Doğan
    affiliation: [11, 12]
  - name: Johann Dreo
    affiliation: [13, 14]
  - name: Ian Dunham
    affiliation: [15, 16]
  - name: Elias Farr
    affiliation: [1]
  - name: Adrià Fernandez-Torras
    affiliation: [2]
  - name: Benjamin M. Gyori
    affiliation: [17]
  - name: Michael Hartung
    affiliation: [4]
  - name: Charles Tapley Hoyt
    affiliation: [17]
  - name: Christoph Klein
    affiliation: [10]
  - name: Tamas Korcsmaros
    affiliation: [5, 18, 19]
  - name: Andreas Maier
    affiliation: [4]
  - name: Matthias Mann
    affiliation: [20, 21]
  - name: David Ochoa
    affiliation: [15, 16]
  - name: Elena Pareja-Lorente
    affiliation: [2]
  - name: Ferdinand Popp
    affiliation: [22]
  - name: Martin Preusse
    affiliation: [23]
  - name: Niklas Probul
    affiliation: [4]
  - name: Benno Schwikowski
    affiliation: [13]
  - name: Bünyamin Sen
    affiliation: [11, 12]
  - name: Maximilian T. Strauss
    affiliation: [20]
  - name: Denes Turei
    affiliation: [1]
  - name: Erva Ulusoy
    affiliation: [11, 12]
  - name: Dagmar Waltemath
    affiliation: [24]
  - name: Judith A. H. Wodke
    affiliation: [24]
  - name: Julio Saez-Rodriguez
    affiliation: [1]
    corresponding: true
affiliations:
  - name: Heidelberg University, Faculty of Medicine, and Heidelberg University Hospital, Institute for Computational Biomedicine, Bioquant
    index: 1
  - name: Institute for Research in Biomedicine (IRB Barcelona), the Barcelona Institute of Science and Technology
    index: 2
  - name: Institució Catalana de Recerca i Estudis Avançats (ICREA)
    index: 3
  - name: Institute for Computational Systems Biology, University of Hamburg, Germany
    index: 4
  - name: Earlham Institute, Norwich, UK
    index: 5
  - name: Biological Research Centre, Szeged, Hungary
    index: 6
  - name: Channing Division of Network Medicine, Mass General Brigham, Harvard Medical School, Boston, USA
    index: 7
  - name: Centre for Quantitative Analysis of Molecular and Cellular Biosystems (Bioquant), Heidelberg University
    index: 8
  - name: Department of Medical Oncology, National Centre for Tumour Diseases (NCT), Heidelberg University Hospital (UKHD)
    index: 9
  - name: Department of Pediatrics, Dr. von Hauner Children’s Hospital, University Hospital, LMU Munich, Germany
    index: 10
  - name: Biological Data Science Lab, Department of Computer Engineering, Hacettepe University, Ankara, Turkey
    index: 11
  - name: Department of Bioinformatics, Graduate School of Health Sciences, Hacettepe University, Ankara, Turkey
    index: 12
  - name: Computational Systems Biomedicine Lab, Department of Computational Biology, Institut Pasteur, Université Paris Cité, Paris, France
    index: 13
  - name: Bioinformatics and Biostatistics Hub, Institut Pasteur, Université Paris Cité, Paris, France
    index: 14
  - name: European Molecular Biology Laboratory, European Bioinformatics Institute (EMBL-EBI), Wellcome Genome Campus, Hinxton, Cambridgeshire CB10 1SD, UK
    index: 15
  - name: Open Targets, Wellcome Genome Campus, Hinxton, Cambridgeshire CB10 1SD, UK
    index: 16
  - name: Laboratory of Systems Pharmacology, Harvard Medical School, Boston, USA
    index: 17
  - name: Imperial College London, London, UK
    index: 18
  - name: Quadram Institute Bioscience, Norwich, UK
    index: 19
  - name: Proteomics Program, Novo Nordisk Foundation Centre for Protein Research, University of Copenhagen, Copenhagen, Denmark
    index: 20
  - name: Department of Proteomics and Signal Transduction, Max Planck Institute of Biochemistry, Martinsried, Germany
    index: 21
  - name: Applied Tumour Immunity Clinical Cooperation Unit, National Centre for Tumour Diseases (NCT), German Cancer Research Centre (DKFZ), Im Neuenheimer Feld 460, 69120, Heidelberg, Germany
    index: 22
date: 2023-06-19
paper_url: https://doi.org/10.1038/s41587-023-01848-y

---

# Statement of need

Building a knowledge graph for biomedical tasks usually takes months or years,
often requiring a team of experts in knowledge representation, ontology
engineering, and software development. This is a major bottleneck for
biomedical research, as it prevents researchers from quickly building
knowledge graphs for their specific research questions. We propose BioCypher,
a knowledge graph construction tool that democratises knowledge representation
by enabling biomedical researchers to build knowledge graphs more easily.

# Summary

BioCypher is an open-source Python framework built around the concept of a
“threefold modularity”: modularity of data sources, modularity of
structure-giving ontology, and modularity of output formats. This design allows
for a high degree of flexibility and reusability, rationalising efforts by
leveraging the biomedical community.

# References

For all references, see the [paper](https://doi.org/10.1038/s41587-023-01848-y).
