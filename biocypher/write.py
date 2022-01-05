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
from collections import OrderedDict
from types import GeneratorType
from collections import defaultdict

from .logger import get_logger
from .create import BioCypherEdge, BioCypherNode

logger = get_logger(__name__)
logger.debug(f"Loading module {__name__}.")


class BatchWriter:
    """
    Class for writing node and edge representations to disk using the
    format specified by Neo4j for the use of admin import. Each batch
    writer instance has a fixed representation that needs to be passed
    at instantiation via the :py:attr:`schema` argument. The instance
    also expects a biolink adapter via :py:attr:`bl_adapter` to be able
    to convert and extend the hierarchy.

    Args:
        schema (dict): dictionary detailing the BioCypher graph schema
            (from :py:class:`VersionNode`)
        bl_adapter (BiolinkAdapter): instance of
            :py:class:`BiolinkAdapter` to enable translation and
            ontology queries
    """

    def __init__(self, schema, bl_adapter, dirname=None) -> None:
        """ """
        self.delim = ";"
        self.adelim = "|"
        self.quote = "'"
        self.schema = schema
        self.bl_adapter = bl_adapter
        self.property_dict = None

        if not dirname:
            now = datetime.now()
            dirname = now.strftime("%Y%m%d%H%M")

        logger.info(f"Trying to create output folder at out/{dirname}.")
        ROOT = os.path.join(
            *os.path.split(
                os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
            )
        )
        self.output_path = ROOT + "/out/" + dirname + "/"
        try:
            os.mkdir(self.output_path)
            logger.info("Folder created successfully.")
        except FileExistsError:
            logger.error("Output directory already exists; cannot continue.")

    def write_nodes(self, nodes, batch_size=int(1e6)):
        """
        Wrapper for writing nodes and headers.

        Args:
            nodes (BioCypherNode): a list or generator of nodes in
                :py:class:`BioCypherNode` format

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        # TODO check represented_as

        # write node data
        passed = self._write_node_data(nodes, batch_size)
        if not passed:
            logger.error("Error while writing node data.")
            return False
        # pass property data to header writer per node type written
        passed = self._write_node_headers()
        if not passed:
            logger.error("Error while writing node headers.")
            return False

        return True

    def write_edges(self, edges):
        pass

    def _write_node_data(self, nodes, batch_size):
        """
        Writes biocypher nodes to CSV conforming to the headers created
        with `write_node_headers()`. Expects list or generator of nodes
        from the :py:class:`BioCypherNode` class.

        Args:
            nodes (BioCypherNode): a list or generator of nodes in
                :py:class:`BioCypherNode` format

        Returns:
            bool: The return value. True for success, False otherwise.
        """

        if isinstance(nodes, GeneratorType):
            logger.info("Writing node CSV from generator.")

            bins = defaultdict(list)  # dict to store a list for each
            # label that is passed in
            bin_l = {}  # dict to store the length of each list for
            # batching cutoff
            parts = {}  # dict to store the number of parts of each label
            # for file naming
            props = defaultdict(list)  # dict to store a list of properties
            # for each label to check for consistency
            labels = {}  # dict to store the additional labels for each
            # primary graph constituent from biolink hierarchy
            for n in nodes:
                label = n.get_label()
                if not label in bins.keys():
                    # start new list
                    bins[label].append(n)
                    bin_l[label] = 1
                    parts[label] = 0
                    # use first node to define properties for checking
                    # could later be by checking all nodes but much more
                    # complicated, particularly involving batch writing
                    # (would require "do-overs") TODO
                    props[label] = list(n.get_properties().keys())

                    # get label hierarchy
                    # multiple labels:
                    all_labels = self.bl_adapter.leaves[label]["ancestors"]

                    if all_labels:
                        # remove prefix
                        all_labels = [
                            l.replace("biolink:", "") for l in all_labels
                        ]
                        # remove duplicates
                        all_labels = list(OrderedDict.fromkeys(all_labels))
                        # concatenate with array delimiter
                        all_labels = self.adelim.join(all_labels)
                    else:
                        all_labels = label

                    labels[label] = all_labels

                else:
                    # add to list
                    bins[label].append(n)
                    bin_l[label] += 1
                    if not bin_l[label] < batch_size:
                        # batch size controlled here
                        passed = self._write_single_node_list_to_file(
                            bins[label],
                            label,
                            parts[label],
                            props[label],
                            labels[label],
                        )

                        if not passed:
                            return False

                        bins[label] = []
                        bin_l[label] = 0
                        parts[label] += 1

            # after generator depleted, write remainder of bins
            for label, nl in bins.items():
                passed = self._write_single_node_list_to_file(
                    nl, label, parts[label], props[label], labels[label]
                )

                if not passed:
                    return False

            # use complete bin list to write header files
            # TODO if a node type has varying properties
            # (ie missingness), we'd need to collect all possible
            # properties in the generator pass

            # save first-node properties to instance attribute
            self.property_dict = props

            return True
        else:
            if type(nodes) is not list:
                logger.error("Nodes must be passed as list or generator.")
                return False
            else:

                def gen(nodes):
                    for n in nodes:
                        yield n

                return self._write_node_data(gen(nodes), batch_size=batch_size)

    def _write_node_headers(self):
        """
        Writes single CSV file for a graph entity that is represented
        as a node as per the definition in the `schema_config.yaml`,
        containing only the header for this type of node.

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        # load headers from data parse
        if not self.property_dict:
            logger.error(
                "Header information not found. Was the data parsed first?"
            )
            return False

        for label, props in self.property_dict.items():
            # create header CSV with ID, properties, labels

            # preferred ID from schema
            id = self.schema[label]["preferred_id"] + ":ID"

            # to programmatically define properties to be written, the
            # data would have to be parsed before writing the header.
            # alternatively, desired properties could also be provided
            # via the schema_config.yaml, but that is more effort for
            # the user. TODO provide option to fix desired properties in
            # YAML.

            if len(props) > 1:
                props = self.delim.join(props)

            file_path = self.output_path + label + "-header.csv"
            with open(file_path, "w") as f:
                # concatenate with delimiter
                row = self.delim.join([id, props, ":LABEL"])
                f.write(row)

        return True

    def _write_single_node_list_to_file(
        self, node_list, label, part, props, labels
    ):
        """
        This function takes one list of biocypher nodes and writes them
        to a Neo4j admin import compatible CSV file.

        Args:
            node_list (list): list of BioCypherNodes to be written
            label (str): the primary label of the node
            part (int): for large amounts of data, import is done in
                parts denoted by a suffix in the CSV file name

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        if not all(isinstance(n, BioCypherNode) for n in node_list):
            logger.error("Nodes must be passed as type BioCypherNode.")
            return False

        # from list of nodes to list of strings
        # TODO string properties in quotes (?)
        # only necessary if they contain spaces?
        # TODO property types such as ":int"?
        lines = []
        for n in node_list:
            # check for deviations in properties
            keys = list(n.get_properties().keys())
            if not keys == props:
                onode = n.get_id()
                oprop1 = set(props).difference(keys)
                oprop2 = set(keys).difference(props)
                logger.error(
                    f"At least one node of the class {n.get_label()} "
                    f"has more or fewer properties than the others. "
                    f"Offending node: {onode}, offending property: "
                    f"{max([oprop1, oprop2])}."
                )
                return False
            lines.append(
                self.delim.join(
                    [
                        n.get_id(),
                        # here we need a list of properties in
                        # the same order as in the header
                        self.delim.join(list(n.get_properties().values())),
                        labels,
                    ]
                )
                + "\n"
            )
        padded_part = str(part).zfill(3)
        file_path = self.output_path + label + "-part" + padded_part + ".csv"
        with open(file_path, "w") as f:
            # concatenate with delimiter
            f.writelines(lines)

        return True

    def _write_edge_data(self):
        pass

    def _write_edge_headers(self):
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

            # on the other hand, we need to write the data anyways. may
            # make sense to just reverse the order and pass written
            # properties to the header writer function.

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
    - Can properties the node/relationship does not own be left blank?

Formatting: --delimiter=";"
            --array-delimiter="|"
            --quote="'"

The header contains information for each field, for ID and properties
in the format <name>: <field_type>. E.g.: 
`UniProtKB:ID;genesymbol;entrez_id:int;:LABEL`. Multiple labels can 
be given by separating with the array delimiter.

There are three mandatory fields for relationship data:
:START_ID — ID referring to a node.
:END_ID — ID referring to a node.
:TYPE — The relationship type.

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
