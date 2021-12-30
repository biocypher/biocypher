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

import os
from datetime import datetime

from biocypher.translate import BiolinkAdapter
from .logger import get_logger

logger = get_logger(__name__)


class BatchWriter:
    """
    Class for writing node and edge representations to disk using the
    format specified by Neo4j for the use of admin import.
    """

    def __init__(self, schema, bl_adapter, dirname=None) -> None:
        self.delim = ";"
        self.adelim = "|"
        self.quote = "'"
        self.schema = schema
        self.bl_adapter = bl_adapter

        if not dirname:
            now = datetime.now()
            dirname = now.strftime("%Y%m%d%H%M")

        logger.info(f"Trying to crete output folder at out/{dirname}.")
        ROOT = os.path.join(
            *os.path.split(os.path.abspath(os.path.dirname(__file__)))
        )
        self.output_path = ROOT + "/../out/" + dirname + "/"
        try:
            os.mkdir(self.output_path)
            logger.info("Folder created successfully.")
        except FileExistsError:
            logger.error("Output directory already exists; cannot continue.")

    # file handling
    def write_node_headers(self):
        """
        Writes single CSV file for each graph entity that is represented
        as a node as per the definition in the `schema_config.yaml`,
        containing only the header for this type of node.

        Args:
            schema (dict): graph schema as taken from `schema_config.yaml`
                and, equivalently, from `Driver.db_meta.schema`.

        Todo:
            - handling of properties: parse the data or specify in YAML
            - optional labels: parse from YAML hierarchy
        """
        # extract nodes
        nodes = [
            no
            for no in self.schema.items()
            if no[1]["represented_as"] == "node"
        ]

        for no in nodes:
            # create header CSV with ID, properties, labels
            label = no[0]
            props = no[1]
            id = props["preferred_id"] + ":ID"

            # to programmatically define properties to be written, the
            # data would have to be parsed before writing the header.
            # alternatively, desired properties could also be provided
            # via the schema_config.yaml, but that is more effort for
            # the user.

            # for now, substitute test properties: TODO
            props = ["p1", "p2"]
            if len(props) > 1:
                props = self.delim.join(props)

            # multiple labels:
            opt_labels = self.bl_adapter.leaves[label]["ancestors"]

            if opt_labels:
                labels = opt_labels
                # remove prefix
                labels = [l.replace("biolink", "") for l in labels]
                # concatenate with array delimiter
                labels = self.adelim.join(labels)
            else:
                labels = ":" + label

            file_path = self.output_path + label + "-header.csv"
            with open(file_path, "w") as f:
                # concatenate with delimiter
                row = self.delim.join([id, props, labels])
                f.write(row)

    def write_edge_headers(self):
        # extract nodes
        edges = [
            ed
            for ed in self.schema.items()
            if ed[1]["represented_as"] == "edge"
        ]

        for ed in edges:
            # create header CSV with ID, properties, labels
            label = ed[0]
            props = ed[1]
            id = props["preferred_id"]

            # to programmatically define properties to be written, the
            # data would have to be parsed before writing the header.
            # alternatively, desired properties could also be provided
            # via the schema_config.yaml, but that is more effort for
            # the user.

            # for now, substitute test properties: TODO
            props = ["p1", "p2"]
            if len(props) > 1:
                props = self.delim.join(props)

            file_path = self.output_path + label + "-header.csv"
            with open(file_path, "w") as f:
                # concatenate with delimiter
                row = self.delim.join(
                    [":START_ID", id, props, ":END_ID", label]
                )
                f.write(row)


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

There are three mandatory fields for relationship data:
:START_ID — ID refering to a node.
:END_ID — ID refering to a node.
:TYPE — The relationship type.

E.g.: `:START_ID;relationship_id;residue;:END_ID;:TYPE`.

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
