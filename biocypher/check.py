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
Read and write BioCypher config of a Neo4j database instance.
Each BioCypher database contains a configuration encoded in the graph itself.
This configuration includes the version of the BioCypher standard, the
preferred identifier types, etc.

Todo:
    - connect graph structure setup (from config) with data parsing
    - when to do versioning?
        - setting in config file regarding the granularity?
"""

from .logger import logger
logger.debug(f"Loading module {__name__}.")

from .create import BioCypherEdge, BioCypherNode
from datetime import datetime
import yaml
import os


class MetaNode(BioCypherNode):
    """
    Graph structure information node representing node type entities in
    the BioCypher graph. Inherits from BioCypherNode but fixes label to
    ":MetaNode". Is connected to VersionNode via ":CONTAINS"
    relationship.
    """

    def __init__(
        self,
        node_id,
        node_label="MetaNode",
        optional_labels=None,
        **properties,
    ):
        super().__init__(node_id, node_label, optional_labels, **properties)


class MetaEdge(BioCypherEdge):
    """
    Graph structure information edge in the meta-graph. Inherits from
    BioCypherNode but fixes label to ":CONTAINS".
    """

    def __init__(
        self, source_id, target_id, relationship_label="CONTAINS", **properties
    ):
        super().__init__(
            source_id, target_id, relationship_label, **properties
        )


class VersionNode(BioCypherNode):
    """
    Versioning and graph structure information meta node. Inherits from
    BioCypherNode but fixes label to ":BioCypher" and sets version
    by using the current date and time (meaning it overrides both
    mandatory args from BioCypherNode).

    Is created upon establishment of connection with the database and
    remains fixed for each BioCypher "session" (ie, the entire duration
    from starting the connection to the termination of the BioCypher
    adapter instance). Is connected to MetaNodes and MetaEdges via
    ":CONTAINS" relationships.

    Todo:

        - granularity of versioning?
        - way to instantiate the MetaNode without having to give id and
          label?

            - can only think of creating a parent to both BioCypherNode
              and MetaNode that does not have mandatory id and label.

        - add graph structure information
        - on creation will be generated from yml or json?

            - yml is more readable
            - as dict? from yml/json?
    """

    def __init__(
        self,
        bcy_driver,
        node_id=None,
        node_label="BioCypher",
        from_config=False,
        **properties,
    ):

        super().__init__(node_id, node_label, **properties)
        self.bcy_driver = bcy_driver
        self.node_id = self.get_current_id()
        self.node_label = node_label
        self.graph_state = self.get_graph_state()
        self.schema = self.get_graph_schema(from_config=from_config)
        self.leaves = self.get_leaves(self.schema)

    def get_current_id(self):
        """
        Instantiate a version ID for the current session. For now does
        versioning using datetime.

        Can later implement incremental versioning, versioning from
        config file, or manual specification via argument.
        """

        now = datetime.now()
        return now.strftime("v%Y%m%d-%H%M%S")

    def get_graph_state(self):
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
            "RETURN meta"
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

    def get_graph_schema(self, from_config):
        """
        Return graph schema information from meta graph if it exists, or
        create new schema information properties from configuration
        file.

        Todo:
            - get schema from meta graph
        """
        if self.graph_state and not from_config:
            # TODO do we want information about actual structure here?
            res = self.bcy_driver.query(
                "MATCH (src:MetaNode) "
                # "OPTIONAL MATCH (src)-[r]->(tar)"
                "RETURN src"  # , type(r) AS type, tar"
            )
            gs_dict = {}
            for r in res[0]:
                src = r["src"]
                key = src.pop("id")
                gs_dict[key] = src

            return gs_dict

        else:
            # load default yaml from module
            ROOT = os.path.join(
                *os.path.split(
                    os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
                )
            )

            # get graph state from config
            with open(ROOT + "/config/schema_config.yaml") as f:
                dataMap = yaml.safe_load(f)
            return dataMap

    def get_leaves(self, d):
        """
        Get leaves of the tree hierarchy from the data structure dict
        contained in the `schema_config.yaml`. Serves no purpose
        currently since the decision to have the `schema_config.yaml`
        represent only the direct constituents of the desired graph and
        not the complete hierarchy any more; this will be derived from
        the (modified) Biolink model. Now only does filtering of the
        schema for entities that have a "represented_as" property.

        Will leave in since the "leaves" are a nice visual cue for the
        hierarchical representation of graph constituents.
        """
        leaves = dict()
        stack = list(d.items())
        visited = set()
        while stack:
            key, value = stack.pop()
            if isinstance(value, dict):
                if "represented_as" not in value.keys():
                    if key not in visited:
                        stack.extend(value.items())
                else:
                    leaves[key] = value
            visited.add(key)

        return leaves
