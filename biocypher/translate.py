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
    - genericise: standardise input data to BioCypher specifications or, 
        optionally, user specifications.
        - if the database exists, read biocypher info node
        - if newly created, ask for user input as to which IDs to use etc
        - default scenario?
    - type checking
    - which system for storage? json dump/load? has the advantage of being human-
        readable
    - import ID types from pypath dictionary (later, externalised dictionary)?
"""

from .create import BioCypherEdge, BioCypherNode
from bmt import Toolkit


class BiolinkAdapter(object):
    """
    Performs various functions to integrate the Biolink ontology.
    """

    def __init__(self, leaves) -> None:
        super().__init__()
        self.leaves = self.translate_leaves_to_biolink(leaves)


    def translate_leaves_to_biolink(self, leaves):
        t = Toolkit()
        l = []
        for entity in leaves.keys():
            e = t.get_element(entity) # element name
            if e is not None:
                l.append([entity, e])
            else:
                print("Entity not found:" + entity[0])
                l.append([entity, None])
        
        return l

# -------------------------------------------
# Create nodes and edges from separate inputs
# -------------------------------------------

def gen_translate_nodes(leaves, id_type_tuples):
    """
    Translates input node representation to a representation that conforms
    to the schema of the given BioCypher graph. For now requires explicit 
    statement of node type on pass.


    """

    # biolink = BiolinkAdapter(leaves)

    for id, type in id_type_tuples:
        path = getpath(leaves, type)

        if path is not None:
            bl_type = path[0]
            yield BioCypherNode(
                node_id=id,
                node_label=bl_type,
                # additional here
            )

        else:
            print("No path for type " + type)


def gen_translate_edges(leaves, src_tar_type_tuples):
    """
    Translates input edge representation to a representation that conforms
    to the schema of the given BioCypher graph. For now requires explicit 
    statement of edge type on pass.


    """

    for src, tar, type in src_tar_type_tuples:
        path = getpath(leaves, type)

        if path is not None:
            bl_type = path[0]
            rep = leaves[bl_type]['represented_as']

            if rep == 'node':
                node_id = src + "->" + tar
                n = BioCypherNode(
                    node_id=node_id,
                    node_label=bl_type,
                    # additional here
                )
                e_s = BioCypherEdge(
                    source_id=src,
                    target_id=node_id,
                    relationship_label="IS_SOURCE_OF",
                    # additional here
                )
                e_t = BioCypherEdge(
                    source_id=tar,
                    target_id=node_id,
                    relationship_label="IS_TARGET_OF",
                    # additional here
                )
                yield (n, e_s, e_t)
            
            else:
                edge_label = leaves[bl_type]['label_as_edge']
                yield BioCypherEdge(
                    source_id=src,
                    target_id=tar,
                    relationship_label=edge_label,
                    # additional here
                )

        else:
            print("No path for type " + type)



    

def edges_from_pypath(records):
    return(BioCypherEdge.create_relationship_list(records))

# quick and dirty replacement functions
# this belongs in translate or in the pypath adapter directly


def getpath(nested_dict, value, prepath=()):
    for k, v in nested_dict.items():
        path = prepath + (k,)
        if v == value: # found value
            return path
        elif hasattr(v, 'items'): # v is a dict
            p = getpath(v, value, path) # recursive call
            if p is not None:
                return p
