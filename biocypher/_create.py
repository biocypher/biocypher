#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from typing import Optional
from datetime import datetime
from dataclasses import field, dataclass

import yaml

from . import _misc
from . import _config as config
from ._logger import logger

logger.debug(f"Loading module {__name__}.")


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
    preferred_id: str = "id"
    properties: dict = field(default_factory=dict)

    def __post_init__(self):
        """
        Check for preferred id and add to properties if present.

        Check for reserved keywords.
        """
        if not self.preferred_id == "id":
            self.properties[self.preferred_id] = self.node_id

        if ":TYPE" in self.properties.keys():
            logger.warning(
                "Keyword ':TYPE' is reserved for Neo4j. "
                "Removing from properties."
                # "Renaming to 'type'."
            )
            # self.properties["type"] = self.properties[":TYPE"]
            del self.properties[":TYPE"]

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
            "node_id": self.node_id,
            "node_label": self.node_label,
            "properties": self.properties,
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
    properties: dict = field(default_factory=dict)

    def __post_init__(self):
        """
        Check for reserved keywords.
        """

        if ":TYPE" in self.properties.keys():
            logger.debug(
                "Keyword ':TYPE' is reserved for Neo4j. "
                "Removing from properties."
                # "Renaming to 'type'."
            )
            # self.properties["type"] = self.properties[":TYPE"]
            del self.properties[":TYPE"]

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
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_label": self.relationship_label,
            "properties": self.properties,
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
                f"BioCypherRelAsNode.node must be a BioCypherNode, "
                f"not {type(self.node)}."
            )

        if not isinstance(self.source_edge, BioCypherEdge):
            raise TypeError(
                f"BioCypherRelAsNode.source_edge must be a BioCypherEdge, "
                f"not {type(self.source_edge)}."
            )

        if not isinstance(self.target_edge, BioCypherEdge):
            raise TypeError(
                f"BioCypherRelAsNode.target_edge must be a BioCypherEdge, "
                f"not {type(self.target_edge)}."
            )

    def get_node(self):
        return self.node

    def get_source_edge(self):
        return self.source_edge

    def get_target_edge(self) -> BioCypherEdge:
        return self.target_edge


