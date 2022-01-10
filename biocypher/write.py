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
from more_itertools import peekable

from .create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode
import logging

logger = logging.getLogger(__name__)
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
        self.node_property_dict = None
        self.edge_property_dict = None

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
        Wrapper for writing nodes and their headers.

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

    def write_edges(self, edges, batch_size=int(1e6)):
        """
        Wrapper for writing edges and their headers.

        Args:
            edges (BioCypherEdge): a list or generator of edges in
                :py:class:`BioCypherEdge` format

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        passed = False
        edges = peekable(edges)
        if isinstance(edges.peek(), BioCypherRelAsNode):
            # unwrap generator in one step
            z = zip(
                *(
                    (
                        e.get_node(),
                        [e.get_source_edge(), e.get_target_edge()],
                    )
                    for e in edges
                )
            )
            nod, edg = [list(a) for a in z]
            edg = [val for sublist in edg for val in sublist]  # flatten

            passed = self.write_nodes(nod) and self.write_edges(edg)

        elif isinstance(edges.peek(), BioCypherEdge):
            passed = self._write_edge_data(edges, batch_size)

        if not passed:
            logger.error("Error while writing edge data.")
            return False
        # pass property data to header writer per edge type written
        passed = self._write_edge_headers()
        if not passed:
            logger.error("Error while writing edge headers.")
            return False

        return True

    def _write_node_data(self, nodes, batch_size):
        """
        Writes biocypher nodes to CSV conforming to the headers created
        with `_write_node_headers()`, and is actually required to be run
        before calling `_write_node_headers()` to set the
        :py:attr:`self.node_property_dict` for passing the node properties
        to the instance. Expects list or generator of nodes from the
        :py:class:`BioCypherNode` class.

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
            props = defaultdict(dict)  # dict to store a dict of properties
            # for each label to check for consistency and their type
            # for now, relevant for `int`
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
                    d = dict(n.get_properties())
                    for k, v in d.items():
                        d[k] = type(v)
                    props[label] = d

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
                    nl,
                    label,
                    parts[label],
                    props[label],
                    labels[label],
                )

                if not passed:
                    return False

            # use complete bin list to write header files
            # TODO if a node type has varying properties
            # (ie missingness), we'd need to collect all possible
            # properties in the generator pass

            # save first-node properties to instance attribute
            self.node_property_dict = props

            return True
        else:
            if type(nodes) is not list:
                logger.error("Nodes must be passed as list or generator.")
                return False
            else:

                def gen(nodes):
                    yield from nodes

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
        if not self.node_property_dict:
            logger.error(
                "Header information not found. Was the data parsed first?"
            )
            return False

        for label, props in self.node_property_dict.items():
            # create header CSV with ID, properties, labels

            # preferred ID from schema
            id = self.schema[label]["preferred_id"] + ":ID"

            # to programmatically define properties to be written, the
            # data would have to be parsed before writing the header.
            # alternatively, desired properties could also be provided
            # via the schema_config.yaml, but that is more effort for
            # the user. TODO provide option to fix desired properties in
            # YAML.

            # concatenate key:value in props
            props_list = [
                f"{k}:{v.__name__}" if v.__name__ == "int" else f"{k}"
                for k, v in props.items()
            ]

            # create list of lists and flatten
            # removes need for empty check of property list
            out_list = [[id], props_list, [":LABEL"]]
            out_list = [val for sublist in out_list for val in sublist]

            file_path = self.output_path + label + "-header.csv"
            with open(file_path, "w") as f:
                # concatenate with delimiter
                row = self.delim.join(out_list)
                f.write(row)

        return True

    def _write_single_node_list_to_file(
        self, node_list, label, part, prop_dict, labels
    ):
        """
        This function takes one list of biocypher nodes and writes them
        to a Neo4j admin import compatible CSV file.

        Args:
            node_list (list): list of BioCypherNodes to be written
            label (str): the primary label of the node
            part (int): for large amounts of data, import is done in
                parts denoted by a suffix in the CSV file name
            prop_dict (dict): properties of node class passed from parsing
                function and their types
            labels (str): string of one or several concatenated labels
                for the node class

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
            nprops = n.get_properties()
            hprops = list(prop_dict.keys())
            keys = list(nprops.keys())
            if not keys == hprops:
                onode = n.get_id()
                oprop1 = set(hprops).difference(keys)
                oprop2 = set(keys).difference(hprops)
                logger.error(
                    f"At least one node of the class {n.get_label()} "
                    f"has more or fewer properties than the others. "
                    f"Offending node: {onode}, offending property: "
                    f"{max([oprop1, oprop2])}."
                )
                return False
            if hprops:
                plist = []
                for e, t in zip(nprops.values(), prop_dict.values()):
                    if t == int:
                        plist.append(str(e))
                    else:
                        plist.append(self.quote + str(e) + self.quote)
                # make all into strings, put actual strings in quotes
                lines.append(
                    self.delim.join(
                        [
                            n.get_id(),
                            # here we need a list of properties in
                            # the same order as in the header
                            self.delim.join(plist),
                            labels,
                        ]
                    )
                    + "\n"
                )
            else:
                lines.append(
                    self.delim.join(
                        [
                            n.get_id(),
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

    def _write_edge_data(self, edges, batch_size):
        """
        Writes biocypher edges to CSV conforming to the headers created
        with `_write_edge_headers()`, and is actually required to be run
        before calling `_write_node_headers()` to set the
        :py:attr:`self.edge_property_dict` for passing the edge properties
        to the instance. Expects list or generator of edges
        from the :py:class:`BioCypherEdge` class.

        Args:
            edges (BioCypherEdge): a list or generator of edges in
                :py:class:`BioCypherEdge` format

        Returns:
            bool: The return value. True for success, False otherwise.
        """

        if isinstance(edges, GeneratorType) or isinstance(edges, peekable):
            logger.info("Writing edge CSV from generator.")

            bins = defaultdict(list)  # dict to store a list for each
            # label that is passed in
            bin_l = {}  # dict to store the length of each list for
            # batching cutoff
            parts = {}  # dict to store the number of parts of each label
            # for file naming
            props = defaultdict(dict)  # dict to store a dict of properties
            # for each label to check for consistency and their type
            # for now, relevant for `int`
            for e in edges:
                label = e.get_label()
                if not label in bins.keys():
                    # start new list
                    bins[label].append(e)
                    bin_l[label] = 1
                    parts[label] = 0
                    # use first edge to define properties for checking
                    # could later be by checking all edges but much more
                    # complicated, particularly involving batch writing
                    # (would require "do-overs") TODO
                    d = dict(e.get_properties())
                    for k, v in d.items():
                        d[k] = type(v)
                    props[label] = d

                else:
                    # add to list
                    bins[label].append(e)
                    bin_l[label] += 1
                    if not bin_l[label] < batch_size:
                        # batch size controlled here
                        passed = self._write_single_edge_list_to_file(
                            bins[label],
                            label,
                            parts[label],
                            props[label],
                        )

                        if not passed:
                            return False

                        bins[label] = []
                        bin_l[label] = 0
                        parts[label] += 1

            # after generator depleted, write remainder of bins
            for label, nl in bins.items():
                passed = self._write_single_edge_list_to_file(
                    nl,
                    label,
                    parts[label],
                    props[label],
                )

                if not passed:
                    return False

            # use complete bin list to write header files
            # TODO if a edge type has varying properties
            # (ie missingness), we'd need to collect all possible
            # properties in the generator pass

            # save first-edge properties to instance attribute
            self.edge_property_dict = props

            return True
        else:
            if type(edges) is not list:
                logger.error("Edges must be passed as list or generator.")
                return False
            else:

                def gen(edges):
                    yield from edges

                return self._write_edge_data(gen(edges), batch_size=batch_size)

    def _write_edge_headers(self):
        """
        Writes single CSV file for a graph entity that is represented
        as an edge as per the definition in the `schema_config.yaml`,
        containing only the header for this type of edge.

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        # load headers from data parse
        if not self.edge_property_dict:
            logger.error(
                "Header information not found. Was the data parsed first?"
            )
            return False

        for label, props in self.edge_property_dict.items():
            # create header CSV with :START_ID, (optional) properties,
            # :END_ID, :TYPE

            # TODO provide option to fix desired properties in YAML.

            # concatenate key:value in props
            props_list = [
                f"{k}:{v.__name__}" if v.__name__ == "int" else f"{k}"
                for k, v in props.items()
            ]

            # create list of lists and flatten
            # removes need for empty check of property list
            out_list = [[":START_ID"], props_list, [":END_ID"], [":TYPE"]]
            out_list = [val for sublist in out_list for val in sublist]

            file_path = self.output_path + label + "-header.csv"
            with open(file_path, "w") as f:
                # concatenate with delimiter
                row = self.delim.join(out_list)
                f.write(row)

        return True

    def _write_single_edge_list_to_file(
        self, edge_list, label, part, prop_dict
    ):
        """
        This function takes one list of biocypher edges and writes them
        to a Neo4j admin import compatible CSV file.

        Args:
            edge_list (list): list of BioCypherEdges to be written
            label (str): the label (type) of the edge; verb form, all
                capital with underscores
            part (int): for large amounts of data, import is done in
                parts denoted by a suffix in the CSV file name
            prop_dict (dict): properties of node class passed from parsing
                function and their types

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        if not all(isinstance(n, BioCypherEdge) for n in edge_list):
            logger.error("Edges must be passed as type BioCypherEdge.")
            return False

        # from list of edges to list of strings
        # TODO string properties in quotes (?)
        # only necessary if they contain spaces?
        # TODO property types such as ":int"?
        lines = []
        for e in edge_list:
            # check for deviations in properties
            eprops = e.get_properties()
            hprops = list(prop_dict.keys())
            keys = list(eprops.keys())
            if not keys == hprops:
                oedge = f"{e.get_source_id()}-{e.get_target_id()}"
                oprop1 = set(hprops).difference(keys)
                oprop2 = set(keys).difference(hprops)
                logger.error(
                    f"At least one edge of the class {e.get_label()} "
                    f"has more or fewer properties than the others. "
                    f"Offending edge: {oedge}, offending property: "
                    f"{max([oprop1, oprop2])}."
                )
                return False
            if hprops:
                plist = []
                for ev, tv in zip(eprops.values(), prop_dict.values()):
                    if tv == int:
                        plist.append(str(ev))
                    else:
                        plist.append(self.quote + str(ev) + self.quote)
                # make all into strings, put actual strings in quotes
                lines.append(
                    self.delim.join(
                        [
                            e.get_source_id(),
                            # here we need a list of properties in
                            # the same order as in the header
                            self.delim.join(plist),
                            e.get_target_id(),
                            e.get_label(),
                        ]
                    )
                    + "\n"
                )
            else:
                lines.append(
                    self.delim.join(
                        [
                            e.get_source_id(),
                            e.get_target_id(),
                            e.get_label(),
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
