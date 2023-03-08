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

from typing import Union, Optional
from datetime import datetime
from dataclasses import field, dataclass
from urllib.request import urlopen
import os

import yaml

from . import _misc
from . import _config as config
from ._logger import logger

__all__ = [
    'BioCypherEdge',
    'BioCypherNode',
    'BioCypherRelAsNode',
    'VersionNode',
]

logger.debug(f'Loading module {__name__}.')


@dataclass(frozen=True)
class BioCypherNode:
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
        self.properties['id'] = self.node_id
        self.properties['preferred_id'] = self.preferred_id or None
        # TODO actually make None possible here; as is, "id" is the default in
        # the dataclass as well as in the configuration file

        if ':TYPE' in self.properties.keys():
            logger.warning(
                "Keyword ':TYPE' is reserved for Neo4j. "
                'Removing from properties.',
                # "Renaming to 'type'."
            )
            # self.properties["type"] = self.properties[":TYPE"]
            del self.properties[':TYPE']

        for k, v in self.properties.items():
            if isinstance(v, str):
                self.properties[k] = (
                    v.replace(
                        os.linesep,
                        ' ',
                    ).replace(
                        '\n',
                        ' ',
                    ).replace(
                        '\r',
                        ' ',
                    ).replace('"', "'")
                )

            elif isinstance(v, list):
                self.properties[k] = (
                    [
                        val.replace(
                            os.linesep,
                            ' ',
                        ).replace(
                            '\n',
                            ' ',
                        ).replace('\r', ' ') for val in v
                    ]
                )

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

    def get_preferred_id(self) -> str:
        """
        Returns preferred id.

        Returns:
            str: preferred_id
        """
        return self.preferred_id

    def get_properties(self) -> dict:
        """
        Returns all other node properties apart from primary id and
        label as key-value pairs.

        Returns:
            dict: properties
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


@dataclass(frozen=True)
class BioCypherEdge:
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

        source_id (string): consensus "best" id for biological entity

        target_id (string): consensus "best" id for biological entity

        relationship_label (string): type of interaction, UPPERCASE

        properties (dict): collection of all other properties of the
        respective edge

    """

    source_id: str
    target_id: str
    relationship_label: str
    relationship_id: str = None
    properties: dict = field(default_factory=dict)

    def __post_init__(self):
        """
        Check for reserved keywords.
        """

        if ':TYPE' in self.properties.keys():
            logger.debug(
                "Keyword ':TYPE' is reserved for Neo4j. "
                'Removing from properties.',
                # "Renaming to 'type'."
            )
            # self.properties["type"] = self.properties[":TYPE"]
            del self.properties[':TYPE']

    def get_id(self) -> Union[str, None]:
        """
        Returns primary node identifier or None.

        Returns:
            str: node_id
        """

        return self.relationship_id

    def get_source_id(self) -> str:
        """
        Returns primary node identifier of relationship source.

        Returns:
            str: source_id
        """
        return self.source_id

    def get_target_id(self) -> str:
        """
        Returns primary node identifier of relationship target.

        Returns:
            str: target_id
        """
        return self.target_id

    def get_label(self) -> str:
        """
        Returns relationship label.

        Returns:
            str: relationship_label
        """
        return self.relationship_label

    def get_properties(self) -> dict:
        """
        Returns all other relationship properties apart from primary ids
        and label as key-value pairs.

        Returns:
            dict: properties
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


@dataclass(frozen=True)
class BioCypherRelAsNode:
    """
    Class to represent relationships as nodes (with in- and outgoing
    edges) as a triplet of a BioCypherNode and two BioCypherEdges. Main
    usage in type checking (instances where the receiving function needs
    to check whether it receives a relationship as a single edge or as
    a triplet).

    Args:

        node (BioCypherNode): node representing the relationship

        source_edge (BioCypherEdge): edge representing the source of the
            relationship

        target_edge (BioCypherEdge): edge representing the target of the
            relationship

    """

    node: BioCypherNode
    source_edge: BioCypherEdge
    target_edge: BioCypherEdge

    def __post_init__(self):
        if not isinstance(self.node, BioCypherNode):
            raise TypeError(
                f'BioCypherRelAsNode.node must be a BioCypherNode, '
                f'not {type(self.node)}.',
            )

        if not isinstance(self.source_edge, BioCypherEdge):
            raise TypeError(
                f'BioCypherRelAsNode.source_edge must be a BioCypherEdge, '
                f'not {type(self.source_edge)}.',
            )

        if not isinstance(self.target_edge, BioCypherEdge):
            raise TypeError(
                f'BioCypherRelAsNode.target_edge must be a BioCypherEdge, '
                f'not {type(self.target_edge)}.',
            )

    def get_node(self):
        return self.node

    def get_source_edge(self):
        return self.source_edge

    def get_target_edge(self) -> BioCypherEdge:
        return self.target_edge


class VersionNode:
    """
    Versioning and graph structure information meta node. Similar to
    BioCypherNode but fixes label to ":BioCypher" and sets version by using the
    current date and time (meaning it overrides both mandatory args from
    BioCypherNode).

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
        bcy_driver=None,
    ):

        logger.warning('VersionNode is deprecated.')

        # if we do not have a driver, then likely we are offline, right?
        self.offline = offline or getattr(bcy_driver, 'offline', True)
        self.from_config = from_config
        self.config_file = config_file
        self.node_label = node_label
        self.bcy_driver = bcy_driver

        self.node_id = self._get_current_id()
        self.graph_state = (
            self._get_graph_state() if not self.offline else None
        )
        self.schema = self._get_graph_schema()
        self.extended_schema = self._get_leaves()

        self.properties = {
            'graph_state': self.graph_state,
            'schema': self.schema,
            'leaves': self.extended_schema,
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

    def _get_current_id(self):
        """
        Instantiate a version ID for the current session. For now does
        versioning using datetime.

        Can later implement incremental versioning, versioning from
        config file, or manual specification via argument.
        """

        now = datetime.now()
        return now.strftime('v%Y%m%d-%H%M%S')

    def _get_graph_state(self):
        """
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
        from_config: Optional[bool] = None,
        config_file: Optional[str] = None,
    ) -> dict:
        """
        Return graph schema information from meta graph if it exists, or
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
            if config_file is None:

                dataMap = config.module_data('schema_config')

            # load yaml file from web
            elif config_file.startswith('http'):

                with urlopen(config_file) as f:

                    dataMap = yaml.safe_load(f)

            # get graph state from config (assume file is local)
            else:

                with open(config_file, 'r') as f:

                    dataMap = yaml.safe_load(f)

            return dataMap

    def _get_leaves(self, d: Optional[dict] = None) -> dict:
        """
        Get leaves of the tree hierarchy from the data structure dict
        contained in the `schema_config.yaml`. Creates virtual leaves
        (as children) from entries that provide more than one preferred
        id type (and corresponding inputs).

        Args:
            d:
                Data structure dict from yaml file.

        """

        d = d or self.schema

        leaves = dict()
        max_depth = 0  # TODO needed?

        # first pass: get parent leaves with direct representation in ontology
        for k, v in d.items():

            # k is not an entity
            if 'represented_as' not in v:
                continue

            # preferred_id optional: if not provided, use `id`
            if not v.get('preferred_id'):
                v['preferred_id'] = 'id'

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
                        'exclude_properties']

                # update schema (d)
                d[k] = v

        return d

    def _horizontal_inheritance_pid(self, key, value):
        """
        Create virtual leaves for multiple preferred id types or sources.

        If we create virtual leaves, label_in_input always has to be a list.
        """

        leaves = {}

        preferred_id = value['preferred_id']
        label_in_input = value['label_in_input']
        represented_as = value['represented_as']

        # adjust lengths
        max_l = max(
            [
                len(_misc.to_list(preferred_id)),
                len(_misc.to_list(label_in_input)),
                len(_misc.to_list(represented_as)),
            ],
        )

        # adjust pid length if necessary
        if isinstance(preferred_id, str):
            pids = [preferred_id] * max_l
        else:
            pids = preferred_id

        # adjust rep length if necessary
        if isinstance(represented_as, str):
            reps = [represented_as] * max_l
        else:
            reps = represented_as

        for pid, lab, rep in zip(pids, label_in_input, reps):

            skey = pid + '.' + key
            svalue = {
                'preferred_id': pid,
                'label_in_input': lab,
                'represented_as': rep,
                # mark as virtual
                'virtual': True,
            }

            # inherit is_a if exists
            if 'is_a' in value.keys():

                # treat as multiple inheritance
                if isinstance(value['is_a'], list):
                    v = list(value['is_a'])
                    v.insert(0, key)
                    svalue['is_a'] = v

                else:
                    svalue['is_a'] = [key, value['is_a']]

            else:
                # set parent as is_a
                svalue['is_a'] = key

            # inherit everything except core attributes
            for k, v in value.items():
                if k not in [
                    'is_a',
                    'preferred_id',
                    'label_in_input',
                    'represented_as',
                ]:
                    svalue[k] = v

            leaves[skey] = svalue

        return leaves

    def _horizontal_inheritance_source(self, key, value):
        """
        Create virtual leaves for multiple sources.

        If we create virtual leaves, label_in_input always has to be a list.
        """

        leaves = {}

        source = value['source']
        label_in_input = value['label_in_input']
        represented_as = value['represented_as']

        # adjust lengths
        src_l = len(source)

        # adjust label length if necessary
        if isinstance(label_in_input, str):
            labels = [label_in_input] * src_l
        else:
            labels = label_in_input

        # adjust rep length if necessary
        if isinstance(represented_as, str):
            reps = [represented_as] * src_l
        else:
            reps = represented_as

        for src, lab, rep in zip(source, labels, reps):

            skey = src + '.' + key
            svalue = {
                'source': src,
                'label_in_input': lab,
                'represented_as': rep,
                # mark as virtual
                'virtual': True,
            }

            # inherit is_a if exists
            if 'is_a' in value.keys():

                # treat as multiple inheritance
                if isinstance(value['is_a'], list):
                    v = list(value['is_a'])
                    v.insert(0, key)
                    svalue['is_a'] = v

                else:
                    svalue['is_a'] = [key, value['is_a']]

            else:
                # set parent as is_a
                svalue['is_a'] = key

            # inherit everything except core attributes
            for k, v in value.items():
                if k not in [
                    'is_a',
                    'source',
                    'label_in_input',
                    'represented_as',
                ]:
                    svalue[k] = v

            leaves[skey] = svalue

        return leaves
