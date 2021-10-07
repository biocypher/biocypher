#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles the lookup and storage of entity IDs that are part of the
BioCypher structure. It is part of the BioCypher python package, homepage: TODO.


Copyright 2021, Heidelberg University Clinic

File author(s): Sebastian Lobentanzer
                ...

Distributed under GPLv3 license, see LICENSE.txt.

Todo: 
    - genericise
    - type checking
    - which system for storage? json dump/load? has the advantage of being human-
        redable
    - import ID types from pypath dictionary (later, externalised dictionary)?
"""

from .create import BioCypherEdge, BioCypherNode

def nodes_from_pypath(values):
    return(BioCypherNode.create_node_list(values))

def edges_from_pypath(records):
    return(BioCypherEdge.create_relationship_list(records))