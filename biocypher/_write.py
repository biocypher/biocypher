#!/usr/bin/env python

#
# Copyright 2021, Heidelberg University Clinic
#
# File author(s): Sebastian Lobentanzer
#                 ...
#
# Distributed under GPLv3 license, see the file `LICENSE`.
#

"""
Export of CSV files for the Neo4J admin import. The admin import is able
to quickly transfer large amounts of content into an unused database. For more
explanation, see https://neo4j.com/docs/operations-manual/current/tuto\
rial/neo4j-admin-import/.

Import like that:
https://community.neo4j.com/t/how-can-i-use-a-database-created-with-neo4j-\
admin-import-in-neo4j-desktop/40594

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

.. code-block:: bash

   bin/neo4j-admin import --database=neo4j
   --nodes=import/entities-header.csv,import/entities-part1.csv,
    import/entities-part2.csv
   --nodes=import/interactions-header.csv,import/interactions-part1.csv,
    import/interaction-part2.csv
   --relationships=import/rels-header.csv,import/rels-part1.csv,
    import/rels-part2.csv

Can use regex, e.g., [..] import/rels-part*. In this case, use padding
for ordering of the earlier part files ("01, 02").

# How to import:

1. stop the db

2. shell command:

.. code-block:: bash

   bin/neo4j-admin import --database=neo4j
   # nodes per type, separate header, regex for parts:
   --nodes="<path>/<node_type>-header.csv,<path>/<node_type>-part.*"
   # edges per type, separate header, regex for parts:
   --relationships="<path>/<edge_type>-header.csv,<path>/<edge_type>-part.*"

3. start db, test for consistency
"""

import glob
from ._logger import logger

logger.debug(f"Loading module {__name__}.")

from types import GeneratorType
from typing import TYPE_CHECKING, Optional, Union
from more_itertools import peekable
from datetime import datetime
from collections import OrderedDict, defaultdict
import os

from biocypher._config import config as _config
from ._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode

__all__ = ["BatchWriter"]

if TYPE_CHECKING:

    from ._translate import BiolinkAdapter

# TODO global variable for collecting all ids to avoid duplicates?

# TODO retrospective check of written csvs?


