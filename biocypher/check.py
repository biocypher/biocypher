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
    - implement
    - a unique node with label ":BioCypher" and id representing basic versioning
        that carries information about the preferred primary identifiers etc as
        properties and that gets updated each time the graph is modified?
        - versioning could be the date of change
"""

from .create import BioCypherNode
from datetime import datetime


class MetaNode(BioCypherNode):
    """
    Versioning and graph structure information meta node. Inherits from 
    BioCypherNode but sets label to fixed ":BioCypher" and sets version 
    by using the current date and time.

    Todo:
        - could implement a continuous versioning system where we get the most 
            recent version from the graph and add one increment.
        - way to instantiate the MetaNode without having to give id and label?
        - put in create or here?
    """
    
    def __init__(self, node_id, node_label, **properties):
        super().__init__(node_id, node_label, **properties)
        self.node_id = self.get_current_id()
        self.node_label = ":BioCypher"

    def get_current_id(self):
        now = datetime.now()
        return now.strftime("v%Y%M%d%:%H%M%S")

