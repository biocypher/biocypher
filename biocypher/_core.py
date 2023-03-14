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

from ._logger import logger

logger.debug(f'Loading module {__name__}.')

from ._write import get_writer
from ._config import config as _config
from ._config import update_from_file as _file_update
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
    'head_ontology',
]


class BioCypher:
    def __init__(
        self,
        dbms: str = None,
        offline: bool = None,
        strict_mode: bool = None,
        biocypher_config_path: str = None,
        schema_config_path: str = None,
        head_ontology: dict = None,
        tail_ontologies: dict = None,
        output_directory: str = None,
        # legacy params
        db_name: str = None,
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

        """

        # Update configuration if custom path is provided
        if biocypher_config_path:
            _file_update(biocypher_config_path)

        if db_name:
            logger.warning(
                'The parameter `db_name` is deprecated. Please set the '
                '`database_name` setting in the `biocypher_config.yaml` file '
                'instead.'
            )
            _config(**{'neo4j': {'database_name': db_name}})

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

        self._schema_config_path = schema_config_path or self.base_config.get(
            'schema_config_path'
        )

        if not self._schema_config_path:
            raise ValueError(
                'BioCypher requires a schema configuration; please provide a '
                'path to the schema configuration YAML file via '
                '`biocypher_config.yaml` or `BioCypher` class parameter.'
            )

        self._head_ontology = head_ontology or self.base_config['head_ontology']

        # Set configuration - optional
        self._output_directory = output_directory or self.base_config.get(
            'output_directory'
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
                config_file=self._schema_config_path,
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

    # OVERVIEW AND CONVENIENCE METHODS ###

    def log_missing_bl_types(self):
        """
        Get the set of Biolink types encountered without an entry in
        the `schema_config.yaml` and print them to the logger.

        Returns:
            set: a set of missing Biolink types
        """

        mt = self._translator.get_missing_biolink_types()

        if mt:
            msg = (
                'Input entities not accounted for due to them not being '
                'present in the `schema_config.yaml` configuration file '
                '(this is not necessarily a problem, if you did not intend '
                'to include them in the database; see the log for details): \n'
            )
            for k, v in mt.items():
                msg += f'    {k}: {v} \n'

            logger.info(msg)
            return mt

        else:
            logger.info('No missing Biolink types in input.')
            return None

    def log_duplicates(self):
        """
        Get the set of duplicate nodes and edges encountered and print them to
        the logger.
        """

        dn = self._writer.get_duplicate_nodes()

        if dn:

            ntypes = dn[0]
            nids = dn[1]

            msg = ('Duplicate node types encountered (IDs in log): \n')
            for typ in ntypes:
                msg += f'    {typ}\n'

            logger.info(msg)

            idmsg = ('Duplicate node IDs encountered: \n')
            for _id in nids:
                idmsg += f'    {_id}\n'

            logger.debug(idmsg)

        else:
            logger.info('No duplicate nodes in input.')

        de = self._writer.get_duplicate_edges()

        if de:

            etypes = de[0]
            eids = de[1]

            msg = ('Duplicate edge types encountered (IDs in log): \n')
            for typ in etypes:
                msg += f'    {typ}\n'

            logger.info(msg)

            idmsg = ('Duplicate edge IDs encountered: \n')
            for _id in eids:
                idmsg += f'    {_id}\n'

            logger.debug(idmsg)

        else:
            logger.info('No duplicate edges in input.')

    def show_ontology_structure(self, **kwargs):
        """
        Show the ontology structure of the database using the Biolink schema and
        treelib.
        """

        if not self._ontology:
            self._get_ontology()

        return self._ontology.show_ontology_structure(**kwargs)

    def write_import_call(self) -> None:
        """
        Write a shell script to import the database depending on the chosen
        DBMS.
        """

        if not self._offline:
            raise NotImplementedError(
                'Cannot write import call in online mode.'
            )

        self._writer.write_import_call()

    # TRANSLATION METHODS ###

    def translate_term(self, term: str) -> str:
        """
        Translate a term to its BioCypher equivalent.
        """

        # instantiate adapter if not exists
        self.start_ontology()

        return self._translator.translate_term(term)

    def reverse_translate_term(self, term: str) -> str:
        """
        Reverse translate a term from its BioCypher equivalent.
        """

        # instantiate adapter if not exists
        self.start_ontology()

        return self._translator.reverse_translate_term(term)

    def translate_query(self, query: str) -> str:
        """
        Translate a query to its BioCypher equivalent.
        """

        # instantiate adapter if not exists
        self.start_ontology()

        return self._translator.translate(query)

    def reverse_translate_query(self, query: str) -> str:
        """
        Reverse translate a query from its BioCypher equivalent.
        """

        # instantiate adapter if not exists
        self.start_ontology()

        return self._translator.reverse_translate(query)
