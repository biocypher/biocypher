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
Create a property graph database for biomedical research applications.

Transforms ordered collections of biomedical entities and relationships
to BioCypher objects that represent property graph nodes and edges.

Todo:
    - Calls to the classes are independent, so there is no way to
      check directly; nodes can be created at any point in time
      previous to edge creation. We could require a pass of all
      the nodes in the graph when creating edges. Pro: this would
      also allow a check whether the existing graph adheres to
      BioCypher, at least in the node domain. If it doesn't,
      the call does not make much sense.
    - establish a dictionary lookup with the id types to be used / basic
      type checking of the input
    - translation of id types using pypath translation facilities (to be
      later externalised)
"""

from typing import Literal, TYPE_CHECKING
from datetime import datetime
from dataclasses import field, dataclass
import re

import yaml

from . import _misc
from ._misc import is_str
from . import _config as config
from ._logger import logger

if TYPE_CHECKING:

    from biocypher._driver import Driver

__all__ = [
    'BC_TYPES',
    'BioCypherEdge',
    'BioCypherNode',
    'BioCypherRelAsNode',
    'VersionNode',
]

logger.debug(f'Loading module {__name__}.')


_RELFCR = re.compile('[\n\r]+')


class BioCypherEntity:

    def _type_in_properties(self):

        if ':TYPE' in self.properties:

            logger.warning(
                'Keyword `:TYPE` is reserved for Neo4j. '
                'Removing from properties.',
            )
            del self.properties[':TYPE']

    def _process_str_props(self):

        self.properties = {
            k:
            _RELFCR.sub(' ', ', '.join(_misc.to_list(v))).replace('"', "'")
            if is_str(v) or isinstance(v, list) and all(map(is_str, v)) else v
            for k, v in self.properties.items()
        }


@dataclass
class BioCypherNode(BioCypherEntity):
    """
    Handoff class to represent biomedical entities as Neo4j nodes.

    Has id, label, property dict; id and label (in the Neo4j sense of a
    label, ie, the entity descriptor after the colon, such as
    ":Protein") are non-optional and called node_id and node_label to
    avoid confusion with "label" properties. Node labels are written in
    PascalCase and as nouns, as per Neo4j consensus.

    Args:
        node_id (string): consensus "best" id for biological entity
        node_label (string): primary type of entity, capitalised
        **properties (kwargs): collection of all other properties to be
            passed to neo4j for the respective node (dict)

    Todo:
        - check and correct small inconsistencies such as capitalisation
            of ID names ("uniprot" vs "UniProt")
        - check for correct ID patterns (eg "ENSG" + string of numbers,
            uniprot length)
        - ID conversion using pypath translation facilities for now
    """

    node_id: str
    node_label: str
    preferred_id: str = 'id'
    properties: dict = field(default_factory=dict)

    def __post_init__(self):
        """
        Add id field to properties.

        Check for reserved keywords.

        Replace unwanted characters in properties.
        """
        self.entity = 'node'
        self.properties['id'] = self.node_id
        self.properties['preferred_id'] = self.preferred_id or None
        # TODO actually make None possible here; as is, "id" is the default in
        # the dataclass as well as in the configuration file

        self._type_in_properties()
        self._process_str_props()

    def get_id(self) -> str:
        """
        Returns primary node identifier.

        Returns:
            The node identifier.
        """
        return self.node_id

    def get_label(self) -> str:
        """
        Primary node label.

        Returns:
            The label of the node.
        """
        return self.node_label

    def get_preferred_id(self) -> str:
        """
        The preferred identifier.

        Returns:
            The preferred ID of the node.
        """
        return self.preferred_id

    def get_properties(self) -> dict:
        """
        Properties of the node.

        Returns:
            Node properties apart from primary id and label as key-value pairs.
        """
        return self.properties

    def get_dict(self) -> dict:
        """
        Return dict of id, labels, and properties.

        Returns:
            dict: node_id and node_label as top-level key-value pairs,
            properties as second-level dict.
        """
        return {
            'node_id': self.node_id,
            'node_label': self.node_label,
            'properties': self.properties,
        }

    @property
    def nodes(self) -> tuple['BioCypherNode']:
        """
        Create a tuple of node(s).

        Returns:
            This node in a single element tuple.
        """

        return (self,)

    @property
    def key(self) -> tuple[str, str]:
        """
        A key that identifies the group of graph components
        this item belongs to.
        """

        return (self.node_label, self.entity)


@dataclass
class BioCypherEdge(BioCypherEntity):
    """
    Handoff class to represent biomedical relationships in Neo4j.

    Has source and target ids, label, property dict; ids and label (in
    the Neo4j sense of a label, ie, the entity descriptor after the
    colon, such as ":TARGETS") are non-optional and called source_id,
    target_id, and relationship_label to avoid confusion with properties
    called "label", which usually denotes the human-readable form.
    Relationship labels are written in UPPERCASE and as verbs, as per
    Neo4j consensus.

    Args:
        source_id:
            Consensus "best" id for biological entity.
        target_id:
            Consensus "best" id for biological entity.
        relationship_label:
            Type of interaction, UPPERCASE.
        properties:
            Collection of all other properties of the respective edge.
    """

    source_id: str
    target_id: str
    relationship_label: str
    id: str = None
    properties: dict = field(default_factory=dict)

    def __post_init__(self):
        """
        Check for reserved keywords.
        """

        self.entity = 'edge'
        self._type_in_properties()

    def get_id(self) -> str | None:
        """
        Returns primary node identifier or None.

        Returns:
            str: node_id
        """

        return self.id

    def get_source_id(self) -> str:
        """
        Primary node identifier of the relationship source.

        Returns:
            A node identifier.
        """
        return self.source_id

    def get_target_id(self) -> str:
        """
        Primary node identifier of the relationship target.

        Returns:
            A node identifier.
        """
        return self.target_id

    def get_label(self) -> str:
        """
        Label of the relationship.

        Returns:
            str: relationship_label
        """
        return self.relationship_label

    def get_properties(self) -> dict:
        """
        Properties of the relationship.

        Returns:
            All relationship properties apart from primary ids and label
            as key-value pairs.
        """
        return self.properties

    def get_dict(self) -> dict:
        """
        Return dict of ids, label, and properties.

        Returns:
            dict: source_id, target_id and relationship_label as
                top-level key-value pairs, properties as second-level
                dict.
        """
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relationship_label': self.relationship_label,
            'properties': self.properties,
        }

    @property
    def edges(self) -> tuple['BioCypherEdge']:
        """
        Create a tuple of edge(s).

        Returns:
            This edge in a single element tuple.
        """

        return (self,)

    @property
    def nodes(self) -> tuple:
        """
        Create a tuple of node(s).

        Returns:
            An empty tuple.
        """

        return ()

    @property
    def key(self) -> tuple[str, str]:
        """
        A key that identifies the group of graph components
        this item belongs to.
        """

        return (self.relationship_label, self.entity)


@dataclass(frozen=True)
class BioCypherRelAsNode:
    """
    Class to represent relationships as nodes.

    A relationship can be converted or alternatively represented as a node
    with in- and outgoing edges, ie. a triplet of a BioCypherNode and two
    BioCypherEdges. Main usage in type checking (instances where the
    receiving function needs to check whether it receives a relationship
    as a single edge or as a triplet).

    Args:
        node:
            Node representing the relationship.
        source_edge:
            Eedge representing the source of the relationship.
        target_edge:
            Edge representing the target of the relationship.
    """

    node: BioCypherNode
    source_edge: BioCypherEdge
    target_edge: BioCypherEdge

    def __post_init__(self):

        # wow, I thought dataclass at least does this out of the box
        for attr, t in self.__class__.__annotations__.items():

            if not isinstance(getattr(self, attr), t):

                raise TypeError(
                    f'{self.__class__.__name__}.{attr} must be '
                    f'of type `{t.__name__}`.',
                )

    def get_node(self):
        """
        The node representing the former relationship.
        """
        return self.node

    def get_source_edge(self):
        """
        The edge pointing to the source of the relationship.
        """
        return self.source_edge

    def get_target_edge(self) -> BioCypherEdge:
        """
        The edge pointing to the target of the relationship.
        """
        return self.target_edge

    @property
    def edges(self) -> tuple[BioCypherEdge, BioCypherEdge]:
        """
        Create a tuple of edge(s).

        Returns:
            The source and target edges in a two elements tuple.
        """

        return (self.source_edge, self.target_edge)

    @property
    def nodes(self) -> tuple[BioCypherNode]:
        """
        Create a tuple of node(s).

        Returns:
            An empty tuple.
        """

        return (self.node,)


class VersionNode:
    """
    Versioning and graph structure information meta node.

    Similar to BioCypherNode but fixes label to ":BioCypher" and sets
    version by using the current date and time (meaning it overrides both
    mandatory args from BioCypherNode).

    Is created upon establishment of connection with the database and remains
    fixed for each BioCypher "session" (ie, the entire duration from starting
    the connection to the termination of the BioCypher adapter instance). Is
    connected to MetaNodes and MetaEdges via ":CONTAINS" relationships.
    """

    def __init__(
            self,
            offline: bool = False,
            from_config: bool = False,
            config_file: str = None,
            node_label: str = 'BioCypher',
            bcy_driver: 'Driver' = None,
    ):
        """
        Create a node with schema and version information.

        Args:
            offline:
                No connection to server.
            from_config:
                Read the parameters from config, instead of an existing
                node in the database.
            config_file:
                Path to config file.
            node_label:
                Label of the version node.
            bcy_driver:
                A driver instance that supports the connection and already
                carries config data.
        """

        # if we do not have a driver, then likely we are offline, right?
        self.offline = offline or getattr(bcy_driver, 'offline', True)
        self.from_config = from_config
        self.config_file = config_file
        self.node_label = node_label
        self.bcy_driver = bcy_driver

        self.node_id = self._timestamp
        self.graph_state = (
            self._get_graph_state() if not self.offline else None
        )
        self.schema = self._get_graph_schema()
        self.leaves = self._get_leaves()

        self.properties = {
            'graph_state': self.graph_state,
            'schema': self.schema,
            'leaves': self.leaves,
        }

    def get_id(self) -> str:
        """
        Returns primary node identifier.

        Returns:
            str: node_id
        """
        return self.node_id

    def get_label(self) -> str:
        """
        Returns primary node label.

        Returns:
            str: node_label
        """
        return self.node_label

    def get_dict(self) -> dict:
        """
        Return dict of id, labels, and properties.

        Returns:
            dict: node_id and node_label as top-level key-value pairs,
            properties as second-level dict.
        """
        return {
            'node_id': self.node_id,
            'node_label': self.node_label,
            'properties': self.properties,
        }

    @property
    def _timestamp(self):
        """
        A timestampt that serves as unique ID for the current session.

        Instantiate a version ID for the current session. For now does
        versioning using datetime.

        Can later implement incremental versioning, versioning from
        config file, or manual specification via argument.
        """

        now = datetime.now()
        return now.strftime('v%Y%m%d-%H%M%S')

    @property
    def node_id(self):
        """
        Unique ID of the current session.
        """

        return self._node_id

    @node_id.setter
    def node_id(self, node_id: str) -> str:
        """
        Unique ID of the current session.
        """

        if hasattr(self, '_node_id'):

            raise TypeError('Changing `node_id` is not supported.')

        else:

            self._node_id = node_id

    def _get_graph_state(self):
        """
        Current graph state if available, otherwise create a new one.

        Check in active DBMS connection for existence of VersionNodes,
        return the most recent VersionNode as representation of the
        graph state. If no VersionNode found, assume blank graph state
        and initialise.
        """

        logger.info('Getting graph state.')

        result, summary = self.bcy_driver.query(
            'MATCH (meta:BioCypher)'
            'WHERE NOT (meta)-[:PRECEDES]->(:BioCypher)'
            'RETURN meta',
        )

        # if result is empty, initialise
        if not result:
            logger.info('No existing graph found, initialising.')
            return None
        # else, pass on graph state
        else:
            version = result[0]['meta']['id']
            logger.info(f'Found graph state at {version}.')
            return result[0]['meta']

    def _get_graph_schema(
        self,
        from_config: bool | None = None,
        config_file: str | None = None,
    ) -> dict:
        """
        The current schema.

        Returns:
            Graph schema information from meta graph if it exists, or
            create new schema information properties from configuration
            file.

        Todo:
            - get schema from meta graph
        """

        from_config = self.from_config if from_config is None else from_config
        config_file = config_file or self.config_file

        if self.graph_state and not from_config:
            # TODO do we want information about actual structure here?
            res = self.bcy_driver.query(
                'MATCH (src:MetaNode) '
                # "OPTIONAL MATCH (src)-[r]->(tar)"
                'RETURN src',  # , type(r) AS type, tar"
            )
            gs_dict = {}
            for r in res[0]:
                src = r['src']
                key = src.pop('id')
                gs_dict[key] = src

            return gs_dict

        else:
            # load default yaml from module
            # get graph state from config
            if config_file is not None:
                with open(config_file) as f:
                    dataMap = yaml.safe_load(f)
            else:
                dataMap = config.module_data('schema_config')

            return dataMap

    def _get_leaves(self, d: dict | None = None) -> dict:
        """
        Leaves of the schema.

        Get leaves of the tree hierarchy from the data structure dict
        contained in the `schema_config.yaml`. Creates virtual leaves
        (as children) from entries that provide more than one preferred
        id type (and corresponding inputs).

        Args:
            d:
                Data structure dict from yaml file.
        """

        d = d or self.schema

        leaves = {}
        max_depth = 0  # TODO needed? # ???

        # first pass: get parent leaves with direct representation in ontology
        for k, v in d.items():

            # k is not an entity
            if 'represented_as' not in v:
                continue

            # k is an entity that is present in the ontology
            if 'is_a' not in v:
                leaves[k] = v

            # find max depth of children
            else:
                lst = v['is_a'] if isinstance(v['is_a'], list) else [v['is_a']]
                max_depth = max(max_depth, len(lst))

        # second pass: "vertical" inheritance
        d = self._vertical_property_inheritance(d)
        # create leaves for all straight descendants (no multiple identifiers
        # or sources) -> explicit children
        # TODO do we need to order children by depth from real leaves?
        leaves.update({k: v for k, v in d.items() if 'is_a' in v})

        # "horizontal" inheritance: create siblings for multiple identifiers or
        # sources -> virtual leaves or implicit children
        mi_leaves = {}
        ms_leaves = {}
        for k, v in d.items():

            # k is not an entity
            if 'represented_as' not in v:
                continue

            if isinstance(v.get('preferred_id'), list):
                mi_leaves = self._horizontal_inheritance_pid(k, v)
                leaves.update(mi_leaves)

            elif isinstance(v.get('source'), list):
                ms_leaves = self._horizontal_inheritance_source(k, v)
                leaves.update(ms_leaves)

        return leaves

    def _vertical_property_inheritance(self, d):
        """
        Inherit properties from parents to children and update `d` accordingly.
        """
        for k, v in d.items():

            # k is not an entity
            if 'represented_as' not in v:
                continue

            # k is an entity that is present in the ontology
            if 'is_a' not in v:
                continue

            # "vertical" inheritance: inherit properties from parent
            if v.get('inherit_properties', False):

                # get direct ancestor
                if isinstance(v['is_a'], list):
                    parent = v['is_a'][0]
                else:
                    parent = v['is_a']

                # update properties of child
                if self.schema[parent].get('properties'):
                    v['properties'] = self.schema[parent]['properties']
                if self.schema[parent].get('exclude_properties'):
                    v['exclude_properties'] = self.schema[parent][
                        'exclude_properties'
                    ]

                # update schema (d)
                d[k] = v

        return d

    def _horizontal_inheritance(
            self,
            key: str,
            value: dict,
            by: Literal['source', 'preferred_id'],
        ) -> dict:
        """
        Create virtual leaves for multiple sources or preferred IDs.

        If we create virtual leaves, label_in_input always has to be a list.
        """

        leaves = {}

        variables = (by, 'label_in_input', 'represented_as')

        length = (
            len(value['source'])
                if by == 'source' else
            max(len(_misc.to_list(value[v])) for v in variables)
        )

        values = tuple(
            [value[v]] * length
                if isinstance(value[v], str) else
            value[v]
            for v in variables
        )

        for _by, lab, rep in zip(*values):

            skey = f'{_by}.{key}'
            leaves[skey] = value.copy()
            leaves[skey].update({
                by: _by,
                'label_in_input': lab,
                'represented_as': rep,
                'virtual': True,
                'is_a': [key] + _misc.to_list(value.get('is_a', []))
            })

        return leaves

    def _horizontal_inheritance_pid(self, key, value):
        """
        Create virtual leaves for multiple preferred id types or sources.

        If we create virtual leaves, label_in_input always has to be a list.
        """

        return self._horizontal_inheritance(
            key = key,
            value = value,
            by = 'preferred_id',
        )

    def _horizontal_inheritance_source(self, key, value):
        """
        Create virtual leaves for multiple sources.

        If we create virtual leaves, label_in_input always has to be a list.
        """

        return self._horizontal_inheritance(
            key = key,
            value = value,
            by = 'source',
        )


BC_TYPES = (
    BioCypherNode |
    BioCypherEdge |
    BioCypherRelAsNode
)