class VersionNode:
    """
    Versioning and graph structure information meta node. Inherits from
    # TODO: it doesn't inherit from BCNode
    # and the label comes from the argument
    BioCypherNode but fixes label to ":BioCypher" and sets version
    by using the current date and time (meaning it overrides both
    mandatory args from BioCypherNode).

    Is created upon establishment of connection with the database and
    remains fixed for each BioCypher "session" (ie, the entire duration
    from starting the connection to the termination of the BioCypher
    adapter instance). Is connected to MetaNodes and MetaEdges via
    ":CONTAINS" relationships.
    """

    def __init__(
        self,
        offline: bool = False,
        from_config: bool = False,
        config_file: str = None,
        node_label: str = "BioCypher",
        bcy_driver=None,
    ):

        # if we do not have a driver, then likely we are offline, right?
        self.offline = offline or getattr(bcy_driver, "offline", True)
        self.from_config = from_config
        self.config_file = config_file
        self.node_label = node_label
        self.bcy_driver = bcy_driver

        self.node_id = self._get_current_id()
        self.graph_state = (
            self._get_graph_state() if not self.offline else None
        )
        self.schema = self._get_graph_schema()
        self.leaves = self._get_leaves()

        self.properties = {
            "graph_state": self.graph_state,
            "schema": self.schema,
            "leaves": self.leaves,
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
            "node_id": self.node_id,
            "node_label": self.node_label,
            "properties": self.properties,
        }

    def _get_current_id(self):
        """
        Instantiate a version ID for the current session. For now does
        versioning using datetime.

        Can later implement incremental versioning, versioning from
        config file, or manual specification via argument.
        """

        now = datetime.now()
        return now.strftime("v%Y%m%d-%H%M%S")

    def _get_graph_state(self):
        """
        Check in active DBMS connection for existence of VersionNodes,
        return the most recent VersionNode as representation of the
        graph state. If no VersionNode found, assume blank graph state
        and initialise.
        """

        logger.info("Getting graph state.")

        result, summary = self.bcy_driver.query(
            "MATCH (meta:BioCypher)"
            "WHERE NOT (meta)-[:PRECEDES]->(:BioCypher)"
            "RETURN meta",
        )

        # if result is empty, initialise
        if not result:
            logger.info("No existing graph found, initialising.")
            return None
        # else, pass on graph state
        else:
            version = result[0]["meta"]["id"]
            logger.info(f"Found graph state at {version}.")
            return result[0]["meta"]

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
                "MATCH (src:MetaNode) "
                # "OPTIONAL MATCH (src)-[r]->(tar)"
                "RETURN src",  # , type(r) AS type, tar"
            )
            gs_dict = {}
            for r in res[0]:
                src = r["src"]
                key = src.pop("id")
                gs_dict[key] = src

            return gs_dict

        else:
            # load default yaml from module
            # get graph state from config
            if config_file is not None:
                with open(config_file, "r") as f:
                    dataMap = yaml.safe_load(f)
            else:
                dataMap = config.module_data("schema_config")

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

        TODO: allow multiple leaves with same Biolink name but different
        specs? (eg ProteinToDiseaseAssociation from two different
        entries in CKG, DETECTED_IN_PATHOLOGY_SAMPLE and ASSOCIATED_WITH)
        """

        d = d or self.schema

        leaves = dict()
        stack = list(d.items())
        visited = set()

        while stack:

            key, value = stack.pop()

            if isinstance(value, dict):
                # using `represented_as` as a marker for an entity
                # TODO find something better
                if "represented_as" not in value.keys():
                    if key not in visited:
                        stack.extend(value.items())

                else:

                    # create virtual leaves for multiple preferred id types
                    if isinstance(value.get("preferred_id"), list):
                        # create "virtual" leaves for each preferred
                        # id

                        # adjust lengths (if representation and/or id are
                        # not given as lists but inputs are multiple)
                        l = len(_misc.to_list(value["label_in_input"]))
                        # adjust pid length if necessary
                        if isinstance(value["preferred_id"], str):
                            pids = [value["preferred_id"]] * l
                        else:
                            pids = value["preferred_id"]
                        # adjust rep length if necessary
                        if isinstance(value["represented_as"], str):
                            reps = [value["represented_as"]] * l
                        else:
                            reps = value["represented_as"]

                        for pid, label, rep in zip(
                            pids,
                            value["label_in_input"],
                            reps,
                        ):
                            skey = pid + "." + key
                            svalue = {
                                "preferred_id": pid,
                                "label_in_input": label,
                                "represented_as": rep,
                                # mark as virtual
                                "virtual": True,
                            }
                            # inherit is_a if exists
                            if "is_a" in value.keys():
                                # treat as multiple inheritance
                                svalue["is_a"] = [key, value["is_a"]]
                            # inherit properties if exist
                            if value.get("properties"):
                                svalue["properties"] = value["properties"]
                            # inherit edge label if exists
                            if value.get("label_as_edge"):
                                svalue["label_as_edge"] = value[
                                    "label_as_edge"
                                ]
                            leaves[skey] = svalue

                    # create virtual leaves for multiple sources
                    elif isinstance(value.get("source"), list):
                        # create "virtual" leaves for each source

                        # adjust lengths (if representation and/or id are
                        # not given as lists but inputs are multiple)
                        l = len(value["source"])

                        # adjust label length if necessary
                        if isinstance(value["label_in_input"], str):
                            labels = [value["label_in_input"]] * l
                        else:
                            labels = value["label_in_input"]
                        # adjust rep length if necessary
                        if isinstance(value["represented_as"], str):
                            reps = [value["represented_as"]] * l
                        else:
                            reps = value["represented_as"]

                        for source, label, rep in zip(
                            value["source"], labels, reps
                        ):
                            skey = source + "." + key
                            svalue = {
                                "source": source,
                                "label_in_input": label,
                                "represented_as": rep,
                                # mark as virtual
                                "virtual": True,
                            }
                            # inherit is_a if exists
                            if "is_a" in value.keys():
                                # treat as multiple inheritance
                                svalue["is_a"] = [key, value["is_a"]]
                            # inherit properties if exist
                            if value.get("properties"):
                                svalue["properties"] = value["properties"]
                            # inherit edge label if exists
                            if value.get("label_as_edge"):
                                svalue["label_as_edge"] = value[
                                    "label_as_edge"
                                ]
                            leaves[skey] = svalue
                    # finally, add parent
                    leaves[key] = value

            visited.add(key)

        return leaves
