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
Lookup and storage of entity IDs that are part of the BioCypher schema.

Todo:

    - genericise: standardise input data to BioCypher specifications or,
      optionally, user specifications.

        - if the database exists, read biocypher info node
        - if newly created, ask for user input (?) as to which IDs to
          use etc
        - default scenario -> YAML?
        - the consensus representation ("target" of translation) is
          the literal Biolink class, which is assigned to database
          content using user input for each class to be represented
          in the graph ("source" of translation). currently,
          implemented by assigning source nomenclature explicitly in
          the schema_config.yaml file ("label_in_input").

    - type checking
    - import ID types from pypath dictionary (later, externalised
      dictionary)? biolink?
"""

from ._logger import logger

logger.debug(f'Loading module {__name__}.')

from typing import Union, Literal, Optional
import os

import bmt

from ._config import _read_yaml, module_data_path
from ._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode

__all__ = ['BiolinkAdapter', 'gen_translate_edges', 'gen_translate_nodes', 'getpath']


class BiolinkAdapter:
    """
    Performs various functions to integrate the Biolink ontology.

    Todo:
        - refer to pythonised biolink model from YAML
    """

    def __init__(
        self,
        leaves,
        schema: Optional[
            Union[
                Literal['biocypher', 'biolink'],
                str,
                dict,
            ]
        ] = None,
    ):
        """
        Args:
            leaves:
                I don't know.
            schema:
                Either a label referring to a built-in schema, or a path
                to a YAML file with the schema. If not provided, the default
                built-in schema will be used.
        """

        self.leaves = leaves
        self.schema = schema

        logger.debug('Instantiating Biolink Adapter.')

        self.main()


    def main(self):

        self.set_schema()
        self.init_toolkit()
        self.translate()


    def set_schema(self):

        schemata_builtin = {
            'biocypher': 'biocypher-biolink-model',
            'biolink': 'biolink-model',
        }

        self.schema = self.schema or 'biocypher'

        self.schema_name = (
            self.schema
                if isinstance(self.schema, str) else
            'custom'
        )

        if self.schema in schemata_builtin:

            label = schemata_builtin[self.schema]
            self.schema = module_data_path(label)


    def init_toolkit(self):
        """
        """

        # TODO explain: isn't schma_yaml automatically at least
        # 'biocypher' after running set_schema? How would we get default?
        # - yes it is, we should default to biocypher, isn't it?
        logger.info(
            f'Creating BioLink model toolkit from `{self.schema_name}` model.',
        )

        self.toolkit = (
            bmt.Toolkit(self.schema)
                if self.schema else
            bmt.Toolkit()
        )


    def translate(self):
        """
        Translates the leaves (direct constituents of the graph) given
        in the `schema_config.yaml` to Biolink-conforming nomenclature.
        Simultaneously get the structure in the form of the parents of
        each leaf.
        """

        logger.info('Translating BioCypher config leaves to Biolink.')

        l = {}

        for entity in self.leaves.keys():

            e = self.toolkit.get_element(entity)  # element name

            # find element in bmt
            if e is not None:

                # create dict of biolink class definition and biolink
                # ancestors
                ancestors = self.toolkit.get_ancestors(entity, formatted=True)
                l[entity] = {'class_definition': e, 'ancestors': ancestors}

            else:

                logger.info('Entity not found:' + entity[0])
                l[entity] = None

        self.biolink = l


"""
Biolink toolkit wiki:
https://biolink.github.io/biolink-model-toolkit/example_usage.html
"""

# -------------------------------------------
# Create nodes and edges from separate inputs
# -------------------------------------------


def gen_translate_nodes(leaves, id_type_tuples):
    """
    Translates input node representation to a representation that
    conforms to the schema of the given BioCypher graph. For now
    requires explicit statement of node type on pass.

    Args:
        leaves (dict): dictionary detailing the leaves of the hierarchy
            tree representing the structure of the graph; the leaves are
            the entities that will be direct components of the graph,
            while the intermediary nodes are additional labels for
            filtering purposes.
        id_type_tuples (list of tuples): collection of tuples
            representing individual nodes by their unique id and a type
            that is translated from the original database notation to
            the corresponding BioCypher notation.

    """

    # biolink = BiolinkAdapter(leaves)
    if isinstance(id_type_tuples, list):
        logger.info(f'Translating {len(id_type_tuples)} nodes to BioCypher.')
    else:
        logger.info(f'Translating nodes to BioCypher from generator.')

    for id, type, props in id_type_tuples:
        path = getpath(leaves, type)

        if path is not None:
            bl_type = path[0]
            yield BioCypherNode(node_id=id, node_label=bl_type, **props)

        else:
            print('No path for type ' + type)


def gen_translate_edges(leaves, src_tar_type_tuples):
    """
    Translates input edge representation to a representation that
    conforms to the schema of the given BioCypher graph. For now
    requires explicit statement of edge type on pass.

    Args:
        leaves (dict): dictionary detailing the leaves of the hierarchy
            tree representing the structure of the graph; the leaves are
            the entities that will be direct components of the graph,
            while the intermediary nodes are additional labels for
            filtering purposes.
        src_tar_type_tuples (list of tuples): collection of tuples
            representing source and target of an interaction via their
            unique ids as well as the type of interaction in the
            original database notation, which is translated to BioCypher
            notation using the `leaves`.

    Todo:
        - id of interactions (now simple concat with "_")
            - do we even need one?
    """

    if isinstance(src_tar_type_tuples, list):
        logger.info(
            f'Translating {len(src_tar_type_tuples)} edges to BioCypher.',
        )
    else:
        logger.info(f'Translating edges to BioCypher from generator.')

    for src, tar, type, props in src_tar_type_tuples:
        path = getpath(leaves, type)

        if path is not None:
            bl_type = path[0]
            rep = leaves[bl_type]['represented_as']

            if rep == 'node':
                node_id = (
                    str(src)
                    + '_'
                    + str(tar)
                    + '_'
                    + '_'.join(str(v) for v in props.values())
                )
                n = BioCypherNode(node_id=node_id, node_label=bl_type, **props)
                # directionality check
                if props.get('directed') == True:
                    l1 = 'IS_SOURCE_OF'
                    l2 = 'IS_TARGET_OF'
                else:
                    l1 = l2 = 'IS_PART_OF'
                e_s = BioCypherEdge(
                    source_id=src,
                    target_id=node_id,
                    relationship_label=l1,
                    # additional here
                )
                e_t = BioCypherEdge(
                    source_id=tar,
                    target_id=node_id,
                    relationship_label=l2,
                    # additional here
                )
                yield BioCypherRelAsNode(n, e_s, e_t)

            else:
                edge_label = leaves[bl_type]['label_as_edge']
                yield BioCypherEdge(
                    source_id=src,
                    target_id=tar,
                    relationship_label=edge_label,
                    **props,
                )

        else:
            print('No path for type ' + type)


def getpath(nested_dict, value, prepath=()):
    """
    Get specific value from unknown location in a nested dict.

    Args:
        nested_dict (dict): the dict to search
        value: the dictionary value to find
    """
    for k, v in nested_dict.items():
        path = prepath + (k,)
        if v == value:  # found value
            return path
        elif hasattr(v, 'items'):  # v is a dict
            p = getpath(v, value, path)  # recursive call
            if p is not None:
                return p
