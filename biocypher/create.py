#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module is used for the creating a generic property graph database 
for use in biomedical research applications. It takes as inputs ordered 
collections of biomedical nodes and relationships and yields specific 
classes for property graph nodes and edges that adhere to the BioCypher 
standard. It is part of the BioCypher python package, homepage: TODO. 


Copyright 2021, Heidelberg University Clinic

File author(s): Sebastian Lobentanzer
                ...

Distributed under GPLv3 license, see LICENSE.txt.

Todo:

    - ensure that all relationship source and target IDs are in the node 
      list? Or in the graph? Would require direct connection...
    - Calls to the classes are independent, so there is no way to 
      check directly; nodes can be created at any point in time 
      previous to edge creation. We could require a pass of all 
      the nodes in the graph when creating edges. Pro: this would 
      also allow a check whether the existing graph adheres to 
      BioCypher, at least in the node domain. If it doesn't, 
      the call does not make much sense.

        - We could pass in the driver/session object into the BioCypher 
          class.

    - alternatively, do we merge the relationship, creating new nodes in 
      the process? could lead to duplications when nodes are created 
      that exist in the graph but there is confusion with the ID. 
      could be prevented by BioCypher knowing about the ENTIRE pool of 
      possible nodes.
    - allow custom node and edge labels / annotation?
    - establish a dictionary lookup with the id types to be used / basic 
      type checking of the input
    - translation of id types using pypath translation facilities (to be 
      later externalised)
    - provide options to the user:

        - primary id type(s) of their liking (critical, does not 
          guarantee interoperability: do we want this?)

            - there could be multiple "standard cases" of graph, and 
              upon choosing or detecting one of these, BioCypher could 
              translate
              
        - granularity: the ability to opt out (!) of the more detailed 
          structural components (opt in would again not guarantee 
          interoperability)
"""

# Futures
# from __future__ import


# Built-in/Generic Imports
import os
import sys

from .logger import get_logger

logger = get_logger(__name__)
logger.debug(f"Loading module {__name__}.")

# Libs
# import pandas


# pypath needs to be installed locally from current GitHub version
# import pypath.utils.mapping as mapping


class BioCypherNode:
    """
    Handoff class to represent biomedical entities as Neo4j nodes.

    Has id, label, property dict; id and label (in the Neo4j sense of a
    label, ie, the entity descriptor after the colon, such as
    ":Protein") are non-optional and called node_id and node_label to
    avoid confusion with "label" properties. Node labels are written in
    CamelBack and as nouns, as per Neo4j consensus.

    Args:
        node_id: consensus "best" id for biological entity (string)
        node_label: primary type of entity, capitalised (string)
        **properties (kwargs): collection of all other properties to be
            passed to neo4j for the respective node (dict)

    Todo:
        - "allowed list" of property names
        - account for all properties automatically
        - input of properties explicit via kwargs, or require user to
            pass dicts directly?
        - check and correct small inconsistencies such as capitalisation
            of ID names ("uniprot" vs "UniProt")
        - check for correct ID patterns (eg "ENSG" + string of numbers,
            uniprot length)
        - ID conversion using pypath translation facilities for now
        - one label is required as a minimum, but do we want multiple
            hierarchical labels? if so, how do we implement optional
            secondary labels?
    """

    def __init__(
        self, node_id, node_label, optional_labels=None, **properties
    ):
        self.node_id = node_id
        self.node_label = node_label
        self.properties = properties

        if optional_labels is not None:
            if type(optional_labels) is list:
                self.optional_labels = optional_labels
            else:
                raise Exception("Optional labels expected as list of strings.")

    def get_id(self):
        """
        Returns primary node identifier.

        Returns:
            str: node_id
        """
        return self.node_id

    def get_label(self):
        """
        Returns primary node label.

        Returns:
            str: node_label
        """
        return self.node_label

    def get_optional_labels(self):
        """
        Returns all optional labels.

        Returns:
            dict: properties
        """
        return self.optional_labels

    def get_properties(self):
        """
        Returns all other node properties apart from primary id and
        label as key-value pairs.

        Returns:
            dict: properties
        """
        return self.properties

    def get_dict(self):
        """
        Convert self to format accepted by Neo4j driver (Python dict ->
        Neo4j Map).

        Returns:
            dict: node_id and node_label as top-level key-value pairs,
            properties as second-level dict.
        """
        d = {}
        d.update(
            [
                ("node_id", self.node_id),
                ("node_label", self.node_label),
                ("properties", self.properties),
            ]
        )
        return d


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
        source_id, target_id: consensus "best" id for biological entity
            (string)
        relationship_label: type of interaction, UPPERCASE (string)
        **properties (kwargs): collection of all other properties to be
            passed to Neo4j for the respective edge (dict)

    Todo:
        - account for all properties that may be passed automatically
        - check structural consistency with BioCypher standard
    """

    def __init__(self, source_id, target_id, relationship_label, **properties):
        self.source_id = source_id
        self.target_id = target_id
        self.relationship_label = relationship_label
        self.properties = properties

    def get_source_id(self):
        """
        Returns primary node identifier of relationship source.

        Returns:
            str: source_id
        """
        return self.source_id

    def get_target_id(self):
        """
        Returns primary node identifier of relationship target.

        Returns:
            str: target_id
        """
        return self.target_id

    def get_label(self):
        """
        Returns relationship label.

        Returns:
            str: relationship_label
        """
        return self.relationship_label

    def get_properties(self):
        """
        Returns all other relationship properties apart from primary ids
        and label as key-value pairs.

        Returns:
            dict: properties
        """
        return self.properties

    def get_dict(self):
        """
        Convert self to format accepted by Neo4j driver (Python dict ->
        Neo4j Map).

        Returns:
            dict: source_id, target_id and relationship_label as
                top-level key-value pairs, properties as second-level
                dict.
        """
        d = {}
        d.update(
            [
                ("source_id", self.source_id),
                ("target_id", self.target_id),
                ("relationship_label", self.relationship_label),
                ("properties", self.properties),
            ]
        )
        return d

    def create_relationship_list(relationships):
        """
        Create list of BioCypherEdge objects from dict of pypath
        relationships.

        Args:
            relationships: currently, a collection of pypath
                relationships. should be adapted to accept arbitrary
                collections.

        Todo:
            - account for all additional properties automatically
        """
        lst = []

        for edge in relationships:
            e = BioCypherEdge(
                # these are mandatory
                source_id=_process_id(edge.id_a),
                target_id=_process_id(edge.id_b),
                relationship_label=edge.type.upper(),
                # here are any additional properties
                directed=edge.directed,
                effect=edge.effect,
            )
            lst.append(e)

        return lst


def _process_id(identifier):
    """
    Replace critical symbols in pypath ids so that neo4j doesn't throw
    a type error.

    TODO remove
    """
    return str(identifier).replace("COMPLEX:", "COMPLEX_")
