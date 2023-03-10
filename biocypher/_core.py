from more_itertools import peekable

from ._write import get_writer
from ._config import config as _config
from ._create import BioCypherEdge, BioCypherNode
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
    """
    Orchestration of BioCypher database operations.
    """
    def __init__(self, ):

        # Load configuration
        self.base_config = _config('biocypher')

        # Check for required configuration
        for key in REQUIRED_CONFIG:
            if key not in self.base_config:
                raise ValueError(f'Configuration key {key} is required.')

        # Set configuration - mandatory
        self.dbms = self.base_config['dbms']
        self.offline = self.base_config['offline']
        self.strict_mode = self.base_config['strict_mode']
        self.user_schema_config_path = self.base_config[
            'user_schema_config_path']
        self.head_ontology = self.base_config['head_ontology']

        # Set configuration - optional
        self.output_directory = self.base_config.get(
            'output_directory'
        ) or 'biocypher-out'
        self.log_directory = self.base_config.get(
            'log_directory'
        ) or 'biocypher-log'
        self.tail_ontologies = self.base_config.get('tail_ontologies')

        if self.dbms not in SUPPORTED_DBMS:
            raise ValueError(
                f'DBMS {self.dbms} not supported. '
                f'Please select from {SUPPORTED_DBMS}.'
            )

        # Initialize
        self.ontology_mapping = None
        self.translator = None
        self.ontology = None
        self.writer = None

    def _get_ontology_mapping(self):

        if not self.ontology_mapping:
            self.ontology_mapping = OntologyMapping(
                config_file=self.user_schema_config_path,
            )

        return self.ontology_mapping

    def _get_translator(self):

        if not self.translator:
            self.translator = Translator(
                ontology_mapping=self._get_ontology_mapping(),
                strict_mode=self.strict_mode,
            )

        return self.translator

    def _get_ontology(self):

        if not self.ontology:
            self.ontology = Ontology(
                ontology_mapping=self._get_ontology_mapping(),
                head_ontology=self.head_ontology,
                tail_ontologies=self.tail_ontologies,
            )

        return self.ontology

    def _get_writer(self):

        # Get worker
        if self.offline:
            self.writer = get_writer(
                dbms=self.dbms,
                translator=self._get_translator(),
                ontology=self._get_ontology(),
                output_directory=self.output_directory,
                strict_mode=self.strict_mode,
            )
        else:
            raise NotImplementedError('Online mode not implemented yet.')

    def write_nodes(self, nodes):
        """
        Write nodes to database.
        """

        if not self.writer:
            self._get_writer()

        nodes = peekable(nodes)
        if not isinstance(nodes.peek(), BioCypherNode):
            tnodes = self.translator.translate_nodes(nodes)
        else:
            tnodes = nodes
        # write node files
        return self.writer.write_nodes(tnodes)

    def write_edges(self, edges):
        """
        Write edges to database.
        """

        edges = peekable(edges)
        if not isinstance(edges.peek(), BioCypherEdge):
            tedges = self.translator.translate_edges(edges)
        else:
            tedges = edges
        # write edge files
        return self.writer.write_edges(tedges)