class BatchWriter:
    """
    Class for writing node and edge representations to disk using the
    format specified by Neo4j for the use of admin import. Each batch
    writer instance has a fixed representation that needs to be passed
    at instantiation via the :py:attr:`schema` argument. The instance
    also expects a biolink adapter via :py:attr:`bl_adapter` to be able
    to convert and extend the hierarchy.

    Args:
        schema:
            The BioCypher graph schema (from :py:class:`VersionNode`).
        bl_adapter:
            Instance of :py:class:`BiolinkAdapter` to enable translation and
            ontology queries
        path:
            Path for exporting CSV files.
        db_name:
            Name of the Neo4j database that will be used in the generated
            commands.
    """

    def __init__(
        self,
        leaves: dict,
        bl_adapter: "BiolinkAdapter",
        dirname: Optional[str] = None,
        db_name: str = "neo4j",
        delimiter: str = ",",
        array_delimiter: str = "|",
        quote: str = "'",
    ):
        """ """
        self.delim = delimiter
        self.adelim = array_delimiter
        self.quote = quote
        self.leaves = leaves
        self.bl_adapter = bl_adapter
        self.node_property_dict = None
        self.edge_property_dict = None
        self.import_call_base = (
            f"bin/neo4j-admin import --database={db_name} "
            f'--delimiter="{self.delim}" --array-delimiter="{self.adelim}" '
            '--quote="\'" '
        )
        self.import_call_nodes = ""
        self.import_call_edges = ""
        self.import_call = ""

        timestamp = lambda: datetime.now().strftime("%Y%m%d%H%M")

        self.outdir = dirname or os.path.join(_config("outdir"), timestamp())
        self.outdir = os.path.abspath(self.outdir)

        logger.info(f"Creating output directory `{self.outdir}`.")
        os.makedirs(self.outdir, exist_ok=True)

        self.seen_node_ids = set()  # set to store the ids of nodes that have
        # already been written; to avoid duplicates

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

    def write_edges(
        self, edges: Union[list, GeneratorType], batch_size=int(1e6)
    ) -> bool:
        """
        Wrapper for writing edges and their headers.

        Args:
            edges (BioCypherEdge): a list or generator of edges in
                :py:class:`BioCypherEdge` or :py:class:`BioCypherRelAsNode`
                format

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        passed = False
        # unwrap generator in one step
        z = zip(
            *(
                (
                    e.get_node(),
                    [e.get_source_edge(), e.get_target_edge()],
                )
                if isinstance(e, BioCypherRelAsNode)
                else (None, [e])
                for e in edges
            )
        )
        nod, edg = (list(a) for a in z)
        nod = [n for n in nod if n]
        edg = [val for sublist in edg for val in sublist]  # flatten

        if nod and edg:
            passed = self.write_nodes(nod) and self._write_edge_data(
                edg,
                batch_size,
            )
        else:
            passed = self._write_edge_data(edg, batch_size)

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

        if isinstance(nodes, GeneratorType) or isinstance(nodes, peekable):
            logger.info("Writing node CSV from generator.")

            bins = defaultdict(list)  # dict to store a list for each
            # label that is passed in
            bin_l = {}  # dict to store the length of each list for
            # batching cutoff
            reference_props = defaultdict(
                dict
            )  # dict to store a dict of properties
            # for each label to check for consistency and their type
            # for now, relevant for `int`
            labels = {}  # dict to store the additional labels for each
            # primary graph constituent from biolink hierarchy
            for node in nodes:
                _id = node.get_id()
                # check if node has already been written, if so skip
                if _id in self.seen_node_ids:
                    logger.info(f"Duplicate node id: {_id}")
                    continue

                label = node.get_label()
                if not label in bins.keys():
                    # start new list
                    all_labels = None
                    bins[label].append(node)
                    bin_l[label] = 1

                    # get properties from config if present
                    cprops = self.bl_adapter.leaves.get(label).get(
                        "properties"
                    )
                    if cprops:
                        d = cprops
                    else:
                        d = dict(node.get_properties())
                        # encode property type
                        for k, v in d.items():
                            if d[k] is not None:
                                d[k] = type(v).__name__
                    # else use first encountered node to define
                    # properties for checking; could later be by
                    # checking all nodes but much more complicated,
                    # particularly involving batch writing (would
                    # require "do-overs"). for now, we output a warning
                    # if node properties diverge from reference
                    # properties (in write_single_node_list_to_file)
                    # TODO

                    reference_props[label] = d

                    # get label hierarchy
                    # multiple labels:
                    if self.bl_adapter.biolink_leaves[label] is not None:
                        all_labels = self.bl_adapter.biolink_leaves[label][
                            "ancestors"
                        ]

                    if all_labels:
                        # remove duplicates
                        all_labels = list(OrderedDict.fromkeys(all_labels))
                        # concatenate with array delimiter
                        all_labels = self.adelim.join(all_labels)
                    else:
                        all_labels = label

                    labels[label] = all_labels

                else:
                    # add to list
                    bins[label].append(node)
                    bin_l[label] += 1
                    if not bin_l[label] < batch_size:
                        # batch size controlled here
                        passed = self._write_single_node_list_to_file(
                            bins[label],
                            label,
                            reference_props[label],
                            labels[label],
                        )

                        if not passed:
                            return False

                        bins[label] = []
                        bin_l[label] = 0

                self.seen_node_ids.add(_id)

            # after generator depleted, write remainder of bins
            for label, nl in bins.items():
                passed = self._write_single_node_list_to_file(
                    nl,
                    label,
                    reference_props[label],
                    labels[label],
                )

                if not passed:
                    return False

            # use complete bin list to write header files
            # TODO if a node type has varying properties
            # (ie missingness), we'd need to collect all possible
            # properties in the generator pass

            # save config or first-node properties to instance attribute
            self.node_property_dict = reference_props

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
                "Header information not found. Was the data parsed first?",
            )
            return False

        for label, props in self.node_property_dict.items():
            # create header CSV with ID, properties, labels

            # preferred ID from schema
            id = self.leaves[label]["preferred_id"] + ":ID"

            # to programmatically define properties to be written, the
            # data would have to be parsed before writing the header.
            # alternatively, desired properties could also be provided
            # via the schema_config.yaml, but that is more effort for
            # the user. TODO provide option to fix desired properties in
            # YAML.

            header_path = os.path.join(self.outdir, f"{label}-header.csv")
            parts_path = os.path.join(self.outdir, f"{label}-part.*")

            # check if file already exists
            if not os.path.exists(header_path):

                # concatenate key:value in props
                props_list = []
                for k, v in props.items():
                    if v == "int":
                        props_list.append(f"{k}:int")
                    elif v == "float":
                        props_list.append(f"{k}:double")
                    else:
                        props_list.append(f"{k}")

                # create list of lists and flatten
                # removes need for empty check of property list
                out_list = [[id], props_list, [":LABEL"]]
                out_list = [val for sublist in out_list for val in sublist]

                with open(header_path, "w") as f:

                    # concatenate with delimiter
                    row = self.delim.join(out_list)
                    f.write(row)

                # add file path to neo4 admin import statement
                self.import_call_nodes += (
                    f'--nodes="{header_path},{parts_path}" '
                )

        return True

    def _write_single_node_list_to_file(
        self,
        node_list: list,
        label: str,
        prop_dict: dict,
        labels: str,
    ):
        """
        This function takes one list of biocypher nodes and writes them
        to a Neo4j admin import compatible CSV file.

        Args:
            node_list (list): list of BioCypherNodes to be written
            label (str): the primary label of the node
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
        lines = []

        for n in node_list:

            # check for deviations in properties
            nprops = n.get_properties()
            hprops = list(prop_dict.keys())
            keys = list(nprops.keys())
            # compare lists order invariant
            if not set(hprops) == set(keys):
                onode = n.get_id()
                oprop1 = set(hprops).difference(keys)
                oprop2 = set(keys).difference(hprops)
                logger.error(
                    f"At least one node of the class {n.get_label()} "
                    f"has more or fewer properties than the others. "
                    f"Offending node: {onode!r}, offending property: "
                    f"{max([oprop1, oprop2])}.",
                )
                return False

            line = [n.get_id()]

            if hprops:

                plist = []
                # make all into strings, put actual strings in quotes
                for k, v in prop_dict.items():
                    p = nprops.get(k)
                    if p is None:
                        plist.append("")
                    elif v == "int" or v == "float":
                        plist.append(str(p))
                    else:
                        plist.append(self.quote + str(p) + self.quote)

                line.append(self.delim.join(plist))
            line.append(labels)

            lines.append(self.delim.join(line) + "\n")

        # avoid writing empty files
        if lines:
            self._write_next_part(label, lines)

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

        if isinstance(edges, GeneratorType):
            logger.info("Writing edge CSV from generator.")

            bins = defaultdict(list)  # dict to store a list for each
            # label that is passed in
            bin_l = {}  # dict to store the length of each list for
            # batching cutoff
            props = defaultdict(dict)  # dict to store a dict of properties
            # for each label to check for consistency and their type
            # for now, relevant for `int`
            for e in edges:
                if isinstance(e, BioCypherRelAsNode):
                    # shouldn't happen any more
                    logger.error(
                        "Edges cannot be of type 'RelAsNode'. "
                        f"Caused by: {e.get_node().get_id(), e.get_node().get_label()}"
                    )

                else:
                    label = e.get_label()
                    if not label in bins.keys():
                        # start new list
                        bins[label].append(e)
                        bin_l[label] = 1
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
                                props[label],
                            )

                            if not passed:
                                return False

                            bins[label] = []
                            bin_l[label] = 0

            # after generator depleted, write remainder of bins
            for label, nl in bins.items():

                passed = self._write_single_edge_list_to_file(
                    nl,
                    label,
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
                "Header information not found. Was the data parsed first?",
            )
            return False

        for label, props in self.edge_property_dict.items():
            # create header CSV with :START_ID, (optional) properties,
            # :END_ID, :TYPE

            # TODO provide option to fix desired properties in YAML.

            # paths
            header_path = os.path.join(self.outdir, f"{label}-header.csv")
            parts_path = os.path.join(self.outdir, f"{label}-part.*")

            # check for file exists
            if not os.path.exists(header_path):

                # concatenate key:value in props
                props_list = [
                    f"{k}:{v.__name__}" if v.__name__ == "int" else f"{k}"
                    for k, v in props.items()
                ]

                # create list of lists and flatten
                # removes need for empty check of property list
                out_list = [[":START_ID"], props_list, [":END_ID"], [":TYPE"]]
                out_list = [val for sublist in out_list for val in sublist]

                with open(header_path, "w") as f:

                    # concatenate with delimiter
                    row = self.delim.join(out_list)
                    f.write(row)

                # add file path to neo4 admin import statement
                self.import_call_edges += (
                    f'--relationships="{header_path},{parts_path}" '
                )

        return True

    def _write_single_edge_list_to_file(
        self,
        edge_list: list,
        label: str,
        prop_dict: dict,
    ):
        """
        This function takes one list of biocypher edges and writes them
        to a Neo4j admin import compatible CSV file.

        Args:
            edge_list (list): list of BioCypherEdges to be written
            label (str): the label (type) of the edge; verb form, all
                capital with underscores
            prop_dict (dict): properties of node class passed from parsing
                function and their types

        Returns:
            bool: The return value. True for success, False otherwise.
        """

        if not all(isinstance(n, BioCypherEdge) for n in edge_list):

            logger.error("Edges must be passed as type BioCypherEdge.")
            return False

        # from list of edges to list of strings
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
                    f"Offending edge: {oedge!r}, offending property: "
                    f"{max([oprop1, oprop2])}.",
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
                        ],
                    )
                    + "\n",
                )
            else:
                lines.append(
                    self.delim.join(
                        [
                            e.get_source_id(),
                            e.get_target_id(),
                            e.get_label(),
                        ],
                    )
                    + "\n",
                )

        # avoid writing empty files
        if lines:
            self._write_next_part(label, lines)

        return True

    def _write_next_part(self, label: str, lines: list):
        # list files in self.outdir
        files = glob.glob(os.path.join(self.outdir, f"{label}-part*.csv"))
        # find file with highest part number
        if files:
            next_part = (
                max(
                    [
                        int(
                            f.split(".")[-2].split("-")[-1].replace("part", "")
                        )
                        for f in files
                    ]
                )
                + 1
            )
        else:
            next_part = 0

            # write to file
        padded_part = str(next_part).zfill(3)
        logger.debug(
            f"Writing {len(lines)} entries to {label}-part{padded_part}.csv"
        )
        file_path = os.path.join(self.outdir, f"{label}-part{padded_part}.csv")

        with open(file_path, "w") as f:
            # concatenate with delimiter
            f.writelines(lines)

    def get_import_call(self) -> str:
        """
        Function to return the import call detailing folder and
        individual node and edge headers and data files, as well as
        delimiters and database name.

        Returns:
            str: a bash command for neo4j-admin import
        """

        return self._construct_import_call()

    def write_import_call(self) -> bool:
        """
        Function to write the import call detailing folder and
        individual node and edge headers and data files, as well as
        delimiters and database name, to the export folder as txt.

        Returns:
            bool: The return value. True for success, False otherwise.
        """

        file_path = os.path.join(self.outdir, "neo4j-admin-import-call.sh")
        logger.info(f"Writing neo4j-admin import call to `{file_path}`.")

        with open(file_path, "w") as f:

            f.write(self._construct_import_call())

        return True

    def _construct_import_call(self) -> str:
        """
        Function to construct the import call detailing folder and
        individual node and edge headers and data files, as well as
        delimiters and database name. Built after all data has been
        processed to ensure that nodes are called before any edges.

        Returns:
            str: a bash command for neo4j-admin import
        """

        # append node and edge import calls
        self.import_call = (
            self.import_call_base
            + self.import_call_nodes
            + self.import_call_edges
        )

        return self.import_call
