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
from typing import Dict, List, Optional
from more_itertools import peekable
import pandas as pd

from ._logger import logger

logger.debug(f'Loading module {__name__}.')

from ._write import get_writer
from ._pandas import Pandas
from ._config import config as _config
from ._config import update_from_file as _file_update
from ._create import BioCypherEdge, BioCypherNode
from ._connect import get_driver
from ._mapping import OntologyMapping
from ._ontology import Ontology
from ._translate import Translator
from ._deduplicate import Deduplicator

__all__ = ['BioCypher']

SUPPORTED_DBMS = ['neo4j', 'postgresql']

REQUIRED_CONFIG = [
    'dbms',
    'offline',
    'strict_mode',
    'head_ontology',
]


class BioCypher:
    """
    Orchestration of BioCypher operations. Instantiate this class to interact
    with BioCypher.

    Args:

        dbms (str): The database management system to use. For supported
            systems see SUPPORTED_DBMS.

        offline (bool): Whether to run in offline mode. If True, no
            connection to the database will be made.

        strict_mode (bool): Whether to run in strict mode. If True, the
            translator will raise an error if a node or edge does not
            provide source, version, and licence information.

        biocypher_config_path (str): Path to the BioCypher config file.

        schema_config_path (str): Path to the user schema config
            file.

        head_ontology (dict): The head ontology defined by URL ('url') and root
            node ('root_node').

        tail_ontologies (dict): The tail ontologies defined by URL and
            join nodes for both head and tail ontology.

        output_directory (str): Path to the output directory. If not
            provided, the default value 'biocypher-out' will be used.

    """
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

        # Update configuration if custom path is provided
        if biocypher_config_path:
            _file_update(biocypher_config_path)

        if db_name:
            logger.warning(
                'The parameter `db_name` is deprecated. Please set the '
                '`database_name` setting in the `biocypher_config.yaml` file '
                'instead.'
            )
            _config(**{db_name: {'database_name': db_name}})

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
        self._deduplicator = None
        self._translator = None
        self._ontology = None
        self._writer = None
        self._pd = None
    
    def _get_deduplicator(self) -> Deduplicator:
        """
        Create deduplicator if not exists and return.
        """

        if not self._deduplicator:
            self._deduplicator = Deduplicator()

        return self._deduplicator

    def _get_ontology_mapping(self) -> OntologyMapping:
        """
        Create ontology mapping if not exists and return.
        """

        if not self._ontology_mapping:
            self._ontology_mapping = OntologyMapping(
                config_file=self._schema_config_path,
            )

        return self._ontology_mapping

    def _get_translator(self) -> Translator:
        """
        Create translator if not exists and return.
        """

        if not self._translator:
            self._translator = Translator(
                ontology_mapping=self._get_ontology_mapping(),
                strict_mode=self._strict_mode,
            )

        return self._translator

    def _get_ontology(self) -> Ontology:
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
        Create writer if not online. Set as instance variable `self._writer`.
        """

        # Get worker
        if self._offline:
            self._writer = get_writer(
                dbms=self._dbms,
                translator=self._get_translator(),
                ontology=self._get_ontology(),
                deduplicator=self._get_deduplicator(),
                output_directory=self._output_directory,
                strict_mode=self._strict_mode,
            )
        else:
            raise NotImplementedError('Cannot get writer in online mode.')

    def _get_driver(self):
        """
        Create driver if not exists. Set as instance variable `self._driver`.
        """

        if not self._offline:
            self._driver = get_driver(
                dbms=self._dbms,
                translator=self._get_translator(),
                ontology=self._get_ontology(),
                deduplicator=self._get_deduplicator(),
            )
        else:
            raise NotImplementedError('Cannot get driver in offline mode.')

    def write_nodes(self, nodes, batch_size: int = int(1e6)) -> bool:
        """
        Write nodes to database. Either takes an iterable of tuples (if given,
        translates to ``BioCypherNode`` objects) or an iterable of 
        ``BioCypherNode`` objects.

        Args:
            nodes (iterable): An iterable of nodes to write to the database.

        Returns:
            bool: True if successful.
        """

        if not self._writer:
            self._get_writer()

        nodes = peekable(nodes)
        if not isinstance(nodes.peek(), BioCypherNode):
            tnodes = self._translator.translate_nodes(nodes)
        else:
            tnodes = nodes
        # write node files
        return self._writer.write_nodes(tnodes, batch_size=batch_size)

    def write_edges(self, edges, batch_size: int = int(1e6)) -> bool:
        """
        Write edges to database. Either takes an iterable of tuples (if given,
        translates to ``BioCypherEdge`` objects) or an iterable of
        ``BioCypherEdge`` objects.

        Args:
            edges (iterable): An iterable of edges to write to the database.

        Returns:
            bool: True if successful.
        """

        if not self._writer:
            self._get_writer()

        edges = peekable(edges)
        if not isinstance(edges.peek(), BioCypherEdge):
            tedges = self._translator.translate_edges(edges)
        else:
            tedges = edges
        # write edge files
        return self._writer.write_edges(tedges, batch_size=batch_size)

    def to_df(self) -> List[pd.DataFrame]:
        """
        Convert entities to a pandas DataFrame for each entity type and return
        a list.

        Args:
            entities (iterable): An iterable of entities to convert to a
                DataFrame.

        Returns:
            pd.DataFrame: A pandas DataFrame.
        """
        if not self._pd:
            raise ValueError(
                "No pandas instance found. Please call `add()` first."
            )
        
        return self._pd.dfs
        

    def add(self, entities):
        """
        Function to add entities to the in-memory database. Accepts an iterable
        of tuples (if given, translates to ``BioCypherNode`` or
        ``BioCypherEdge`` objects) or an iterable of ``BioCypherNode`` or
        ``BioCypherEdge`` objects.
        """
        if not self._pd:
            self._pd = Pandas(
                translator=self._get_translator(),
                ontology=self._get_ontology(),
                deduplicator=self._get_deduplicator(),
            )

        entities = peekable(entities)

        if isinstance(entities.peek(), BioCypherNode) or isinstance(entities.peek(), BioCypherEdge):
            tentities = entities
        elif len(entities.peek()) < 4:
            tentities = self._translator.translate_nodes(entities)
        else:
            tentities = self._translator.translate_edges(entities)

        self._pd.add_tables(tentities)

    def add_nodes(self, nodes):
        self.add(nodes)

    def add_edges(self, edges):
        self.add(edges)

    def merge_nodes(self, nodes) -> bool:
        """
        Merge nodes into database. Either takes an iterable of tuples (if given,
        translates to ``BioCypherNode`` objects) or an iterable of
        ``BioCypherNode`` objects.

        Args:
            nodes (iterable): An iterable of nodes to merge into the database.

        Returns:
            bool: True if successful.
        """

        if not self._driver:
            self._get_driver()

        nodes = peekable(nodes)
        if not isinstance(nodes.peek(), BioCypherNode):
            tnodes = self._translator.translate_nodes(nodes)
        else:
            tnodes = nodes
        # write node files
        return self._driver.add_biocypher_nodes(tnodes)

    def merge_edges(self, edges) -> bool:
        """
        Merge edges into database. Either takes an iterable of tuples (if given,
        translates to ``BioCypherEdge`` objects) or an iterable of
        ``BioCypherEdge`` objects.
        
        Args:
            edges (iterable): An iterable of edges to merge into the database. 

        Returns:    
            bool: True if successful.
        """

        if not self._driver:
            self._get_driver()

        edges = peekable(edges)
        if not isinstance(edges.peek(), BioCypherEdge):
            tedges = self._translator.translate_edges(edges)
        else:
            tedges = edges
        # write edge files
        return self._driver.add_biocypher_edges(tedges)

    # OVERVIEW AND CONVENIENCE METHODS ###

    def log_missing_input_labels(self) -> Optional[Dict[str, List[str]]]:
        """

        Get the set of input labels encountered without an entry in the
        `schema_config.yaml` and print them to the logger.

        Returns:

            Optional[Dict[str, List[str]]]: A dictionary of Biolink types
            encountered without an entry in the `schema_config.yaml` file.

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
            logger.info('No missing labels in input.')
            return None

    def log_duplicates(self) -> None:
        """
        Get the set of duplicate nodes and edges encountered and print them to
        the logger.
        """

        dn = self._deduplicator.get_duplicate_nodes()

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

        de = self._deduplicator.get_duplicate_edges()

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

    def show_ontology_structure(self, **kwargs) -> None:
        """
        Show the ontology structure using treelib or write to GRAPHML file.

        Args:

            to_disk (str): If specified, the ontology structure will be saved
                to disk as a GRAPHML file, to be opened in your favourite
                graph visualisation tool.

            full (bool): If True, the full ontology structure will be shown,
                including all nodes and edges. If False, only the nodes and
                edges that are relevant to the extended schema will be shown.
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

        Args:
            term (str): The term to translate.

        Returns:
            str: The BioCypher equivalent of the term.
        """

        # instantiate adapter if not exists
        self.start_ontology()

        return self._translator.translate_term(term)
    
    def summary(self) -> None:
        """
        Wrapper for showing ontology structure and logging duplicates and
        missing input types.
        """

        self.show_ontology_structure()
        self.log_duplicates()
        self.log_missing_input_labels()

    def reverse_translate_term(self, term: str) -> str:
        """
        Reverse translate a term from its BioCypher equivalent.

        Args:
            term (str): The BioCypher term to reverse translate.

        Returns:
            str: The original term.
        """

        # instantiate adapter if not exists
        self.start_ontology()

        return self._translator.reverse_translate_term(term)

    def translate_query(self, query: str) -> str:
        """
        Translate a query to its BioCypher equivalent.

        Args:
            query (str): The query to translate.

        Returns:
            str: The BioCypher equivalent of the query.
        """

        # instantiate adapter if not exists
        self.start_ontology()

        return self._translator.translate(query)

    def reverse_translate_query(self, query: str) -> str:
        """
        Reverse translate a query from its BioCypher equivalent.

        Args:
            query (str): The BioCypher query to reverse translate.

        Returns:
            str: The original query.
        """

        # instantiate adapter if not exists
        self.start_ontology()

        return self._translator.reverse_translate(query)
