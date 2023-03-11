#!/usr/bin/env python

#
# Copyright 2021, Heidelberg University Clinic
#
# File author(s): Sebastian Lobentanzer
#                 ...
#
# Distributed under MIT licence, see the file `LICENSE`.
#
"""
BioCypher core module. Interfaces with the user and distributes tasks to
submodules.
"""
from more_itertools import peekable

from ._write import get_writer
from ._config import config as _config
from ._create import BioCypherEdge, BioCypherNode
from ._connect import get_driver
from ._mapping import OntologyMapping
from ._ontology import Ontology
from ._translate import Translator

__all__ = ['BioCypher']

SUPPORTED_DBMS = ['neo4j']

REQUIRED_CONFIG = [
    'dbms',
    'offline',
    'strict_mode',
    'user_schema_config_path',
    'head_ontology',
]


class BioCypher:
    def __init__(
        self,
        dbms: str = None,
        offline: bool = None,
        strict_mode: bool = None,
        user_schema_config_path: str = None,
        head_ontology: dict = None,
        tail_ontologies: dict = None,
        output_directory: str = 'biocypher-out',
        log_directory: str = 'biocypher-log',
    ):
        """
        Orchestration of BioCypher operations.

        Args:

            dbms (str): The database management system to use. For supported
                systems see SUPPORTED_DBMS.

            offline (bool): Whether to run in offline mode. If True, no
                connection to the database will be made.

            strict_mode (bool): Whether to run in strict mode. If True, the
                translator will raise an error if a node or edge does not
                provide source, version, and licence information.

            user_schema_config_path (str): Path to the user schema config
                file.

            head_ontology (dict): The head ontology defined by URL and root
                node.

            tail_ontologies (dict): The tail ontologies defined by URL and
                join nodes for both head and tail ontology.

            output_directory (str): Path to the output directory. If not
                provided, the default value 'biocypher-out' will be used.

            log_directory (str): Path to the log directory. If not provided,
                the default value 'biocypher-log' will be used.

        """

        # Load configuration
        self.base_config = _config('biocypher')

        # Check for required configuration
        for key in REQUIRED_CONFIG:
            if key not in self.base_config:
                raise ValueError(f'Configuration key {key} is required.')

        # Set configuration - mandatory
        self._dbms = dbms or self.base_config['dbms']

        if offline is None:
            self._offline = self.base_config['offline']
        else:
            self._offline = offline

        if strict_mode is None:
            self._strict_mode = self.base_config['strict_mode']
        else:
            self._strict_mode = strict_mode

        self._user_schema_config_path = user_schema_config_path or self.base_config[
            'user_schema_config_path']

        self._head_ontology = head_ontology or self.base_config['head_ontology']

        # Set configuration - optional
        self._output_directory = output_directory or self.base_config.get(
            'output_directory'
        )
        self._log_directory = log_directory or self.base_config.get(
            'log_directory'
        )
        self._tail_ontologies = tail_ontologies or self.base_config.get(
            'tail_ontologies'
        )

        if self._dbms not in SUPPORTED_DBMS:
            raise ValueError(
                f'DBMS {self._dbms} not supported. '
                f'Please select from {SUPPORTED_DBMS}.'
            )

        # Initialize
        self._ontology_mapping = None
        self._translator = None
        self._ontology = None
        self._writer = None

    def _get_ontology_mapping(self):
        """
        Create ontology mapping if not exists and return.
        """

        if not self._ontology_mapping:
            self._ontology_mapping = OntologyMapping(
                config_file=self._user_schema_config_path,
            )

        return self._ontology_mapping

    def _get_translator(self):
        """
        Create translator if not exists and return.
        """

        if not self._translator:
            self._translator = Translator(
                ontology_mapping=self._get_ontology_mapping(),
                strict_mode=self._strict_mode,
            )

        return self._translator

    def _get_ontology(self):
        """
        Create ontology if not exists and return.
        """

        if not self._ontology:
            self._ontology = Ontology(
                ontology_mapping=self._get_ontology_mapping(),
                head_ontology=self._head_ontology,
                tail_ontologies=self._tail_ontologies,
            )

        return self._ontology

    def _get_writer(self):
        """
        Create writer if not online.
        """

        # Get worker
        if self._offline:
            self._writer = get_writer(
                dbms=self._dbms,
                translator=self._get_translator(),
                ontology=self._get_ontology(),
                output_directory=self._output_directory,
                strict_mode=self._strict_mode,
            )
        else:
            raise NotImplementedError('Cannot get writer in online mode.')

    def _get_driver(self):
        """
        Create driver if not exists and return.
        """

        if not self._offline:
            self._driver = get_driver(
                dbms=self._dbms,
                translator=self._get_translator(),
                ontology=self._get_ontology(),
            )
        else:
            raise NotImplementedError('Cannot get driver in offline mode.')

    def write_nodes(self, nodes):
        """
        Write nodes to database.
        """

        if not self._writer:
            self._get_writer()

        nodes = peekable(nodes)
        if not isinstance(nodes.peek(), BioCypherNode):
            tnodes = self._translator.translate_nodes(nodes)
        else:
            tnodes = nodes
        # write node files
        return self._writer.write_nodes(tnodes)

    def write_edges(self, edges):
        """
        Write edges to database.
        """

        if not self._writer:
            self._get_writer()

        edges = peekable(edges)
        if not isinstance(edges.peek(), BioCypherEdge):
            tedges = self._translator.translate_edges(edges)
        else:
            tedges = edges
        # write edge files
        return self._writer.write_edges(tedges)

    def add_nodes(self, nodes):
        pass

    def add_edges(self, edges):
        pass

    def merge_nodes(self, nodes):
        """
        Merge nodes into database.
        """

        if not self._driver:
            self._get_driver()

        nodes = peekable(nodes)
        if not isinstance(nodes.peek(), BioCypherNode):
            tnodes = self._translator.translate_nodes(nodes)
        else:
            tnodes = nodes
        # write node files
        return self._driver.merge_nodes(tnodes)

    def merge_edges(self, edges):
        pass
