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
            # RDF graph does not support 'ttl' format, but only "turtle" format. while the preferred extension is always .ttl
            if self.rdf_format == "turtle":
                self.extension = "ttl"
            elif self.rdf_format == "ttl":
                self.rdf_format = "turtle"
                self.extension = "ttl"
            else:
                self.extension = self.rdf_format
            return True
    
    def _write_single_edge_list_to_file(
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
        fileName = os.path.join(self._outdir, f'{label_pascal}.{self.extension}')

        # write data in graph

        g = Graph()
        self._init_namespaces(g)

        for e in edge_list:
            rdf_subject = e.get_source_id()
            rdf_object = e.get_target_id()
            rdf_predicate = e.get_id()

            edge_label = self.translator.name_sentence_to_pascal(e.get_label())
            g.add((self.label_to_uri(rdf_subject), self.namespaces["biocypher"][edge_label], self.label_to_uri((rdf_object))))
        
        g.serialize(destination=fileName, format=self.rdf_format)
        
        # write to file
        logger.info(
            f'Writing {len(edge_list)} entries to {label_pascal}.{self.rdf_format}',
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

        for n in node_list:
            
            # do not check for deviations in properties.
            # This is not applicable for rdf.
            if False:
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
        fileName = os.path.join(self._outdir, f'{label_pascal}.{self.extension}')

        # write data in graph
        g = Graph()
        self._init_namespaces(g)

        for n in node_list:
            rdf_subject = n.get_id()
            rdf_object = n.get_label()
            properties = n.get_properties()
            class_name = self.translator.name_sentence_to_pascal(rdf_object)
            g.add((self.namespaces["biocypher"][class_name], RDF.type, RDFS.Class))
            g.add((self.label_to_uri(rdf_subject), RDFS.Class, self.namespaces["biocypher"][class_name]))
            for key, value in properties.items():
                # only write value if it exists.
                if value:
                    g.add((self.label_to_uri(rdf_subject), self.namespaces["biocypher"][key], Literal(value)))
                
        
        g.serialize(destination=fileName, format=self.rdf_format)
        
        # write to file
        logger.info(
            f'Writing {len(node_list)} entries to {label_pascal}.{self.rdf_format}',
        )

        return True
       
    def write_nodes(self, nodes, batch_size: int = int(1e6)):
        """
        Wrapper for writing nodes in rdf format. It calls _write_node_data()
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
        # write node data using _write_node_data method
        passed = self._write_node_data(nodes, batch_size=batch_size)
        if not passed:
            logger.error('Error while writing node data.')
            return False
        
    def write_edges(
        self,
        edges: Union[list, GeneratorType],
        batch_size: int = int(1e6),
    ) -> bool:
        """
        Wrapper for writing edges in rdf format. It calls _write_edge_data()
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
        # write edge data using _write_edge_data method
        passed = self._write_edge_data(edges, batch_size=batch_size)
        if not passed:
            logger.error('Error while writing edge data.')
            return False
    
    def _construct_import_call(self) -> bool:
        """
        Function to write the import call, not needed for RDF

        Returns:
            bool: The return value. True for success, False otherwise.
        """
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
    
    def _init_namespaces(self, graph):
        self.namespaces = {}
        self.namespaces["biocypher"] = Namespace("http://example.org/biocypher#")
        self.namespaces["chembl"] = Namespace("https://www.ebi.ac.uk/chembl/compound_report_card/")
        self.namespaces["go"] = Namespace("http://purl.obolibrary.org/obo/GO_")
        self.namespaces["mondo"] = Namespace("http://purl.obolibrary.org/obo/MONDO_")
        self.namespaces["efo"] = Namespace("http://purl.obolibrary.org/obo/EFO_")
        self.namespaces["hp"] = Namespace("http://purl.obolibrary.org/obo/HP_")

        for key, value in self.namespaces.items():
            graph.bind(key, Namespace(value)) 
    