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
from ._write import get_writer, _Neo4jBatchWriter
from ._config import config as _config
from ._create import VersionNode, BioCypherEdge, BioCypherNode
from ._mapping import OntologyMapping
from ._ontology import Ontology
from ._translate import Translator

__all__ = ['_Driver']


class _Driver():
    """
    Manages a connection to a biocypher database.

    Args:

        database_name (str): The name of the database to connect to.

        wipe (bool): Whether to wipe the database before importing.

        uri (str): The URI of the database.

        user (str): The username to use for authentication.

        password (str): The password to use for authentication.


    """
    def __init__(
        self,
        database_name: Optional[str] = None,
        wipe: bool = False,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        multi_db: Optional[bool] = None,
        fetch_size: int = 1000,
        increment_version: bool = True,
        ontology: Optional[Ontology] = None,
        translator: Optional[Translator] = None,
    ):

        self._ontology = ontology
        self._translator = translator

        self._driver = neo4j_utils.Driver(
            db_name=database_name,
            db_uri=uri,
            db_user=user,
            db_passwd=password,
            fetch_size=fetch_size,
            wipe=wipe,
            multi_db=multi_db,
        )

        # check for biocypher config in connected graph

        if wipe:

            self.init_db()

        if increment_version:

            # set new current version node
            self._update_meta_graph()

    def _update_meta_graph(self):

        logger.info('Updating Neo4j meta graph.')
        # add version node
        self.add_biocypher_nodes(self._ontology)

        # find current version node
        db_version = self._driver.query(
            'MATCH (v:BioCypher) '
            'WHERE NOT (v)-[:PRECEDES]->() '
            'RETURN v',
        )

        # connect version node to previous
        if db_version[0]:
            e_meta = BioCypherEdge(
                self._ontology.graph_state['id'],
                self._ontology.node_id,
                'PRECEDES',
            )
            self.add_biocypher_edges(e_meta)

    def init_db(self):
        """
        Used to initialise a property graph database by setting up new
        constraints. Wipe has been performed by the ``neo4j_utils.Driver``
        class` already.

        Todo:
            - set up constraint creation interactively depending on the
                need of the database
        """

        logger.info('Initialising database.')
        self._create_constraints()

    def _create_constraints(self):
        """
        Creates constraints on node types in the graph. Used for
        initial setup.

        Grabs leaves of the ``schema_config.yaml`` file and creates
        constraints on the id of all entities represented as nodes.
        """

        logger.info('Creating constraints for node types in config.')

        # get structure
        for leaf in self._ontology.extended_schema.items():
            label = leaf[0]
            if leaf[1]['represented_as'] == 'node':

                s = (
                    f'CREATE CONSTRAINT `{label}_id` '
                    f'IF NOT EXISTS ON (n:`{label}`) '
                    'ASSERT n.id IS UNIQUE'
                )
                self._driver.query(s)

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

        bn = self._translator.translate_nodes(id_type_tuples)
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

        bn = self._translator.translate_edges(id_src_tar_type_tuples)
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

            nodes = _misc.to_list(nodes)

            entities = [node.get_dict() for node in nodes]

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

        result = getattr(self._driver, method)(
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

        self._driver.query(node_query, parameters={'rels': rels})

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

        result = getattr(self._driver,
                         method)(edge_query, parameters={
                             'rels': rels
                         })

        logger.info('Finished merging edges.')

        return result

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


def get_driver(
    dbms: str,
    translator: 'Translator',
    ontology: 'Ontology',
):
    """
    Function to return the writer class.

    Returns:
        class: the writer class
    """

    dbms_config = _config(dbms)

    if dbms == 'neo4j':
        return _Driver(
            database_name=dbms_config['database_name'],
            wipe=dbms_config['wipe'],
            uri=dbms_config['uri'],
            user=dbms_config['user'],
            password=dbms_config['password'],
            multi_db=dbms_config['multi_db'],
            ontology=ontology,
            translator=translator,
        )

    return None
