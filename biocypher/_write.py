#!/usr/bin/env python

#
# Copyright 2021, Heidelberg University Clinic
#
# File author(s): Sebastian Lobentanzer
#                 Michael Hartung
#
# Distributed under MIT licence, see the file `LICENSE`.
#
"""
BioCypher 'offline' module. Handles the writing of node and edge representations
suitable for import into a DBMS.
"""

import glob

from ._logger import logger

logger.debug(f'Loading module {__name__}.')

from abc import ABC, abstractmethod
from types import GeneratorType
from typing import TYPE_CHECKING, Union, Optional
from datetime import datetime
from collections import OrderedDict, defaultdict
import os

from more_itertools import peekable

from ._config import config as _config
from ._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode

__all__ = ['get_writer']

if TYPE_CHECKING:

    from ._ontology import Ontology
    from ._translate import Translator
    from ._deduplicate import Deduplicator


class _BatchWriter(ABC):
    """
    Abtract parent class for writing node and edge representations to disk using the
    format specified by each database type. The database-specific functions are implemented
    by the respective child-classes. This abstract class contains all methods expected by
    a bach writer instance, some of which need to be overwritten by the child classes.

    Each batch writer instance has a fixed representation that needs to be passed
    at instantiation via the :py:attr:`schema` argument. The instance
    also expects an ontology adapter via :py:attr:`ontology_adapter` to be able
    to convert and extend the hierarchy.

    Requires the following methods to be overwritten by database-specific writer classes:
        - _write_node_headers
        - _write_edge_headers
        - _construct_import_call
        - _write_array_string
        - _get_import_script_name

    Args:
        ontology:
            Instance of :py:class:`Ontology` to enable translation and
            ontology queries

        translator:
            Instance of :py:class:`Translator` to enable translation of
            nodes and manipulation of properties.

        deduplicator:
            Instance of :py:class:`Deduplicator` to enable deduplication
            of nodes and edges.

        delimiter:
            The delimiter to use for the CSV files.

        array_delimiter:
            The delimiter to use for array properties.

        quote:
            The quote character to use for the CSV files.

        dirname:
            Path for exporting CSV files.

        db_name:
            Name of the database that will be used in the generated
            commands.

        import_call_bin_prefix:
            Path prefix for the admin import call binary.

        import_call_file_prefix:
            Path prefix for the data files (headers and parts) in the import 
            call.

        wipe:
            Whether to force import (removing existing DB content). (Specific to Neo4j.)

        strict_mode:
            Whether to enforce source, version, and license properties.

        skip_bad_relationships:
            Whether to skip relationships that do not have a valid
            start and end node. (Specific to Neo4j.)

        skip_duplicate_nodes:
            Whether to skip duplicate nodes. (Specific to Neo4j.)
    """
    @abstractmethod
    def _get_default_import_call_bin_prefix(self):
        """
        Abstract method to provide the default string for the import call bin prefix.

        Returns:
            str: The database-specific string for the path to the import call bin prefix
        """
        raise NotImplementedError(
            "Database writer must override '_get_default_import_call_bin_prefix'"
        )

    @abstractmethod
    def _write_array_string(self, string_list):
        """
        Abstract method to write the string representation of an array into a .csv file.
        Different databases require different formats of array to optimize import speed.

        Args:
            string_list (list): list of ontology strings

        Returns:
            str: The database-specific string representation of an array
        """
        raise NotImplementedError(
            "Database writer must override '_write_node_headers'"
        )

    @abstractmethod
    def _write_node_headers(self):
        """
        Abstract method that takes care of importing properties of a graph entity that is represented
        as a node as per the definition in the `schema_config.yaml`

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        raise NotImplementedError(
            "Database writer must override '_write_node_headers'"
        )

    @abstractmethod
    def _write_edge_headers(self):
        """
        Abstract method to write a database import-file for a graph entity that is represented
        as an edge as per the definition in the `schema_config.yaml`,
        containing only the header for this type of edge.

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        raise NotImplementedError(
            "Database writer must override '_write_edge_headers'"
        )

    @abstractmethod
    def _construct_import_call(self) -> str:
        """
        Function to construct the import call detailing folder and
        individual node and edge headers and data files, as well as
        delimiters and database name. Built after all data has been
        processed to ensure that nodes are called before any edges.

        Returns:
            str: A bash command for csv import.
        """
        raise NotImplementedError(
            "Database writer must override '_construct_import_call'"
        )

    @abstractmethod
    def _get_import_script_name(self) -> str:
        """
        Returns the name of the import script.
        The name will be chosen based on the used database.

        Returns:
            str: The name of the import script (ending in .sh)
        """
        raise NotImplementedError(
            "Database writer must override '_get_import_script_name'"
        )

    def __init__(
        self,
        ontology: 'Ontology',
        translator: 'Translator',
        deduplicator: 'Deduplicator',
        delimiter: str,
        array_delimiter: str = ',',
        quote: str = '"',
        output_directory: Optional[str] = None,
        db_name: str = 'neo4j',
        import_call_bin_prefix: Optional[str] = None,
        import_call_file_prefix: Optional[str] = None,
        wipe: bool = True,
        strict_mode: bool = False,
        skip_bad_relationships: bool = False,
        skip_duplicate_nodes: bool = False,
        db_user: str = None,
        db_password: str = None,
        db_port: str = None
    ):
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_port = db_port

        self.delim, self.escaped_delim = self._process_delimiter(delimiter)
        self.adelim, self.escaped_adelim = self._process_delimiter(
            array_delimiter
        )
        self.quote = quote
        self.skip_bad_relationships = skip_bad_relationships
        self.skip_duplicate_nodes = skip_duplicate_nodes

        if import_call_bin_prefix is None:
            self.import_call_bin_prefix = self._get_default_import_call_bin_prefix(
            )
        else:
            self.import_call_bin_prefix = import_call_bin_prefix

        self.wipe = wipe
        self.strict_mode = strict_mode

        self.extended_schema = ontology.extended_schema
        self.ontology = ontology
        self.translator = translator
        self.deduplicator = deduplicator
        self.node_property_dict = {}
        self.edge_property_dict = {}
        self.import_call_nodes = set()
        self.import_call_edges = set()

        self._outdir = output_directory

        self._import_call_file_prefix = import_call_file_prefix

        if os.path.exists(self.outdir):
            logger.warning(
                f'Output directory `{self.outdir}` already exists. '
                'If this is not planned, file consistency may be compromised.'
            )
        else:
            logger.info(f'Creating output directory `{self.outdir}`.')
            os.makedirs(self.outdir)

        self.parts = {}  # dict to store the paths of part files for each label

        # TODO not memory efficient, but should be fine for most cases; is
        # there a more elegant solution?

    @property
    def outdir(self):
        """
        Property for output directory path.
        """

        return self._outdir


    @property
    def import_call_file_prefix(self):
        """
        Property for output directory path.
        """

        if self._import_call_file_prefix is None:
            return self._outdir
        else:
            return self._import_call_file_prefix

    def _process_delimiter(self, delimiter: str) -> str:
        """
        Return escaped characters in case of receiving their string
        representation (e.g. tab for '\t').
        """

        if delimiter == '\\t':

            return '\t', '\\t'

        else:

            return delimiter, delimiter

    def write_nodes(self, nodes, batch_size: int = int(1e6)):
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
            logger.error('Error while writing node data.')
            return False
        # pass property data to header writer per node type written
        passed = self._write_node_headers()
        if not passed:
            logger.error('Error while writing node headers.')
            return False

        return True

    def write_edges(
        self,
        edges: Union[list, GeneratorType],
        batch_size: int = int(1e6),
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
        edges = list(edges)  # force evaluation to handle empty generator
        if edges:
            z = zip(
                *(
                    (
                        e.get_node(),
                        [
                            e.get_source_edge(),
                            e.get_target_edge(),
                        ],
                    ) if isinstance(e, BioCypherRelAsNode) else (None, [e])
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

        else:
            # is this a problem? if the generator or list is empty, we
            # don't write anything.
            logger.debug(
                'No edges to write, possibly due to no matched Biolink classes.',
            )
            pass

        if not passed:
            logger.error('Error while writing edge data.')
            return False
        # pass property data to header writer per edge type written
        passed = self._write_edge_headers()
        if not passed:
            logger.error('Error while writing edge headers.')
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
            logger.debug('Writing node CSV from generator.')

            bins = defaultdict(list)  # dict to store a list for each
            # label that is passed in
            bin_l = {}  # dict to store the length of each list for
            # batching cutoff
            reference_props = defaultdict(
                dict,
            )  # dict to store a dict of properties
            # for each label to check for consistency and their type
            # for now, relevant for `int`
            labels = {}  # dict to store the additional labels for each
            # primary graph constituent from biolink hierarchy
            for node in nodes:
                # check if node has already been written, if so skip
                if self.deduplicator.node_seen(node):
                    continue

                _id = node.get_id()
                label = node.get_label()

                # check for non-id
                if not _id:
                    logger.warning(f'Node {label} has no id; skipping.')
                    continue

                if not label in bins.keys():
                    # start new list
                    all_labels = None
                    bins[label].append(node)
                    bin_l[label] = 1

                    # get properties from config if present
                    cprops = self.extended_schema.get(label).get('properties', )
                    if cprops:
                        d = dict(cprops)

                        # add id and preferred id to properties; these are
                        # created in node creation (`_create.BioCypherNode`)
                        d['id'] = 'str'
                        d['preferred_id'] = 'str'

                        # add strict mode properties
                        if self.strict_mode:
                            d['source'] = 'str'
                            d['version'] = 'str'
                            d['licence'] = 'str'

                    else:
                        d = dict(node.get_properties())
                        # encode property type
                        for k, v in d.items():
                            if d[k] is not None:
                                d[k] = type(v).__name__
                    # else use first encountered node to define properties for
                    # checking; could later be by checking all nodes but much
                    # more complicated, particularly involving batch writing
                    # (would require "do-overs"). for now, we output a warning
                    # if node properties diverge from reference properties (in
                    # write_single_node_list_to_file) TODO if it occurs, ask
                    # user to select desired properties and restart the process

                    reference_props[label] = d

                    # get label hierarchy
                    # multiple labels:
                    all_labels = self.ontology.get_ancestors(label)

                    if all_labels:
                        # convert to pascal case
                        all_labels = [
                            self.translator.name_sentence_to_pascal(label)
                            for label in all_labels
                        ]
                        # remove duplicates
                        all_labels = list(OrderedDict.fromkeys(all_labels))
                        # order alphabetically
                        all_labels.sort()
                        # concatenate with array delimiter
                        all_labels = self._write_array_string(all_labels)
                    else:
                        all_labels = self.translator.name_sentence_to_pascal(
                            label
                        )

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
            for label in reference_props.keys():
                self.node_property_dict[label] = reference_props[label]

            return True
        else:
            if type(nodes) is not list:
                logger.error('Nodes must be passed as list or generator.')
                return False
            else:

                def gen(nodes):
                    yield from nodes

                return self._write_node_data(gen(nodes), batch_size=batch_size)

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
            logger.error('Nodes must be passed as type BioCypherNode.')
            return False

        # from list of nodes to list of strings
        lines = []

        for n in node_list:

            # check for deviations in properties
            # node properties
            n_props = n.get_properties()
            n_keys = list(n_props.keys())
            # reference properties
            ref_props = list(prop_dict.keys())

            # compare lists order invariant
            if not set(ref_props) == set(n_keys):
                onode = n.get_id()
                oprop1 = set(ref_props).difference(n_keys)
                oprop2 = set(n_keys).difference(ref_props)
                logger.error(
                    f'At least one node of the class {n.get_label()} '
                    f'has more or fewer properties than another. '
                    f'Offending node: {onode!r}, offending property: '
                    f'{max([oprop1, oprop2])}. '
                    f'All reference properties: {ref_props}, '
                    f'All node properties: {n_keys}.',
                )
                return False

            line = [n.get_id()]

            if ref_props:

                plist = []
                # make all into strings, put actual strings in quotes
                for k, v in prop_dict.items():
                    p = n_props.get(k)
                    if p is None:  # TODO make field empty instead of ""?
                        plist.append('')
                    elif v in [
                        'int',
                        'integer',
                        'long',
                        'float',
                        'double',
                        'dbl',
                        'bool',
                        'boolean',
                    ]:
                        plist.append(str(p))
                    else:
                        if isinstance(p, list):
                            plist.append(self._write_array_string(p))
                        else:
                            plist.append(f'{self.quote}{str(p)}{self.quote}')

                line.append(self.delim.join(plist))
            line.append(labels)

            lines.append(self.delim.join(line) + '\n')

        # avoid writing empty files
        if lines:
            self._write_next_part(label, lines)

        return True

    def _write_edge_data(self, edges, batch_size):
        """
        Writes biocypher edges to CSV conforming to the headers created
        with `_write_edge_headers()`, and is actually required to be run
        before calling `_write_node_headers()` to set the
        :py:attr:`self.edge_property_dict` for passing the edge
        properties to the instance. Expects list or generator of edges
        from the :py:class:`BioCypherEdge` class.

        Args:
            edges (BioCypherEdge): a list or generator of edges in
                :py:class:`BioCypherEdge` format

        Returns:
            bool: The return value. True for success, False otherwise.

        Todo:
            - currently works for mixed edges but in practice often is
              called on one iterable containing one type of edge only
        """

        if isinstance(edges, GeneratorType):
            logger.debug('Writing edge CSV from generator.')

            bins = defaultdict(list)  # dict to store a list for each
            # label that is passed in
            bin_l = {}  # dict to store the length of each list for
            # batching cutoff
            reference_props = defaultdict(
                dict,
            )  # dict to store a dict of properties
            # for each label to check for consistency and their type
            # for now, relevant for `int`
            for edge in edges:
                # check for duplicates
                if self.deduplicator.edge_seen(edge):
                    continue

                if not (edge.get_source_id() and edge.get_target_id()):
                    logger.error(
                        'Edge must have source and target node. '
                        f'Caused by: {edge}',
                    )
                    continue

                label = edge.get_label()

                if not label in bins.keys():
                    # start new list
                    bins[label].append(edge)
                    bin_l[label] = 1

                    # get properties from config if present

                    # check whether label is in ontology_adapter.leaves
                    # (may not be if it is an edge that carries the
                    # "label_as_edge" property)
                    cprops = None
                    if label in self.extended_schema:
                        cprops = self.extended_schema.get(label).get(
                            'properties',
                        )
                    else:
                        # try via "label_as_edge"
                        for k, v in self.extended_schema.items():
                            if isinstance(v, dict):
                                if v.get('label_as_edge') == label:
                                    cprops = v.get('properties')
                                    break
                    if cprops:
                        d = cprops

                        # add strict mode properties
                        if self.strict_mode:
                            d['source'] = 'str'
                            d['version'] = 'str'
                            d['licence'] = 'str'

                    else:
                        d = dict(edge.get_properties())
                        # encode property type
                        for k, v in d.items():
                            if d[k] is not None:
                                d[k] = type(v).__name__
                    # else use first encountered edge to define
                    # properties for checking; could later be by
                    # checking all edges but much more complicated,
                    # particularly involving batch writing (would
                    # require "do-overs"). for now, we output a warning
                    # if edge properties diverge from reference
                    # properties (in write_single_edge_list_to_file)
                    # TODO

                    reference_props[label] = d

                else:
                    # add to list
                    bins[label].append(edge)
                    bin_l[label] += 1
                    if not bin_l[label] < batch_size:
                        # batch size controlled here
                        passed = self._write_single_edge_list_to_file(
                            bins[label],
                            label,
                            reference_props[label],
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
                    reference_props[label],
                )

                if not passed:
                    return False

            # use complete bin list to write header files
            # TODO if a edge type has varying properties
            # (ie missingness), we'd need to collect all possible
            # properties in the generator pass

            # save first-edge properties to instance attribute
            for label in reference_props.keys():
                self.edge_property_dict[label] = reference_props[label]

            return True
        else:
            if type(edges) is not list:
                logger.error('Edges must be passed as list or generator.')
                return False
            else:

                def gen(edges):
                    yield from edges

                return self._write_edge_data(gen(edges), batch_size=batch_size)

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

            label (str): the label (type) of the edge

            prop_dict (dict): properties of node class passed from parsing
                function and their types

        Returns:
            bool: The return value. True for success, False otherwise.
        """

        if not all(isinstance(n, BioCypherEdge) for n in edge_list):

            logger.error('Edges must be passed as type BioCypherEdge.')
            return False

        # from list of edges to list of strings
        lines = []
        for e in edge_list:
            # check for deviations in properties
            # edge properties
            e_props = e.get_properties()
            e_keys = list(e_props.keys())
            ref_props = list(prop_dict.keys())

            # compare list order invariant
            if not set(ref_props) == set(e_keys):
                oedge = f'{e.get_source_id()}-{e.get_target_id()}'
                oprop1 = set(ref_props).difference(e_keys)
                oprop2 = set(e_keys).difference(ref_props)
                logger.error(
                    f'At least one edge of the class {e.get_label()} '
                    f'has more or fewer properties than another. '
                    f'Offending edge: {oedge!r}, offending property: '
                    f'{max([oprop1, oprop2])}. '
                    f'All reference properties: {ref_props}, '
                    f'All edge properties: {e_keys}.',
                )
                return False

            if ref_props:

                plist = []
                # make all into strings, put actual strings in quotes
                for k, v in prop_dict.items():
                    p = e_props.get(k)
                    if p is None:  # TODO make field empty instead of ""?
                        plist.append('')
                    elif v in [
                        'int',
                        'integer',
                        'long',
                        'float',
                        'double',
                        'dbl',
                        'bool',
                        'boolean',
                    ]:
                        plist.append(str(p))
                    else:
                        if isinstance(p, list):
                            plist.append(self._write_array_string(p))
                        else:
                            plist.append(self.quote + str(p) + self.quote)

                lines.append(
                    self.delim.join(
                        [
                            e.get_source_id(),
                            # here we need a list of properties in
                            # the same order as in the header
                            self.delim.join(plist),
                            e.get_target_id(),
                            self.translator.
                            name_sentence_to_pascal(e.get_label(), ),
                        ],
                    ) + '\n',
                )
            else:
                lines.append(
                    self.delim.join(
                        [
                            e.get_source_id(),
                            e.get_target_id(),
                            self.translator.
                            name_sentence_to_pascal(e.get_label(), ),
                        ],
                    ) + '\n',
                )

        # avoid writing empty files
        if lines:
            self._write_next_part(label, lines)

        return True

    def _write_next_part(self, label: str, lines: list):
        """
        This function writes a list of strings to a new part file.

        Args:
            label (str): the label (type) of the edge; internal
            representation sentence case -> needs to become PascalCase
            for disk representation

            lines (list): list of strings to be written

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        # translate label to PascalCase
        label_pascal = self.translator.name_sentence_to_pascal(label)

        # list files in self.outdir
        files = glob.glob(
            os.path.join(self.outdir, f'{label_pascal}-part*.csv')
        )
        # find file with highest part number
        if not files:

            next_part = 0

        else:

            next_part = (
                max(
                    [
                        int(
                            f.split('.')[-2].split('-')[-1].replace('part', '')
                        ) for f in files
                    ],
                ) + 1
            )

        # write to file
        padded_part = str(next_part).zfill(3)
        logger.info(
            f'Writing {len(lines)} entries to {label_pascal}-part{padded_part}.csv',
        )

        # store name only in case import_call_file_prefix is set
        part = f'{label_pascal}-part{padded_part}.csv'
        file_path = os.path.join(
            self.outdir, part
        )

        with open(file_path, 'w', encoding='utf-8') as f:

            # concatenate with delimiter
            f.writelines(lines)

        if not self.parts.get(label):
            self.parts[label] = [part]
        else:
            self.parts[label].append(part)

    def get_import_call(self) -> str:
        """
        Function to return the import call detailing folder and
        individual node and edge headers and data files, as well as
        delimiters and database name.

        Returns:
            str: a bash command for the database import
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

        file_path = os.path.join(self.outdir, self._get_import_script_name())
        logger.info(f'Writing {self.db_name} import call to `{file_path}`.')

        with open(file_path, 'w', encoding='utf-8') as f:

            f.write(self._construct_import_call())

        return True


class _Neo4jBatchWriter(_BatchWriter):
    """
    Class for writing node and edge representations to disk using the
    format specified by Neo4j for the use of admin import. Each batch
    writer instance has a fixed representation that needs to be passed
    at instantiation via the :py:attr:`schema` argument. The instance
    also expects an ontology adapter via :py:attr:`ontology_adapter` to be able
    to convert and extend the hierarchy.

    This class inherits from the abstract class "_BatchWriter" and implements the
    Neo4j-specific methods:
        - _write_node_headers
        - _write_edge_headers
        - _construct_import_call
        - _write_array_string
    """
    def _get_default_import_call_bin_prefix(self):
        """
        Method to provide the default string for the import call bin prefix.

        Returns:
            str: The default location for the neo4j admin import location
        """
        return 'bin/'

    def _write_array_string(self, string_list):
        """
        Abstract method to write the string representation of an array into a .csv file
        as required by the neo4j admin-import.

        Args:
            string_list (list): list of ontology strings

        Returns:
            str: The string representation of an array for the neo4j admin import
        """
        string = self.adelim.join(string_list)
        return f'{self.quote}{string}{self.quote}'

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
                'Header information not found. Was the data parsed first?',
            )
            return False

        for label, props in self.node_property_dict.items():

            _id = ':ID'

            # translate label to PascalCase
            pascal_label = self.translator.name_sentence_to_pascal(label)

            header = f'{pascal_label}-header.csv'
            header_path = os.path.join(
                self.outdir,
                header,
            )
            parts = f'{pascal_label}-part.*'

            # check if file already exists
            if os.path.exists(header_path):
                logger.warning(
                    f'Header file `{header_path}` already exists. Overwriting.',
                )

            # concatenate key:value in props
            props_list = []
            for k, v in props.items():
                if v in ['int', 'long', 'integer']:
                    props_list.append(f'{k}:long')
                elif v in ['int[]', 'long[]', 'integer[]']:
                    props_list.append(f'{k}:long[]')
                elif v in ['float', 'double', 'dbl']:
                    props_list.append(f'{k}:double')
                elif v in ['float[]', 'double[]']:
                    props_list.append(f'{k}:double[]')
                elif v in ['bool', 'boolean']:
                    # TODO Neo4j boolean support / spelling?
                    props_list.append(f'{k}:boolean')
                elif v in ['bool[]', 'boolean[]']:
                    props_list.append(f'{k}:boolean[]')
                elif v in ['str[]', 'string[]']:
                    props_list.append(f'{k}:string[]')
                else:
                    props_list.append(f'{k}')

            # create list of lists and flatten
            out_list = [[_id], props_list, [':LABEL']]
            out_list = [val for sublist in out_list for val in sublist]

            with open(header_path, 'w', encoding='utf-8') as f:
                # concatenate with delimiter
                row = self.delim.join(out_list)
                f.write(row)

            # add file path to neo4 admin import statement (import call file
            # path may be different from actual file path)
            import_call_header_path = os.path.join(
                self.import_call_file_prefix,
                header,
            )
            import_call_parts_path = os.path.join(
                self.import_call_file_prefix,
                parts,
            )
            self.import_call_nodes.add((import_call_header_path, import_call_parts_path))

        return True

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
                'Header information not found. Was the data parsed first?',
            )
            return False

        for label, props in self.edge_property_dict.items():

            # translate label to PascalCase
            pascal_label = self.translator.name_sentence_to_pascal(label)

            # paths
            header = f'{pascal_label}-header.csv'
            header_path = os.path.join(
                self.outdir,
                header,
            )
            parts = f'{pascal_label}-part.*'

            # check for file exists
            if os.path.exists(header_path):
                logger.warning(
                    f'File {header_path} already exists. Overwriting.'
                )

            # concatenate key:value in props
            props_list = []
            for k, v in props.items():
                if v in ['int', 'long', 'integer']:
                    props_list.append(f'{k}:long')
                elif v in ['int[]', 'long[]', 'integer[]']:
                    props_list.append(f'{k}:long[]')
                elif v in ['float', 'double']:
                    props_list.append(f'{k}:double')
                elif v in ['float[]', 'double[]']:
                    props_list.append(f'{k}:double[]')
                elif v in [
                    'bool',
                    'boolean',
                ]:  # TODO does Neo4j support bool?
                    props_list.append(f'{k}:boolean')
                elif v in ['bool[]', 'boolean[]']:
                    props_list.append(f'{k}:boolean[]')
                elif v in ['str[]', 'string[]']:
                    props_list.append(f'{k}:string[]')
                else:
                    props_list.append(f'{k}')

            out_list = [':START_ID', *props_list, ':END_ID', ':TYPE']

            with open(header_path, 'w', encoding='utf-8') as f:
                # concatenate with delimiter
                row = self.delim.join(out_list)
                f.write(row)

            # add file path to neo4 admin import statement (import call file
            # path may be different from actual file path)
            import_call_header_path = os.path.join(
                self.import_call_file_prefix,
                header,
            )
            import_call_parts_path = os.path.join(
                self.import_call_file_prefix,
                parts,
            )
            self.import_call_edges.add((import_call_header_path, import_call_parts_path))

        return True

    def _get_import_script_name(self) -> str:
        """
        Returns the name of the neo4j admin import script

        Returns:
            str: The name of the import script (ending in .sh)
        """
        return 'neo4j-admin-import-call.sh'

    def _construct_import_call(self) -> str:
        """
        Function to construct the import call detailing folder and
        individual node and edge headers and data files, as well as
        delimiters and database name. Built after all data has been
        processed to ensure that nodes are called before any edges.

        Returns:
            str: a bash command for neo4j-admin import
        """
        import_call = (
            f'{self.import_call_bin_prefix}neo4j-admin import '
            f'--database={self.db_name} '
            f'--delimiter="{self.escaped_delim}" '
            f'--array-delimiter="{self.escaped_adelim}" '
        )

        if self.quote == "'":
            import_call += f'--quote="{self.quote}" '
        else:
            import_call += f"--quote='{self.quote}' "

        if self.wipe:
            import_call += f'--force=true '
        if self.skip_bad_relationships:
            import_call += '--skip-bad-relationships=true '
        if self.skip_duplicate_nodes:
            import_call += '--skip-duplicate-nodes=true '

        # append node import calls
        for header_path, parts_path in self.import_call_nodes:
            import_call += f'--nodes="{header_path},{parts_path}" '

        # append edge import calls
        for header_path, parts_path in self.import_call_edges:
            import_call += f'--relationships="{header_path},{parts_path}" '

        return import_call


class _ArangoDBBatchWriter(_Neo4jBatchWriter):
    """
    Class for writing node and edge representations to disk using the format
    specified by ArangoDB for the use of "arangoimport". Output files are
    similar to Neo4j, but with a different header format.
    """
    def _get_default_import_call_bin_prefix(self):
        """
        Method to provide the default string for the import call bin prefix.

        Returns:
            str: The default location for the neo4j admin import location
        """
        return ''

    def _get_import_script_name(self) -> str:
        """
        Returns the name of the neo4j admin import script

        Returns:
            str: The name of the import script (ending in .sh)
        """
        return 'arangodb-import-call.sh'

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
                'Header information not found. Was the data parsed first?',
            )
            return False

        for label, props in self.node_property_dict.items():
            # create header CSV with ID, properties, labels

            _id = '_key'

            # translate label to PascalCase
            pascal_label = self.translator.name_sentence_to_pascal(label)

            header = f'{pascal_label}-header.csv'
            header_path = os.path.join(
                self.outdir,
                header,
            )

            # check if file already exists
            if os.path.exists(header_path):
                logger.warning(
                    f'File {header_path} already exists. Overwriting.'
                )

            # concatenate key:value in props
            props_list = []
            for k in props.keys():

                props_list.append(f'{k}')

            # create list of lists and flatten
            # removes need for empty check of property list
            out_list = [[_id], props_list]
            out_list = [val for sublist in out_list for val in sublist]

            with open(header_path, 'w', encoding='utf-8') as f:
                # concatenate with delimiter
                row = self.delim.join(out_list)
                f.write(row)

            # add collection from schema config
            collection = self.extended_schema[label].get(
                'db_collection_name', None
            )

            # add file path to neo4 admin import statement
            # do once for each part file
            parts = self.parts.get(label, [])

            if not parts:

                raise ValueError(
                    f'No parts found for node label {label}. '
                    f'Check that the data was parsed first.',
                )

            for part in parts:
                
                import_call_header_path = os.path.join(
                    self.import_call_file_prefix,
                    header,
                )
                import_call_parts_path = os.path.join(
                    self.import_call_file_prefix,
                    part,
                )

                self.import_call_nodes.add((import_call_header_path, import_call_parts_path, collection))

        return True

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
                'Header information not found. Was the data parsed first?',
            )
            return False

        for label, props in self.edge_property_dict.items():

            # translate label to PascalCase
            pascal_label = self.translator.name_sentence_to_pascal(label)

            # paths
            header = f'{pascal_label}-header.csv'
            header_path = os.path.join(
                self.outdir,
                header,
            )
            parts = f'{pascal_label}-part.*'

            # check for file exists
            if os.path.exists(header_path):
                logger.warning(
                    f'Header file {header_path} already exists. Overwriting.'
                )

            # concatenate key:value in props
            props_list = []
            for k in props.keys():

                props_list.append(f'{k}')

            out_list = ['_from', *props_list, '_to']

            with open(header_path, 'w', encoding='utf-8') as f:
                # concatenate with delimiter
                row = self.delim.join(out_list)
                f.write(row)

            # add collection from schema config
            if not self.extended_schema.get(label):

                for _, v in self.extended_schema.items():
                    if v.get('label_as_edge') == label:
                        collection = v.get('db_collection_name', None)
                        break

            else:

                collection = self.extended_schema[label].get(
                    'db_collection_name', None
                )

            # add file path to neo4 admin import statement (import call path
            # may be different from actual output path)
            header_import_call_path = os.path.join(
                self.import_call_file_prefix,
                header,
            )
            parts_import_call_path = os.path.join(
                self.import_call_file_prefix,
                parts,
            )
            self.import_call_edges.add((header_import_call_path, parts_import_call_path, collection,))

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
        import_call = (
            f'{self.import_call_bin_prefix}arangoimp '
            f'--type csv '
            f'--separator="{self.escaped_delim}" '
        )

        if self.quote == "'":
            import_call += f'--quote="{self.quote}" '
        else:
            import_call += f"--quote='{self.quote}' "

        node_lines = ''

        # node import calls: one line per node type
        for header_path, parts_path, collection in self.import_call_nodes:

            line = (
                f'{import_call} '
                f'--headers-file {header_path} '
                f'--file= {parts_path} '
            )

            if collection:
                line += f'--create-collection --collection {collection} '

            node_lines += f'{line}\n'

        edge_lines = ''

        # edge import calls: one line per edge type
        for header_path, parts_path, collection in self.import_call_edges:
            import_call += f'--relationships="{header_path},{parts_path}" '

        return node_lines + edge_lines


class _PostgreSQLBatchWriter(_BatchWriter):
    """
    Class for writing node and edge representations to disk using the
    format specified by PostgreSQL for the use of "COPY FROM...". Each batch
    writer instance has a fixed representation that needs to be passed
    at instantiation via the :py:attr:`schema` argument. The instance
    also expects an ontology adapter via :py:attr:`ontology_adapter` to be able
    to convert and extend the hierarchy.

    This class inherits from the abstract class "_BatchWriter" and implements the
    PostgreSQL-specific methods:
        - _write_node_headers
        - _write_edge_headers
        - _construct_import_call
        - _write_array_string
    """

    DATA_TYPE_LOOKUP = {
        'str': 'VARCHAR',  # VARCHAR needs limit
        'int': 'INTEGER',
        'long': 'BIGINT',
        'float': 'NUMERIC',
        'double': 'NUMERIC',
        'dbl': 'NUMERIC',
        'boolean': 'BOOLEAN',
        'str[]': 'VARCHAR[]',
        'string[]': 'VARCHAR[]'
    }

    def __init__(self, *args, **kwargs):
        self._copy_from_csv_commands = set()
        super().__init__(*args, **kwargs)

    def _get_default_import_call_bin_prefix(self):
        """
        Method to provide the default string for the import call bin prefix.

        Returns:
            str: The default location for the psql command
        """
        return ''

    def _get_data_type(self, string) -> str:
        try:
            return self.DATA_TYPE_LOOKUP[string]
        except KeyError:
            logger.info(
                'Could not determine data type {string}. Using default "VARCHAR"'
            )
            return 'VARCHAR'

    def _write_array_string(self, string_list) -> str:
        """
        Abstract method to write the string representation of an array into a .csv file
        as required by the postgresql COPY command, with '{','}' brackets and ',' separation.

        Args:
            string_list (list): list of ontology strings

        Returns:
            str: The string representation of an array for postgres COPY
        """
        string = ','.join(string_list)
        string = f'"{{{string}}}"'
        return string

    def _get_import_script_name(self) -> str:
        """
        Returns the name of the psql import script

        Returns:
            str: The name of the import script (ending in .sh)
        """
        return f'{self.db_name}-import-call.sh'

    def _adjust_pascal_to_psql(self, string):
        string = string.replace('.', '_')
        string = string.lower()
        return string

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
                'Header information not found. Was the data parsed first?',
            )
            return False

        for label, props in self.node_property_dict.items():
            # create header CSV with ID, properties, labels

            # translate label to PascalCase
            pascal_label = self.translator.name_sentence_to_pascal(label)

            parts = f'{pascal_label}-part*.csv'
            parts_paths = os.path.join(self.outdir, parts)
            parts_paths = glob.glob(parts_paths)
            parts_paths.sort()

            # adjust label for import to psql
            pascal_label = self._adjust_pascal_to_psql(pascal_label)
            table_create_command_path = os.path.join(
                self.outdir,
                f'{pascal_label}-create_table.sql',
            )

            # check if file already exists
            if os.path.exists(table_create_command_path):
                logger.warning(
                    f'File {table_create_command_path} already exists. Overwriting.',
                )

            # concatenate key:value in props
            columns = ['_ID VARCHAR']
            for col_name, col_type in props.items():
                col_type = self._get_data_type(col_type)
                col_name = self._adjust_pascal_to_psql(col_name)
                columns.append(f'{col_name} {col_type}')
            columns.append('_LABEL VARCHAR[]')

            with open(table_create_command_path, 'w', encoding='utf-8') as f:

                command = ''
                if self.wipe:
                    command += f'DROP TABLE IF EXISTS {pascal_label};\n'

                # table creation requires comma separation
                command += f'CREATE TABLE {pascal_label}({",".join(columns)});\n'
                f.write(command)

                for parts_path in parts_paths:
                    
                    # if import_call_file_prefix is set, replace actual path 
                    # with prefix
                    if self.import_call_file_prefix != self.outdir:
                        parts_path = parts_path.replace(
                            self.outdir,
                            self.import_call_file_prefix,
                        )

                    self._copy_from_csv_commands.add(
                        f'\\copy {pascal_label} FROM \'{parts_path}\' DELIMITER E\'{self.delim}\' CSV;'
                    )

            # add file path to import statement
            # if import_call_file_prefix is set, replace actual path
            # with prefix
            if self.import_call_file_prefix != self.outdir:
                table_create_command_path = table_create_command_path.replace(
                    self.outdir,
                    self.import_call_file_prefix,
                )

            self.import_call_nodes.add(table_create_command_path)

        return True

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
                'Header information not found. Was the data parsed first?',
            )
            return False

        for label, props in self.edge_property_dict.items():

            # translate label to PascalCase
            pascal_label = self.translator.name_sentence_to_pascal(label)

            parts_paths = os.path.join(self.outdir, f'{pascal_label}-part*.csv')
            parts_paths = glob.glob(parts_paths)
            parts_paths.sort()

            # adjust label for import to psql
            pascal_label = self._adjust_pascal_to_psql(pascal_label)
            table_create_command_path = os.path.join(
                self.outdir,
                f'{pascal_label}-create_table.sql',
            )

            # check for file exists
            if os.path.exists(table_create_command_path):
                logger.warning(
                    f'File {table_create_command_path} already exists. Overwriting.',
                )

            # concatenate key:value in props
            columns = []
            for col_name, col_type in props.items():
                col_type = self._get_data_type(col_type)
                col_name = self._adjust_pascal_to_psql(col_name)
                columns.append(f'{col_name} {col_type}')

            # create list of lists and flatten
            # removes need for empty check of property list
            out_list = [
                '_START_ID VARCHAR', *columns, '_END_ID VARCHAR',
                '_TYPE VARCHAR'
            ]

            with open(table_create_command_path, 'w', encoding='utf-8') as f:
                command = ''
                if self.wipe:
                    command += f'DROP TABLE IF EXISTS {pascal_label};\n'

                # table creation requires comma separation
                command += f'CREATE TABLE {pascal_label}({",".join(out_list)});\n'
                f.write(command)

                for parts_path in parts_paths:

                    # if import_call_file_prefix is set, replace actual path
                    # with prefix
                    if self.import_call_file_prefix != self.outdir:
                        parts_path = parts_path.replace(
                            self.outdir,
                            self.import_call_file_prefix,
                        )

                    self._copy_from_csv_commands.add(
                        f'\\copy {pascal_label} FROM \'{parts_path}\' DELIMITER E\'{self.delim}\' CSV;'
                    )

            # add file path to import statement
            # if import_call_file_prefix is set, replace actual path
            # with prefix
            if self.import_call_file_prefix != self.outdir:
                table_create_command_path = table_create_command_path.replace(
                    self.outdir,
                    self.import_call_file_prefix,
                )
                
            self.import_call_edges.add(table_create_command_path)

        return True

    def _construct_import_call(self) -> str:
        """
        Function to construct the import call detailing folder and
        individual node and edge headers and data files, as well as
        delimiters and database name. Built after all data has been
        processed to ensure that nodes are called before any edges.

        Returns:
            str: a bash command for postgresql import
        """
        import_call = ''

        # create tables
        # At this point, csv files of nodes and edges do not require differentiation
        for import_file_path in [
            *self.import_call_nodes, *self.import_call_edges
        ]:
            import_call += f'echo "Setup {import_file_path}..."\n'
            if {self.db_password}:
                # set password variable inline
                import_call += f'PGPASSWORD={self.db_password} '
            import_call += f'{self.import_call_bin_prefix}psql -f {import_file_path}'
            import_call += f' --dbname {self.db_name}'
            import_call += f' --port {self.db_port}'
            import_call += f' --user {self.db_user}'
            import_call += '\necho "Done!"\n'
            import_call += '\n'

        # copy data to tables
        for command in self._copy_from_csv_commands:
            table_part = command.split(' ')[3]
            import_call += f'echo "Importing {table_part}..."\n'
            if {self.db_password}:
                # set password variable inline
                import_call += f'PGPASSWORD={self.db_password} '
            import_call += f'{self.import_call_bin_prefix}psql -c "{command}"'
            import_call += f' --dbname {self.db_name}'
            import_call += f' --port {self.db_port}'
            import_call += f' --user {self.db_user}'
            import_call += '\necho "Done!"\n'
            import_call += '\n'

        return import_call


DBMS_TO_CLASS = {
    'neo': _Neo4jBatchWriter,
    'neo4j': _Neo4jBatchWriter,
    'Neo4j': _Neo4jBatchWriter,
    'postgres': _PostgreSQLBatchWriter,
    'postgresql': _PostgreSQLBatchWriter,
    'PostgreSQL': _PostgreSQLBatchWriter,
    'arango': _ArangoDBBatchWriter,
    'arangodb': _ArangoDBBatchWriter,
    'ArangoDB': _ArangoDBBatchWriter,
}


def get_writer(
    dbms: str,
    translator: 'Translator',
    ontology: 'Ontology',
    deduplicator: 'Deduplicator',
    output_directory: str,
    strict_mode: bool,
):
    """
    Function to return the writer class based on the selection in the config
    file.

    Args:

        dbms: the database management system; for options, see DBMS_TO_CLASS.

        translator: the Translator object.

        ontology: the Ontology object.

        output_directory: the directory to write the output files to.

        strict_mode: whether to use strict mode.

    Returns:

        instance: an instance of the selected writer class.

    """

    dbms_config = _config(dbms)

    timestamp = lambda: datetime.now().strftime('%Y%m%d%H%M%S')
    outdir = output_directory or os.path.join('biocypher-out', timestamp())
    outdir = os.path.abspath(outdir)

    writer = DBMS_TO_CLASS[dbms]

    if not writer:
        raise ValueError(f'Unknown dbms: {dbms}')

    if writer is not None:
        return writer(
            ontology=ontology,
            translator=translator,
            deduplicator=deduplicator,
            delimiter=dbms_config.get('delimiter'),
            array_delimiter=dbms_config.get('array_delimiter'),
            quote=dbms_config.get('quote_character'),
            output_directory=outdir,
            db_name=dbms_config.get('database_name'),
            import_call_bin_prefix=dbms_config.get('import_call_bin_prefix'),
            import_call_file_prefix=dbms_config.get('import_call_file_prefix'),
            wipe=dbms_config.get('wipe'),
            strict_mode=strict_mode,
            skip_bad_relationships=dbms_config.get('skip_bad_relationships'
                                                  ),  # neo4j
            skip_duplicate_nodes=dbms_config.get('skip_duplicate_nodes'
                                                ),  # neo4j
            db_user=dbms_config.get('user'),  # psql
            db_password=dbms_config.get('password'),  # psql
            db_port=dbms_config.get('port'),  # psql
        )
