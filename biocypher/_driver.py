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
A wrapper around the Neo4j driver which handles the DBMS connection and
provides basic management methods.
"""
from collections.abc import Iterable

from ._logger import logger

logger.debug(f'Loading module {__name__}.')

from typing import TYPE_CHECKING, Optional
import itertools

from more_itertools import peekable

if TYPE_CHECKING:

    import neo4j

import neo4j_utils

from . import _misc
from ._write import BatchWriter
from ._config import config as _config
from ._create import VersionNode, BioCypherEdge, BioCypherNode
from ._mapping import OntologyMapping
from ._ontology import Ontology
from ._translate import Translator

__all__ = ['Driver']


class Driver(neo4j_utils.Driver):
    """
    Manages a connection to a biocypher database.

    The connection can be defined in three ways:
        * Providing a ready ``neo4j.Driver`` instance
        * By URI and authentication data
        * By a YAML config file

    Args:
        driver:
            A ``neo4j.Driver`` instance, created by, for example,
            ``neo4j.GraphDatabase.driver``.
        db_name:
            Name of the database (Neo4j graph) to use.
        db_uri:
            Protocol, host and port to access the Neo4j server.
        db_user:
            Neo4j user name.
        db_passwd:
            Password of the Neo4j user.
        fetch_size:
            Optional; the fetch size to use in database transactions.
        wipe:
            Wipe the database after connection, ensuring the data is
            loaded into an empty database.
        offline:
            Do not connect to the database, but use the provided
            schema to create a graph representation and write CSVs for
            admin import.
        output_directory:
            Directory to write CSV files to.
        increment_version:
            Whether to increase version number automatically and create a
            new BioCypher version node in the graph.
        user_schema_config_path:
            Path to the graph database schema configuration file.
        clear_cache:
            Whether to clear the ontological hierarchy cache at driver
            instantiation. The cache is used to speed up the translation
            of Biolink classes to the database schema.
        delimiter:
            Delimiter for CSV export.
        array_delimiter:
            Array delimiter for CSV exported contents.
        quote_char:
            String quotation character for CSV export.
        import_call_bin_prefix:
            Prefix for the Cypher call to the admin import shell command.
            Defaults to ``bin/``.
        import_call_file_prefix:
            Path prefix for the data files (headers and parts) in the admin
            import call. Defaults to the absolute output directory path.
        skip_bad_relationships:
            Whether to skip relationships with missing source or target
            nodes in the admin import shell command.
        skip_duplicate_nodes:
            Whether to skip duplicate nodes in the admin import shell
            command.
        biolink_model:
            Path to the custom Biolink model YAML file.
        tail_ontology_url:
            URL of the ontology to hybridise to the head ontology.
        head_join_node:
            Biolink class of the node to join the tail ontology to.
        tail_join_node:
            Ontology class of the node to join the head ontology to.
    """
    def __init__(
        self,
        driver: Optional['neo4j.Driver'] = None,
        db_name: Optional[str] = None,
        db_uri: Optional[str] = None,
        db_user: Optional[str] = None,
        db_passwd: Optional[str] = None,
        multi_db: Optional[bool] = None,
        fetch_size: int = 1000,
        skip_bad_relationships: bool = False,
        skip_duplicate_nodes: bool = False,
        wipe: bool = False,
        strict_mode: Optional[bool] = None,
        offline: Optional[bool] = None,
        output_directory: Optional[str] = None,
        increment_version: bool = True,
        clear_cache: Optional[bool] = None,
        user_schema_config_path: Optional[str] = None,
        delimiter: Optional[str] = None,
        array_delimiter: Optional[str] = None,
        quote_char: Optional[str] = None,
        import_call_bin_prefix: Optional[str] = None,
        import_call_file_prefix: Optional[str] = None,
        head_ontology: Optional[dict] = None,
        tail_ontologies: Optional[dict] = None,
    ):

        # Neo4j options
        db_name = db_name or _config('neo4j_db')
        db_uri = db_uri or _config('neo4j_uri')
        db_user = db_user or _config('neo4j_user')
        db_passwd = db_passwd or _config('neo4j_pw')
        multi_db = multi_db or _config('neo4j_multi_db')
        self.db_delim = delimiter or _config('neo4j_delimiter')
        self.db_adelim = array_delimiter or _config('neo4j_array_delimiter')
        self.db_quote = quote_char or _config('neo4j_quote_char')

        if import_call_bin_prefix is None:
            self.import_call_bin_prefix = _config(
                'neo4j_import_call_bin_prefix'
            )
        else:
            self.import_call_bin_prefix = import_call_bin_prefix

        if import_call_file_prefix is None:
            self.import_call_file_prefix = _config(
                'neo4j_import_call_file_prefix'
            )
        else:
            self.import_call_file_prefix = import_call_file_prefix

        self.skip_bad_relationships = skip_bad_relationships
        self.skip_duplicate_nodes = skip_duplicate_nodes
        self.wipe = wipe

        if offline is None:
            self._offline = _config('offline')
        else:
            self._offline = offline

        # BioCypher options
        self.user_schema_config_path = user_schema_config_path or _config(
            'user_schema_config_path'
        )
        self.strict_mode = strict_mode or _config('strict_mode')
        self.output_directory = output_directory or _config('output_directory')
        self.clear_cache = clear_cache or _config('clear_cache')

        self.head_ontology = head_ontology or _config('head_ontology')

        self.tail_ontologies = tail_ontologies or _config('tail_ontologies')

        if self._offline:

            if not self.user_schema_config_path:
                raise ValueError(
                    'Offline mode requires a user schema config file.'
                    ' Please provide one with the `user_schema_config_path`'
                    ' argument or set the `user_schema_config_path`'
                    ' configuration variable.'
                )

            logger.info('Offline mode: no connection to DBMS.')

            self._ontology_mapping = OntologyMapping(
                config_file=self.user_schema_config_path,
            )

            self._db_config = {
                'uri': db_uri,
                'user': db_user,
                'passwd': db_passwd,
                'db': db_name,
                'fetch_size': fetch_size,
            }

            self.driver = None
            self._db_name = db_name

        else:

            neo4j_utils.Driver.__init__(**locals())

            # if db representation node does not exist or explicitly
            # asked for wipe, create new graph representation: default
            # yaml, interactive?
            if wipe:

                # get database version node ('check' module) immutable
                # variable of each instance (ie, each call from the
                # adapter to BioCypher); checks for existence of graph
                # representation and returns if found, else creates new
                # one
                self._ontology_mapping = VersionNode(
                    from_config=offline or wipe,
                    config_file=self.user_schema_config_path,
                    bcy_driver=self,
                )

                # init requires db_meta to be set
                self.init_db()

            else:

                self._ontology_mapping = VersionNode(self)

        if increment_version:

            # set new current version node
            self.update_meta_graph()

        self.ontology = None
        self.batch_writer = None
        self._update_translator()

        # TODO: implement passing a driver instance
        # I am not sure, but seems like it should work from driver

    def update_meta_graph(self):

        if self._offline:
            return

        logger.info('Updating Neo4j meta graph.')
        # add version node
        self.add_biocypher_nodes(self._ontology_mapping)

        # find current version node
        db_version = self.query(
            'MATCH (v:BioCypher) '
            'WHERE NOT (v)-[:PRECEDES]->() '
            'RETURN v',
        )
        # connect version node to previous
        if db_version[0]:
            e_meta = BioCypherEdge(
                self._ontology_mapping.graph_state['id'],
                self._ontology_mapping.node_id,
                'PRECEDES',
            )
            self.add_biocypher_edges(e_meta)

        # add structure nodes
        no_l = []
        # leaves of the hierarchy specified in schema yaml
        for entity, params in self._ontology_mapping.extended_schema.items():
            no_l.append(
                BioCypherNode(
                    node_id=entity,
                    node_label='MetaNode',
                    properties=params,
                ),
            )
        self.add_biocypher_nodes(no_l)

        # remove connection of structure nodes from previous version
        # node(s)
        self.query('MATCH ()-[r:CONTAINS]-()'
                   'DELETE r', )

        # connect structure nodes to version node
        ed_v = []
        current_version = self._ontology_mapping.get_id()
        for entity in self._ontology_mapping.extended_schema.keys():
            ed_v.append(
                BioCypherEdge(
                    source_id=current_version,
                    target_id=entity,
                    relationship_label='CONTAINS',
                ),
            )
        self.add_biocypher_edges(ed_v)

        # add graph structure between MetaNodes
        ed = []
        for no in no_l:
            id = no.get_id()
            src = no.get_properties().get('source')
            tar = no.get_properties().get('target')
            if None not in [id, src, tar]:
                ed.append(BioCypherEdge(id, src, 'IS_SOURCE_OF'))
                ed.append(BioCypherEdge(id, tar, 'IS_TARGET_OF'))
        self.add_biocypher_edges(ed)

    def _update_translator(self):

        self.translator = Translator(
            extended_schema=self._ontology_mapping.extended_schema,
            strict_mode=self.strict_mode,
        )

    def init_db(self):
        """
        Used to initialise a property graph database by deleting
        contents and constraints and setting up new constraints.

        Todo:
            - set up constraint creation interactively depending on the
                need of the database
        """

        self.wipe_db()
        self._create_constraints()
        logger.info('Initialising database.')

    def _create_constraints(self):
        """
        Creates constraints on node types in the graph. Used for
        initial setup.

        Grabs leaves of the ``schema_config.yaml`` file and creates
        constraints on the id of all entities represented as nodes.
        """

        logger.info('Creating constraints for node types in config.')

        # get structure
        for leaf in self._ontology_mapping.extended_schema.items():
            label = leaf[0]
            if leaf[1]['represented_as'] == 'node':

                s = (
                    f'CREATE CONSTRAINT `{label}_id` '
                    f'IF NOT EXISTS ON (n:`{label}`) '
                    'ASSERT n.id IS UNIQUE'
                )
                self.query(s)

    def add_nodes(self, id_type_tuples: Iterable[tuple]) -> tuple:
        """
        Generic node adder method to add any kind of input to the graph via the
        :class:`biocypher.create.BioCypherNode` class. Employs translation
        functionality and calls the :meth:`add_biocypher_nodes()` method.

        Args:
            id_type_tuples (iterable of 3-tuple): for each node to add to
                the biocypher graph, a 3-tuple with the following layout:
                first, the (unique if constrained) ID of the node; second, the
                type of the node, capitalised or PascalCase and in noun form
                (Neo4j primary label, eg `:Protein`); and third, a dictionary
                of arbitrary properties the node should possess (can be empty).

        Returns:
            2-tuple: the query result of :meth:`add_biocypher_nodes()`
                - first entry: data
                - second entry: Neo4j summary.
        """

        bn = self.translator.translate_nodes(id_type_tuples)
        return self.add_biocypher_nodes(bn)

    def add_edges(self, id_src_tar_type_tuples: Iterable[tuple]) -> tuple:
        """
        Generic edge adder method to add any kind of input to the graph
        via the :class:`biocypher.create.BioCypherEdge` class. Employs
        translation functionality and calls the
        :meth:`add_biocypher_edges()` method.

        Args:

            id_src_tar_type_tuples (iterable of 5-tuple):

                for each edge to add to the biocypher graph, a 5-tuple
                with the following layout: first, the optional unique ID
                of the interaction. This can be `None` if there is no
                systematic identifier (which for many interactions is
                the case). Second and third, the (unique if constrained)
                IDs of the source and target nodes of the relationship;
                fourth, the type of the relationship; and fifth, a
                dictionary of arbitrary properties the edge should
                possess (can be empty).

        Returns:

            2-tuple: the query result of :meth:`add_biocypher_edges()`

                - first entry: data
                - second entry: Neo4j summary.
        """

        bn = self.translator.translate_edges(id_src_tar_type_tuples)
        return self.add_biocypher_edges(bn)

    def add_biocypher_nodes(
        self,
        nodes: Iterable[BioCypherNode],
        explain: bool = False,
        profile: bool = False,
    ) -> bool:
        """
        Accepts a node type handoff class
        (:class:`biocypher.create.BioCypherNode`) with id,
        label, and a dict of properties (passing on the type of
        property, ie, ``int``, ``str``, ...).

        The dict retrieved by the
        :meth:`biocypher.create.BioCypherNode.get_dict()` method is
        passed into Neo4j as a map of maps, explicitly encoding node id
        and label, and adding all other properties from the 'properties'
        key of the dict. The merge is performed via APOC, matching only
        on node id to prevent duplicates. The same properties are set on
        match and on create, irrespective of the actual event.

        Args:
            nodes:
                An iterable of :class:`biocypher.create.BioCypherNode` objects.
            explain:
                Call ``EXPLAIN`` on the CYPHER query.
            profile:
                Do profiling on the CYPHER query.

        Returns:
            True for success, False otherwise.
        """

        try:

            entities = [
                node.get_dict() for node in _misc.ensure_iterable(nodes)
            ]

        except AttributeError:

            msg = 'Nodes must have a `get_dict` method.'
            logger.error(msg)

            raise ValueError(msg)

        logger.info(f'Merging {len(entities)} nodes.')

        entity_query = (
            'UNWIND $entities AS ent '
            'CALL apoc.merge.node([ent.node_label], '
            '{id: ent.node_id}, ent.properties, ent.properties) '
            'YIELD node '
            'RETURN node'
        )

        method = 'explain' if explain else 'profile' if profile else 'query'

        result = getattr(self, method)(
            entity_query,
            parameters={
                'entities': entities,
            },
        )

        logger.info('Finished merging nodes.')

        return result

    def add_biocypher_edges(
        self,
        edges: Iterable[BioCypherEdge],
        explain: bool = False,
        profile: bool = False,
    ) -> bool:
        """
        Accepts an edge type handoff class
        (:class:`biocypher.create.BioCypherEdge`) with source
        and target ids, label, and a dict of properties (passing on the
        type of property, ie, int, string ...).

        The individual edge is either passed as a singleton, in the case
        of representation as an edge in the graph, or as a 4-tuple, in
        the case of representation as a node (with two edges connecting
        to interaction partners).

        The dict retrieved by the
        :meth:`biocypher.create.BioCypherEdge.get_dict()` method is
        passed into Neo4j as a map of maps, explicitly encoding source
        and target ids and the relationship label, and adding all edge
        properties from the 'properties' key of the dict. The merge is
        performed via APOC, matching only on source and target id to
        prevent duplicates. The same properties are set on match and on
        create, irrespective of the actual event.

        Args:
            edges:
                An iterable of :class:`biocypher.create.BioCypherEdge` objects.
            explain:
                Call ``EXPLAIN`` on the CYPHER query.
            profile:
                Do profiling on the CYPHER query.

        Returns:
            `True` for success, `False` otherwise.
        """

        edges = _misc.ensure_iterable(edges)
        edges = itertools.chain(*(_misc.ensure_iterable(i) for i in edges))

        nodes = []
        rels = []

        try:

            for e in edges:

                if hasattr(e, 'get_node'):

                    nodes.append(e.get_node())
                    rels.append(e.get_source_edge().get_dict())
                    rels.append(e.get_target_edge().get_dict())

                else:

                    rels.append(e.get_dict())

        except AttributeError:

            msg = 'Edges and nodes must have a `get_dict` method.'
            logger.error(msg)

            raise ValueError(msg)

        self.add_biocypher_nodes(nodes)
        logger.info(f'Merging {len(rels)} edges.')

        # cypher query

        # merging only on the ids of the entities, passing the
        # properties on match and on create;
        # TODO add node labels?
        node_query = (
            'UNWIND $rels AS r '
            'MERGE (src {id: r.source_id}) '
            'MERGE (tar {id: r.target_id}) '
        )

        self.query(node_query, parameters={'rels': rels})

        edge_query = (
            'UNWIND $rels AS r '
            'MATCH (src {id: r.source_id}) '
            'MATCH (tar {id: r.target_id}) '
            'WITH src, tar, r '
            'CALL apoc.merge.relationship'
            '(src, r.relationship_label, NULL, '
            'r.properties, tar, r.properties) '
            'YIELD rel '
            'RETURN rel'
        )

        method = 'explain' if explain else 'profile' if profile else 'query'

        result = getattr(self, method)(edge_query, parameters={'rels': rels})

        logger.info('Finished merging edges.')

        return result

    def write_nodes(self, nodes):
        """
        Write BioCypher nodes to disk using the :mod:`write` module,
        formatting the CSV to enable Neo4j admin import from the target
        directory.

        Args:
            nodes (iterable): collection of nodes to be written in
                BioCypher-compatible CSV format; can be any compatible
                (ie, translatable) input format or already as
                :class:`biocypher.create.BioCypherNode`.
        """

        # instantiate ontology on demand because it takes time to load
        self.start_ontology()

        self.start_batch_writer()

        nodes = peekable(nodes)
        if not isinstance(nodes.peek(), BioCypherNode):
            tnodes = self.translator.translate_nodes(nodes)
        else:
            tnodes = nodes
        # write node files
        return self.batch_writer.write_nodes(tnodes)

    def start_batch_writer(self) -> None:
        """
        Instantiate the batch writer if it does not exist.

        Args:
            dirname (str): the directory to write the files to
            db_name (str): the name of the database to write the files to
        """
        if not self.batch_writer:
            self.batch_writer = BatchWriter(
                ontology=self.ontology,
                translator=self.translator,
                delimiter=self.db_delim,
                array_delimiter=self.db_adelim,
                quote=self.db_quote,
                dirname=self.output_directory,
                db_name=self._db_name,
                skip_bad_relationships=self.skip_bad_relationships,
                skip_duplicate_nodes=self.skip_duplicate_nodes,
                import_call_bin_prefix=self.import_call_bin_prefix,
                import_call_file_prefix=self.import_call_file_prefix,
                wipe=self.wipe,
                strict_mode=self.strict_mode,
            )

    def start_ontology(self) -> None:
        """
        Instantiate the :class:`biocypher._ontology.Ontology` if not
        existing.
        """
        if not self.ontology:
            self.ontology = Ontology(
                head_ontology=self.head_ontology,
                mapping=self._ontology_mapping,
                tail_ontologies=self.tail_ontologies,
            )

    def write_edges(
        self,
        edges,
    ) -> None:
        """
        Write BioCypher edges to disk using the :mod:`write` module,
        formatting the CSV to enable Neo4j admin import from the target
        directory.

        Args:
            edges (iterable): collection of edges to be written in
                BioCypher-compatible CSV format; can be any compatible
                (ie, translatable) input format or already as
                :class:`biocypher.create.BioCypherEdge`.
        """

        # instantiate adapter on demand because it takes time to load
        # the biolink model toolkit
        self.start_ontology()

        self.start_batch_writer()

        edges = peekable(edges)
        if not isinstance(edges.peek(), BioCypherEdge):
            tedges = self.translator.translate_edges(edges)
        else:
            tedges = edges
        # write edge files
        self.batch_writer.write_edges(tedges)

    def get_import_call(self):
        """
        Upon using the batch writer for writing admin import CSV files,
        return a string containing the neo4j admin import call with
        delimiters, database name, and paths of node and edge files.

        Returns:
            str: a neo4j-admin import call
        """
        return self.batch_writer.get_import_call()

    def write_import_call(self):
        """
        Upon using the batch writer for writing admin import CSV files,
        write a string containing the neo4j admin import call with
        delimiters, database name, and paths of node and edge files, to
        the export directory.

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        return self.batch_writer.write_import_call()

    def log_missing_bl_types(self):
        """
        Get the set of Biolink types encountered without an entry in
        the `schema_config.yaml` and print them to the logger.

        Returns:
            set: a set of missing Biolink types
        """

        mt = self.translator.get_missing_biolink_types()

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

        dn = self.batch_writer.get_duplicate_nodes()

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

        de = self.batch_writer.get_duplicate_edges()

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

    def show_ontology_structure(self) -> None:
        """
        Show the ontology structure of the database using the Biolink schema and
        treelib.
        """

        self.start_ontology()

        self.ontology.show_ontology_structure()

    # TRANSLATION METHODS ###

    def translate_term(self, term: str) -> str:
        """
        Translate a term to its BioCypher equivalent.
        """

        # instantiate adapter if not exists
        self.start_ontology()

        return self.translator.translate_term(term)

    def reverse_translate_term(self, term: str) -> str:
        """
        Reverse translate a term from its BioCypher equivalent.
        """

        # instantiate adapter if not exists
        self.start_ontology()

        return self.translator.reverse_translate_term(term)

    def translate_query(self, query: str) -> str:
        """
        Translate a query to its BioCypher equivalent.
        """

        # instantiate adapter if not exists
        self.start_ontology()

        return self.translator.translate(query)

    def reverse_translate_query(self, query: str) -> str:
        """
        Reverse translate a query from its BioCypher equivalent.
        """

        # instantiate adapter if not exists
        self.start_ontology()

        return self.translator.reverse_translate(query)

    def __repr__(self):

        return f'<BioCypher {neo4j_utils.Driver.__repr__(self)[1:]}'
