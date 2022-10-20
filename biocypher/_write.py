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

logger.debug(f'Loading module {__name__}.')

from typing import Any, Iterable, Literal, TYPE_CHECKING, Union, Optional
from datetime import datetime
from collections import OrderedDict, defaultdict
import os
import re

import ._misc as _misc
from biocypher._config import config as _config
from ._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode

__all__ = ['BatchWriter']

if TYPE_CHECKING:

    from ._translate import BiolinkAdapter

N4_ALL_TYPES = {
    'int',
    'long',
    'float',
    'double',
    'boolean',
    'byte',
    'short',
    'char',
    'string',
    'point',
    'date',
    'localtime',
    'time',
    'localdatetime',
    'datetime',
    'duration',
}

N4_TYPES = {
    'long': ('int', 'long'),
    'double': ('double', 'float', 'dbl'),
    'boolean': ('bool', 'boolean'),
    'string': ('str',),
}

PY_TYPES = {py: n4 for n4, pys in N4_TYPES.items() for py in pys}
BATCH_SIZE_FALLBACK = int(1e6)

# TODO retrospective check of written csvs?


class BatchWriter:
    """
    Write node and edge representations to disk using the
    format specified by Neo4j for the use of admin import. Each batch
    writer instance has a fixed representation that needs to be passed
    at instantiation via the :py:attr:`schema` argument. The instance
    also expects a biolink adapter via :py:attr:`bl_adapter` to be able
    to convert and extend the hierarchy.
    """

    def __init__(
        self,
        leaves: dict,
        bl_adapter: 'BiolinkAdapter',
        delimiter: str | None = None,
        array_delimiter: str | None = None,
        quote: str | None = None,
        dirname: Optional[str] = None,
        db_name: str = 'neo4j',
        skip_bad_relationships: bool = False,
        skip_duplicate_nodes: bool = False,
        batch_size: int | None = None,
    ):
        """
        Export data into CSV for *neo4j-admin* import.

        Args:
            leaves:
                The BioCypher graph schema (from :py:class:`VersionNode`).
            bl_adapter:
                Instance of :py:class:`BiolinkAdapter` to enable translation
                and ontology queries
            delimiter:
                Character to separate the fields in CSV files.
            array_delimiter:
                Character to separate elements of arrays within CSV fields.
            quote:
                Character to enclose string fields in CSV files.
            dirname:
                Path for exporting CSV files.
            db_name:
                Name of the Neo4j database that will be used in the generated
                commands.
            skip_bad_relationships:
                Behaviour when encountering erroneous relationships.
            skip_duplicate_nodes:
                Behaviour when encountering duplicate nodes.
            batch_size:
                Number of records in one CSV. Override here the value defined
                in the config.

        Attributes:
            seen_node_ids:
                Dictionary to store the ids of nodes that have already been
                written; to avoid duplicates. keys: ids, values: amount of
                duplicates
            duplicate_node_types:
                Set to store the types of nodes that have been found to have
                duplicates.
            seen_edges:
                Dict to store the set of edges that have already been written;
                to avoid duplicates; per edge type. Keys: ids, values: count.
            duplicate_edge_types:
                Set to store the types of nodes that have been found to have
                duplicates.
            property_types:
                Dict to store a dict of properties for each label to check for
                consistency and their type for now, relevant for `int`.
        """
        self.db_name = db_name

        self.delim = delimiter or _conf('csv_delimiter')
        self.adelim = array_delimiter or _conf('csv_array_delimiter')
        self.quote = quote or _conf('csv_quote_char')
        self.batch_size = batch_size or _conf('csv_batch_size')

        self.skip_bad_relationships = skip_bad_relationships
        self.skip_duplicate_nodes = skip_duplicate_nodes

        self.leaves = leaves
        self.bl_adapter = bl_adapter
        self.set_outdir(dirname)
        self.reset()

    def set_outdir(self, path: str | None = None):
        """
        Set and create the output directory where CSV files will be written.

        Args:
            path:
                Use it to override the value from config.
        """

        timestamp = datetime.now().strftime('%Y%m%d%H%M')
        self.outdir = path or os.path.join(_config('outdir'), timestamp)
        self.outdir = os.path.abspath(self.outdir)

        logger.info(f'Creating output directory `{self.outdir}`.')
        os.makedirs(self.outdir, exist_ok=True)

    def reset(self):
        """
        Creates empty data structures for the writing process.

        This object works by preprocessing data and writing it into multiple
        CSV files in batches, and creating CLI commands that can be used to
        import the CSV files into a Neo4j database. This method drops all
        previously preprocessed data and creates a clean environment for
        further processing tasks.
        """

        self.property_types = {'node': {}, 'edge': {}}
        self.cli_call = {'node': [], 'edge': []}
        self.seen = {'nodes': defaultdict(int), 'edges': defaultdict(int)}
        self.duplicate_types = {'nodes': set(), 'edges': set()}

    def get_duplicate_node_types(self) -> set:
        """
        Returns:
            The set of node types that have been found to have duplicates.
        """
        return self.duplicate_node_types

    def get_duplicate_nodes(self) -> dict:
        """
        Summary of duplicate nodes found.

        Returns:
            Duplicate node types and the number of duplicates.
        """

        if self.duplicate_node_types:
            # subset seen_node_ids dictionary based on values > 0

            return {
                nid: count
                for nid, count in self.seen_node_ids.items()
                if count > 0
            }

    def get_duplicate_edge_types(self) -> set:
        """
        Returns:
            The set of edge types that have been found to have duplicates.
        """
        return self.duplicate_edge_types

    def get_duplicate_edges(self) -> dict:
        """
        Returns a dict of duplicate edge types and the number of duplicates.
        """

        if self.duplicate_edge_types:
            # subset seen_edges dictionary based on values > 0

            return {
                nid: count
                for nid, count in self.seen_edges.items()
                if count > 0
            }

    def write_nodes(
            self,
            nodes: Iterable[BioCypherNode],
            batch_size: int | None = None,
        ) -> bool:
        """
        Top level method for writing nodes and their headers.

        Args:
            nodes:
                Iterable of nodes, each represented as
                :py:class:`BioCypherNode` instance.

        Returns:
            True for success, False otherwise.
        """
        # TODO check represented_as

        batch_size = self._batch_size(batch_size)

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
        edges: Iterable[BioCypherEdge],
        batch_size: int | None = None,
    ) -> bool:
        """
        Top level method for writing edges and their headers.

        Args:
            edges:
                Iterable of edges, each represented as a
                :py:class:`BioCypherEdge` or :py:class:`BioCypherRelAsNode`
                instance.
            batch_size:
                Number of records in one CSV file.

        Returns:
            True for success, False otherwise.
        """

        bs = batch_size = self._batch_size(batch_size)

        edges = _misc.to_list(edges)
        nodes = (n for ee in edges for n in ee.nodes)
        edges = (e for ee in edges for e in ee.edges)

        return (
            self.write_nodes(nodes, batch_size = bs) and
            self._write_edge_data(edges, batch_size = bs) and
            self._write_edge_headers()
        )

    def _write_node_data(
            self,
            nodes: Iterable[BioCypherNode],
            batch_size: int | None = None,
        ) -> bool:
        """
        Writes biocypher nodes to CSV conforming to the headers created
        with `_write_node_headers()`, and is actually required to be run
        before calling `_write_node_headers()` to set the
        :py:attr:`self.node_property_dict` for passing the node properties
        to the instance. Expects list or generator of nodes from the
        :py:class:`BioCypherNode` class.

        Args:
            nodes:
                An iterable of nodes, each represented by a
                :py:class:`BioCypherNode` instance.

        Returns:
            True for success, False otherwise.
        """

        if not isinstance(nodes, _misc.LIST_LIKE):

            # is this error worth to check? if this value is not
            # iterable at all, that means some huge and obvious error
            # that raises a type error just a few lines below anyways
            logger.error('Nodes must be passed as list or generator.')
            return False

        logger.debug('Writing node CSV from generator.')

        by_label = defaultdict(list)  # dict to store a list for each
                                      # label that is passed in
        labels = {}  # dict to store the additional labels for each
                     # primary graph constituent from biolink hierarchy
        batch_size = self._batch_size(batch_size)

        for node in nodes:

            _id = node.get_id()
            self.seen_node_ids[_id] += 1
            label = node.get_label()

            # how would it be possible for a node not to have an id?
            # shouldn't we check in the translation step, instead of
            # at writing a csv?
            # check for non-id
            if not _id:

                logger.warning(
                    f'Node [{_misc.dict_str(node.get_dict())}] '
                    'has no id; skipping.'
                )
                continue

            # check if node has already been written, if so skip
            if self.seen_node_ids[_id] > 1:

                self.duplicate_node_types.add(label)
                continue

            by_label[label].append(node)

            if label not in by_label:
                # else use first encountered node to define properties for
                # checking; could later be by checking all nodes but much
                # more complicated, particularly involving batch writing
                # (would require "do-overs"). for now, we output a warning
                # if node properties diverge from reference properties (in
                # write_single_node_list_to_file) TODO if it occurs, ask
                # user to select desired properties and restart the process
                self._property_types(label = label, instance = node)

                all_labels = (
                    self.bl_adapter.biolink_leaves.
                    get(label, {}).
                    get('ancestors')
                ) or (label,)
                all_labels = OrderedDict.fromkeys(all_labels)
                all_labels = self.adelim.join(all_labels)
                labels[label] = all_labels

            if len(counts_by_label[label]) >= batch_size:

                # batch size controlled here
                passed = self._write_node_batch(
                    by_label[label],
                    label,
                    self.property_types['node'][label],
                    labels[label],
                )

                if not passed:

                    return False

                by_label[label] = []
                counts_by_label[label] = 0

        # after generator depleted, write remainder of by_label
        for label, lnodes in by_label.items():

            passed = self._write_node_batch(
                lnodes,
                label,
                self.property_types['node'][label],
                labels[label],
            )

            if not passed:

                return False

        # --- where this comment belongs to?
        # use complete bin list to write header files
        # TODO if a node type has varying properties
        # (ie missingness), we'd need to collect all possible
        # properties in the generator pass
        return True

    def _property_types(
            self,
            label: str,
            instance: BioCypherNode | BioCypherEdge | None = None,
            node_edge: Literal['node', 'edge'] = 'node',
        ):

        propt = {}
        # get properties from config if present
        from_conf = self.bl_adapter.leaves.get(label).get('properties')

        if from_conf:

            propt = dict(from_conf)
            # add id and preferred id to properties; these are
            # created in node creation (`_create.BioCypherNode`)
            propt.update({'id': 'str', 'preferred_id': 'str'})

        elif instance:

            propt = {
                k: v.__class__.__name__
                for k, v in instance.get_properties()
                if k is not None  # why would be a key here None?
            }

        self.property_types[node_edge][label] = propt

    def _batch_size(self, override: int | None = None) -> int:
        """
        Batch size from the currently valid config.
        """

        return override or self._batch_size or BATCH_SIZE_FALLBACK

    def _write_node_headers(self) -> bool:
        """
        Writes single CSV file for a graph entity that is represented
        as a node as per the definition in the `schema_config.yaml`,
        containing only the header for this type of node.

        Returns:
            True for success, False otherwise.
        """
        # load headers from data parse
        if not self.property_types.get('nodes'):

            logger.error(
                'Header information not found. Was the data parsed first?',
            )
            return False

        for label, props in self.property_types['nodes'].items():

            # to programmatically define properties to be written, the
            # data would have to be parsed before writing the header.
            # alternatively, desired properties can also be provided
            # via the schema_config.yaml.

            # translate label to PascalCase
            label = self.bl_adapter.name_sentence_to_pascal(label)
            header_path = os.path.join(self.outdir, f'{label}-header.csv')
            parts_path = os.path.join(self.outdir, f'{label}-part.*')

            # check if file already exists
            if not os.path.exists(header_path):

                # add column types

                header = [':ID']
                header.extend(
                    f'{prop}{self._col_type(py_t)}'
                    for prop, py_t in props.items()
                )
                header.append(':LABEL')

                with open(header_path, 'w') as f:

                    # concatenate with delimiter
                    f.write(self.delim.join(header))

                # add file path to neo4 admin import statement
                self.import_call_nodes += (
                    f'--nodes="{header_path},{parts_path}" '
                )

        return True

    @staticmethod
    def _col_type(py_type: str | type) -> str:
        """
        Neo4j column types as used in the CSV header notation.

        Args:
            py_type:
                A type or its name.

        Returns:
            A type annotation that can be appended to the CSV column label.
        """

        py_type = py_type.__name__ if isinstance(py_type, type) else py_type
        n4_type = PY_TYPES.get(
            py_type,
            py_type if py_type in N4_ALL_TYPES else None,
        )

        return f'{":" if n4_type else ""}{n4_type}'

    def _write_node_batch(
            self,
            nodes: Iterable[BioCypherNode],
            label: str,
            labels: str,
        ) -> bool:
        """
        This function takes one list of biocypher nodes and writes them
        to a Neo4j admin import compatible CSV file.

        Args:
            nodes:
                Iterable of ``BioCypherNode`` instances.
            label:
                The primary label of the nodes.
            labels:
                String of one or several concatenated labels
                for the node class.

        Returns:
            True for success, False otherwise.
        """
        if not all(isinstance(n, BioCypherNode) for n in nodes):

            logger.error('Nodes must be passed as type BioCypherNode.')
            return False

        # from list of nodes to list of strings
        lines = []

        for n in nodes:

            # check for deviations in properties
            # node properties
            props = n.get_properties()
            ptypes = self.property_types['nodes'][label]
            missing = set(ptypes.keys()) - set(props.keys())
            excess = set(props.keys()) - set(ptypes.keys())

            if missing:

                logger.error(
                    f'One `{n.get_label()}` node with ID `{n.get_id()}` is '
                    f'missing the following properties: {", ".join(missing)}.'
                )
                return False

            if excess:

                logger.error(
                    f'One `{n.get_label()}` node with ID `{n.get_id()}` has t'
                    f'he following unexpected properties: {", ".join(excess)}.'
                )
                return False

            line = [n.get_id()]
            line.extend(
                self._proc_prop(props.get(prop), py_type)
                for prop, py_type in ptypes.items()
            )
            line.append(labels)
            lines.append(self.delim.join(line))

        self._write_batch(label, lines)

        return True

    def _proc_prop(self, value: Any, py_type: str | type) -> str:
        """
        Process a property value.

        Converts a property value to string and adds quotes if the column
        type is string.
        """

        n4_type = self._col_type(py_type)
        q = self.quote if n4_type == 'string' else ''
        # make all into strings, put actual strings in quotes
        value = '' if value is None else str(value)

        return f'{q}{value}{q}'

    def _write_edge_data(
            self,
            edges: Iterable[BioCypherEdge],
            batch_size: int | None = None,
        ) -> bool:
        """
        Writes biocypher edges to CSV conforming to the headers created
        with `_write_edge_headers()`, and is actually required to be run
        before calling `_write_node_headers()` to set the
        :py:attr:`self.edge_property_dict` for passing the edge
        properties to the instance. Expects list or generator of edges
        from the :py:class:`BioCypherEdge` class.

        Args:
            edges:
                Iterable of edges, each represented as
                :py:class:`BioCypherEdge`.

        Returns:
            True for success, False otherwise.

        Todo:
            - currently works for mixed edges but in practice often is
              called on one iterable containing one type of edge only
        """

        # TODO not memory efficient, but should be fine for most cases; is
        # there a more elegant solution?

        batch_size = self._batch_size(batch_size)

        if isinstance(edges, _misc.LIST_LIKE):

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
            for e in edges:
                if isinstance(e, BioCypherRelAsNode):
                    # shouldn't happen any more
                    logger.error(
                        "Edges cannot be of type 'RelAsNode'. "
                        f'Caused by: {e}',
                    )
                    return False

                if not (e.get_source_id() and e.get_target_id()):
                    logger.error(
                        'Edge must have source and target node. '
                        f'Caused by: {e}',
                    )
                    continue

                label = e.get_label()

                src_tar_ids = ' -> '.join(
                    [e.get_source_id(), e.get_target_id()],
                )

                # check for duplicates
                if src_tar_ids in self.seen_edges.keys():
                    self.seen_edges[src_tar_ids] += 1
                    if not label in self.duplicate_node_types:
                        self.duplicate_edge_types.add(label)
                        # logger.warning(
                        #     f"Duplicate edges found in type {label}. "
                        #     "More info can be found in the log file."
                        # )
                    continue

                else:
                    self.seen_edges[src_tar_ids] = 0

                if not label in bins.keys():
                    # start new list
                    bins[label].append(e)
                    bin_l[label] = 1

                    # get properties from config if present

                    # check whether label is in bl_adapter.leaves
                    # (may not be if it is an edge that carries the
                    # "label_as_edge" property)
                    cprops = None
                    if label in self.bl_adapter.leaves:
                        cprops = self.bl_adapter.leaves.get(label).get(
                            'properties',
                        )
                    else:
                        # try via "label_as_edge"
                        for k, v in self.bl_adapter.leaves.items():
                            if isinstance(v, dict):
                                if v.get('label_as_edge') == label:
                                    cprops = v.get('properties')
                                    break
                    if cprops:
                        d = cprops
                    else:
                        d = dict(e.get_properties())
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
                    bins[label].append(e)
                    bin_l[label] += 1
                    if not bin_l[label] < batch_size:
                        # batch size controlled here
                        passed = self._write_edge_batch(
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

                passed = self._write_edge_batch(
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
            # create header CSV with :START_ID, (optional) properties,
            # :END_ID, :TYPE

            # translate label to PascalCase
            pascal_label = self.bl_adapter.name_sentence_to_pascal(label)

            # paths
            header_path = os.path.join(
                self.outdir, f'{pascal_label}-header.csv',
            )
            parts_path = os.path.join(self.outdir, f'{pascal_label}-part.*')

            # check for file exists
            if not os.path.exists(header_path):

                # concatenate key:value in props
                props_list = []
                for k, v in props.items():
                    if v in ['int', 'long']:
                        props_list.append(f'{k}:long')
                    elif v in ['float', 'double']:
                        props_list.append(f'{k}:double')
                    elif v in [
                        'bool',
                        'boolean',
                    ]:  # TODO does Neo4j support bool?
                        props_list.append(f'{k}:boolean')
                    else:
                        props_list.append(f'{k}')

                # create list of lists and flatten
                # removes need for empty check of property list
                out_list = [[':START_ID'], props_list, [':END_ID'], [':TYPE']]
                out_list = [val for sublist in out_list for val in sublist]

                with open(header_path, 'w') as f:

                    # concatenate with delimiter
                    row = self.delim.join(out_list)
                    f.write(row)

                # add file path to neo4 admin import statement
                self.import_call_edges += (
                    f'--relationships="{header_path},{parts_path}" '
                )

        return True

    def _write_edge_batch(
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
                        'long',
                        'float',
                        'double',
                        'dbl',
                        'bool',
                        'boolean',
                    ]:
                        plist.append(str(p))
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
                            self.bl_adapter.name_sentence_to_pascal(
                                e.get_label(),
                            ),
                        ],
                    )
                    + '\n',
                )
            else:
                lines.append(
                    self.delim.join(
                        [
                            e.get_source_id(),
                            e.get_target_id(),
                            self.bl_adapter.name_sentence_to_pascal(
                                e.get_label(),
                            ),
                        ],
                    )
                    + '\n',
                )

        self._write_batch(label, lines)

        return True

    def _write_batch(self, label: str, lines: list[str]):
        """
        This function writes a list of strings to a new part file.

        Args:
            label:
                The label (type) of the edge; internal representation
                in sentence case -> will change to PascalCase before
                writing to CSV.
            lines:
                The lines to be written.
        """

        # avoid writing empty files
        if not lines: return

        # translate label to PascalCase
        label = self.bl_adapter.name_sentence_to_pascal(label)

        # list files in self.outdir
        files = glob.glob(os.path.join(self.outdir, f'{label}-part*.csv'))
        repart = re.compile('part(\d+)')

        idx = max([int(repart.search(f).group(1)) for f in files] + [-1]) + 1

        # write to file
        path = os.path.join(self.outdir, f'{label}-part{idx:03d}.csv')
        logger.info(f'Writing {len(lines)} entries to `{path}`.')

        with open(path, 'w') as fp:
            # concatenate with delimiter
            fp.write(os.linesep.join(lines))

        return True

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

        file_path = os.path.join(self.outdir, 'neo4j-admin-import-call.sh')
        logger.info(f'Writing neo4j-admin import call to `{file_path}`.')

        with open(file_path, 'w') as f:

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

        import_call = (
            f'neo4j-admin import --database={self.db_name} '
            f'--delimiter="{self.delim}" --array-delimiter="{self.adelim}" '
        )
        if not self.quote == '"':
            import_call += f'--quote="{self.quote}" '
        else:
            import_call += f"--quote='{self.quote}' "

        if self.skip_bad_relationships:
            import_call += '--skip-bad-relationships=true '
        if self.skip_duplicate_nodes:
            import_call += '--skip-duplicate-nodes=true '

        # append node and edge import calls
        import_call += self.import_call_nodes
        import_call += self.import_call_edges

        return import_call
