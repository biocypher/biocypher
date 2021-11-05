#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module is used for assessing a Neo4j instance for compliance with the
BioCypher standard and returning pass/fail, and, in the event of "pass", it 
returns the primary identifiers chosen by the user of the active database
to be used in translation of the input data to the correct format required
for the active database. It is part of the BioCypher python package, 
homepage: TODO.


Copyright 2021, Heidelberg University Clinic

File author(s): Sebastian Lobentanzer
                ...

Distributed under GPLv3 license, see LICENSE.txt.

Todo: 
    - when to do versioning?
        - setting in config file regarding the granularity?
    - a unique node with label ":BioCypher" and id representing basic versioning
        that carries information about the preferred primary identifiers etc as
        properties and that gets updated each time the graph is modified?
        - versioning could be the date of change
"""

from .create import BioCypherEdge, BioCypherNode
from datetime import datetime
import yaml


class MetaNode(BioCypherNode):
    """
    Graph structure information node representing node type entities in the 
    BioCypher graph. Inherits from BioCypherNode but fixes label to 
    ":MetaNode". Is connected to VersionNode via ":CONTAINS" relationship.
    """

    def __init__(
        self, node_id, node_label = "MetaNode", 
        optional_labels=None, **properties
    ):
        super().__init__(node_id, node_label, optional_labels, **properties)


class MetaEdge(BioCypherEdge):
    """
    Graph structure information edge in the meta-graph. Inherits from 
    BioCypherNode but fixes label to ":CONTAINS".
    """

    def __init__(
        self, source_id, target_id, 
        relationship_label = "CONTAINS", **properties
    ):
        super().__init__(source_id, target_id, relationship_label, **properties)



class VersionNode(BioCypherNode):
    """
    Versioning and graph structure information meta node. Inherits from 
    BioCypherNode but fixes label to ":BioCypher" and sets version 
    by using the current date and time (meaning it overrides both 
    mandatory args from BioCypherNode).

    Is created upon establishment of connection with the database and remains
    fixed for each BioCypher "session" (ie, the entire duration from starting
    the connection to the termination of the BioCypher adapter instance). Is 
    connected to MetaNodes and MetaEdges via ":CONTAINS" relationships.

    Todo:
        - granularity of versioning?
            - if many short calls are made in a short amount of time, closing
                biocypher after each call, the number of meta-nodes would be
                too large. on the other hand, one node per day may be too 
                little for some.
        - could implement a continuous versioning system where we get the most 
            recent version from the graph and add one increment, or a way to 
            pass in an arbitrary version of choice.
        - way to instantiate the MetaNode without having to give id and label?
            - can only think of creating a parent to both BioCypherNode and 
                MetaNode that does not have mandatory id and label.
        - put in create or here?
        - add graph structure information
            - on creation will be generated from yml or json?
                - yml is more readable
            - as dict? from yml/json?
    """
    

    def __init__(
        self, bcy_driver, 
        node_id = None, node_label = "BioCypher", 
        **properties
    ):

        super().__init__(node_id, node_label, **properties)
        self.bcy_driver = bcy_driver
        self.node_id = self.get_current_id()
        self.node_label = node_label
        self.graph_state = self.get_graph_state()
        self.schema = self.get_graph_schema()


    def get_current_id(self):
        """
        Versioning using datetime.
        """

        now = datetime.now()
        return now.strftime("v%Y%m%d%:%H%M%S")


    def get_graph_state(self):
        """
        Check in active DBMS connection for existence of MetaNodes, return
        the most recent MetaNode as representation of the graph state. If no
        MetaNode found, assume blank graph state and initialise.
        """

        result = self.bcy_driver.query(
            'MATCH (meta:BioCypher)'
            'WHERE NOT (meta)-[:PRECEDES]->(:BioCypher)'
            'RETURN meta')


        # if result is empty, initialise
        if len(result) == 0:
            return None
        # else, pass on graph state
        else:
            return result[0]['meta']


    def get_graph_schema(self):
        """
        Return graph schema information from meta node if it exists, or create
        new schema information properties from configuration file.
        """

        # get graph state from config
        with open('schema_config.yaml') as f:
            dataMap = yaml.safe_load(f)
        return dataMap