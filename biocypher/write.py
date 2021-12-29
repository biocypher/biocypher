#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles the configuration and disk writing of CSV files 
intended for use with the Neo4J admin import function, to quickly 
transfer large amounts of content into an unused database. For more 
explanation, see https://neo4j.com/docs/operations-manual/current/tuto\
rial/neo4j-admin-import/. This module is part of the BioCypher python 
package, homepage: TODO.


Copyright 2021, Heidelberg University Clinic

File author(s): Sebastian Lobentanzer
                ...

Distributed under GPLv3 license, see LICENSE.txt.
"""

"""
1. Collect representations of any type of node and edge in the python 
objects.
2. Coordinate representation to optimise number of CSVs to be written.
    - Depends on mutual information (properties are explicitly stated
        in the CSV header)
    - Also depends on performance (maybe), with very large collections
    - Can properties the node/relationship does not own be left blank?

Formatting: --delimiter=";"
            --array-delimiter="|"
            --quote="'"

The header contains information for each field, for ID and properties
in the format <name>: <field_type>. E.g.: 
´UniProtKB:ID;genesymbol;entrez_id:int;:LABEL´. Multiple labels can 
be given by separating with the array delimiter.

Headers would best be separate files, data files with similar name but
different ending. Example from Neo4j documentation:

bin/neo4j-admin import --database=neo4j 
--nodes=import/entities-header.csv,import/entities-part1.csv,
    import/entities-part2.csv 
--nodes=import/interactions-header.csv,import/interactions-part1.csv,
    import/interaction-part2.csv 
--relationships=import/rels-header.csv,import/rels-part1.csv,
    import/rels-part2.csv

Can use regex, e.g., [..] import/rels-part*. In this case, use padding 
for ordering of the earlier part files ("01, 02").
"""


"""
# collect database information

types of nodes: which nodes require separate representation, how many
    types are there?

types of edges: similarly

"""

"""
# write files

one header for each type of node and edge
    parse through database content OR 
    get info from dedicated output

split data into parts
    write from stream, generator?
    create a chunk of certain size in python, then write using
        with open('part.csv', 'x') as file:
            file.write(chunk)

    size of parts, csv 1M lines? (arbitrary)

"""

"""
# import

1. stop the db

2. shell command:
bin/neo4j-admin import --database=neo4j
# nodes per type, separate header, regex for parts:
    --nodes="<path>/<node_type>-header.csv,<path>/<node_type>-part.*"
# edges per type, separate header, regex for parts:
    --relationships="<path>/<edge_type>-header.csv,<path>/<edge_type>-part.*"

3. start db, test for consistency
"""
