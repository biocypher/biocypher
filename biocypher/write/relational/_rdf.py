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

from types import GeneratorType
from typing import Union, Optional

from collections import OrderedDict, defaultdict
from rdflib import Literal, RDFS, URIRef, Namespace, RDF, Graph
import os

from more_itertools import peekable

# from ._config import config as _config
from biocypher._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode
from biocypher._logger import logger
from biocypher.write._batch_writer import _BatchWriter
 
class _RDFwriter(_BatchWriter):
    
    """
    Class to write BioCypher's property graph into an RDF format using
    rdflib and all the extensions it supports (RDF/XML, N3, NTriples, 
    N-Quads, Turtle, TriX, Trig and JSON-LD). By default the conversion
    is done keeping only the minimum information about node and edges,
    skipping all properties.
    """

    def _get_import_script_name(self) -> str:
        """
        Returns the name of the neo4j admin import script

        Returns:
            str: The name of the import script (ending in .sh)
        """
        return "rdf-import-call.sh"
    
    def _get_default_import_call_bin_prefix(self):
        """
        Method to provide the default string for the import call bin prefix.

        Returns:
            str: The default location for the neo4j admin import location
        """
        return "bin/"
    
    def _get_rdf_format(self, string) -> bool:
        """
        Function to check if the specified RDF format is supported.

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        formats = ["xml", "n3", "turtle", "nt", "pretty-xml", "trix", "trig", "nquads", "json-ld"]
        if string not in formats:
            logger.error(
                f'{string}; Incorrect or unsupported RDF format, use one of the following: '
                f'"xml", "n3", "turtle", "nt", "pretty-xml", "trix", "trig", "nquads", "json-ld" ',
                )
            return False
        else:
            return True
    
    def _write_single_edge_list_to_rdf(
        self,
        edge_list: list,
        label: str,
        prop_dict: dict,
    ):
        """
        This function takes one list of biocypher edges and writes them
        to an RDF file with the given format.

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
        
        # check if list has the right structure
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
        
        # translate label to PascalCase
        label_pascal = self.translator.name_sentence_to_pascal(label)

        # create file name
        fileName = os.path.join(self._outdir, f'{label_pascal}.{self.rdf_format}')

        # write data in graph

        # g = Graph()

        for e in edge_list:
            rdf_subject = e.get_source_id()
            rdf_object = e.get_target_id()
            rdf_predicate = e.get_id()

            edge_label = self.translator.name_sentence_to_pascal(e.get_label())
            self.rdf_graph.add((self.label_to_uri(rdf_subject), self.namespaces["biocypher"][edge_label], self.label_to_uri((rdf_object))))
        
        # g.serialize(destination=fileName, format=self.rdf_format)
        
        # write to file
        logger.info(
            f'Writing {len(edge_list)} entries to {label_pascal}.{self.rdf_format}',
        )
                    
        return True
    
    def _write_single_node_list_to_rdf(
        self,
        node_list: list,
        label: str,
        prop_dict: dict,
        labels: str,
    ):
        """
        This function takes one list of biocypher node and writes them
        to an RDF file with the given format.

        Args:
            node_list (list): list of BioCypherNodes to be written

            label (str): the label (type) of the edge

            prop_dict (dict): properties of node class passed from parsing
                function and their types

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

        # translate label to PascalCase
        label_pascal = self.translator.name_sentence_to_pascal(label)

        # create file name
        # fileName = os.path.join(self._outdir, f'{label_pascal}.{self.rdf_format}')

        # write data in graph

        # print(self.translator.ontology.mapping.schema)
        # quit()
        # g = Graph()

        for n in node_list:
            rdf_subject = n.get_id()
            rdf_object = n.get_label()
            properties = n.get_properties()
            class_name = self.translator.name_sentence_to_pascal(rdf_object)
            self.rdf_graph.add((self.namespaces["biocypher"][class_name], RDF.type, RDFS.Class))
            self.rdf_graph.add((self.label_to_uri(rdf_subject), RDFS.Class, self.namespaces["biocypher"][class_name]))
            for key, value in properties.items():
                self.rdf_graph.add((self.label_to_uri(rdf_subject), self.namespaces["biocypher"][key], Literal(value)))
                
        
        # g.serialize(destination=fileName, format=self.rdf_format)
        
        # write to file
        logger.info(
            f'Writing {len(node_list)} entries to {label_pascal}.{self.rdf_format}',
        )

        return True
        
    def _lpg_to_rdf(self, nodes_or_edges, is_node, batch_size):
        """
        Function to convert BioCypher's labeled property graph into RDF
        format using a minimal approach where all properties are dropped.
        Expects list or generator of nodes from the
        :py:class:`BioCypherNode` class,  or edges from the 
        :py:class:`BioCypherEdge` or :py:class:`BioCypherRelAsNode` class.

        Args:
            nodes_or_edges: a list or generator of nodes in
                :py:class:`BioCypherNode`,
                :py:class:`BioCypherEdge` or 
                :py:class:`BioCypherRelAsNode`format
            is_node: boolean, 1=nodes 0=edges

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        self.seen_node_ids = set()
        self.duplicate_node_ids = set()
        self.duplicate_node_types = set()
        self.seen_edges = {}
        self.duplicate_edge_ids = set()
        self.duplicate_edge_types = set()
        self._init_namespaces()

        if is_node:
            #### _write_node_data() function
            if isinstance(nodes_or_edges, GeneratorType) or isinstance(nodes_or_edges, peekable):
                logger.debug('Writing node data to RDF from generator.')

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
                for node in nodes_or_edges:
                    _id = node.get_id()
                    label = node.get_label()

                    # check for non-id
                    if not _id:
                        logger.warning(f'Node {label} has no id; skipping.')
                        continue

                    # check if node has already been written, if so skip
                    if _id in self.seen_node_ids:
                        self.duplicate_node_ids.add(_id)
                        if not label in self.duplicate_node_types:
                            self.duplicate_node_types.add(label)
                            logger.warning(
                                f'Duplicate nodes found in type {label}. '
                            )
                        continue

                    if not label in bins.keys():
                        # start new list
                        all_labels = None
                        bins[label].append(node)
                        bin_l[label] = 1

                        # get properties from config if present
                        cprops = self.translator.ontology.mapping.extended_schema.get(label).get('properties', )
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
                        all_labels = self.translator.ontology.get_ancestors(label)

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
                            passed = self._write_single_node_list_to_rdf(
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
                    passed = self._write_single_node_list_to_rdf(
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
                if type(nodes_or_edges) is not list:
                    logger.error('Nodes must be passed as list or generator.')
                    return False
                else:

                    def gen(nodes):
                        yield from nodes

                    return self._write_node_data(gen(nodes_or_edges), batch_size=batch_size)
                
        else:
            #### _write_edge_data() function
            if isinstance(nodes_or_edges, GeneratorType):
                logger.debug('Writing edge data to RDF from generator.')
                bins = defaultdict(list)  # dict to store a list for each
                # label that is passed in
                bin_l = {}  # dict to store the length of each list for
                # batching cutoff
                reference_props = defaultdict(
                    dict,
                )  # dict to store a dict of properties
                # for each label to check for consistency and their type
                # for now, relevant for `int`
                for e in nodes_or_edges:
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

                    if not label in self.seen_edges.keys():
                        self.seen_edges[label] = set()

                    src_tar_id = '_'.join([e.get_source_id(), e.get_target_id()])

                    # check for duplicates
                    if src_tar_id in self.seen_edges.get(label, set()):
                        self.duplicate_edge_ids.add(src_tar_id)
                        if not label in self.duplicate_edge_types:
                            self.duplicate_edge_types.add(label)
                            logger.warning(
                                f'Duplicate edges found in type {label}. '
                            )
                        continue

                    else:
                        self.seen_edges[label].add(src_tar_id)

                    if not label in bins.keys():
                        # start new list
                        bins[label].append(e)
                        bin_l[label] = 1

                        # get properties from config if present

                        # check whether label is in ontology_adapter.leaves
                        # (may not be if it is an edge that carries the
                        # "label_as_edge" property)
                        cprops = None
                        if label in self.translator.ontology.mapping.extended_schema:
                            cprops = self.translator.ontology.mapping.extended_schema.get(label).get(
                                'properties',
                            )
                        else:
                            # try via "label_as_edge"
                            for k, v in self.translator.ontology.mapping.extended_schema.items():
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
                            passed = self._write_single_edge_list_to_rdf(
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

                    passed = self._write_single_edge_list_to_rdf(
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

            else:
                if type(nodes_or_edges) is not list:
                    logger.error('Edges must be passed as list or generator.')
                    return False
                else:

                    def gen(edges):
                        yield from edges

                    return self._write_edge_data(gen(nodes_or_edges), batch_size=batch_size)
        
        return True
        
    def write_nodes(self, nodes, batch_size: int = int(1e6)):
        """
        Wrapper for writing nodes in rdf format. It calls _lpg_to_rdf()
        functions specifying it's node data.

        Args:
            nodes (BioCypherNode): a list or generator of nodes in
                :py:class:`BioCypherNode` format

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        # check if specified output format is correct
        passed = self._get_rdf_format(self.rdf_format)
        if not passed:
            logger.error('Error while writing node data, wrong RDF format')
            return False
        # write node data using _lpg_to_rdf method
        passed = self._lpg_to_rdf(nodes, is_node=1, batch_size=int(1e6))
        if not passed:
            logger.error('Error while writing node data.')
            return False
        
    def write_edges(
        self,
        edges: Union[list, GeneratorType],
        batch_size: int = int(1e6),
    ) -> bool:
        """
        Wrapper for writing edges in rdf format. It calls _lpg_to_rdf()
        functions specifying it's edge data.

        Args:
            nodes (BioCypherEdge): a list or generator of edges in
                :py:class:`BioCypherEdge` format

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        # check if specified output format is correct
        passed = self._get_rdf_format(self.rdf_format)
        if not passed:
            logger.error('Error while writing edge data, wrong RDF format')
            return False
        # write edge data using _lpg_to_rdf method
        passed = self._lpg_to_rdf(edges, is_node=0, batch_size=int(1e6))
        if not passed:
            logger.error('Error while writing edge data.')
            return False
    
    def _construct_import_call(self) -> bool:
        """
        Function to write the import call, not needed for RDF

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        self.rdf_graph.serialize(destination=os.path.join(self._outdir, f'rdf_output.{self.rdf_format}'), format=self.rdf_format)

        return ""

    def _write_array_string(self, string_list):
        """
        Abstract method to write the string representation of an array into a .csv file
        as required by the neo4j admin-import.

        Args:
            string_list (list): list of ontology strings

        Returns:
            str: The string representation of an array for the neo4j admin import
        """

        return True
    
    def _write_node_headers(self):
        """
        Abstract method that takes care of importing properties of a graph entity that is represented
        as a node as per the definition in the `schema_config.yaml`

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        return True

    def _write_edge_headers(self):
        """
        Abstract method to write a database import-file for a graph entity that is represented
        as an edge as per the definition in the `schema_config.yaml`,
        containing only the header for this type of edge.

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        return True
    
    def _write_node_headers(self):
        """
        Abstract method that takes care of importing properties of a graph entity that is represented
        as a node as per the definition in the `schema_config.yaml`

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        return True
    
    def label_to_uri(self, input):
        """
        Try to convert the input to a proper uri. 
        otherwise default to biocypher prefix
        """
        _pref, _id = input.split(":")

        if _pref in self.namespaces.keys():
            return self.namespaces[_pref][_id]
        else:
            return self.namespaces["biocypher"][input]
        

        # TODO: this should flow out of the config file!
        # hardcoded it for now
    def _init_namespaces(self):
        self.namespaces = {}
        self.namespaces["biocypher"] = Namespace("http://example.org/biocypher#")
        self.namespaces["chembl"] = Namespace("https://www.ebi.ac.uk/chembl/compound_report_card/")
        self.namespaces["go"] = Namespace("http://purl.obolibrary.org/obo/GO_")
        self.namespaces["mondo"] = Namespace("http://purl.obolibrary.org/obo/MONDO_")
        self.namespaces["efo"] = Namespace("http://purl.obolibrary.org/obo/EFO_")
        self.namespaces["hp"] = Namespace("http://purl.obolibrary.org/obo/HP_")

        for key, value in self.namespaces.items():
            self.rdf_graph.bind(key, Namespace(value)) 
    