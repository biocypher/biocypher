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

logger.debug(f"Loading module {__name__}.")

from typing import Union, Literal, Optional
import os

from linkml_runtime.linkml_model.meta import ClassDefinition
import bmt

from ._config import _read_yaml, module_data_path
from ._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode

__all__ = [
    "BiolinkAdapter",
    "gen_translate_edges",
    "gen_translate_nodes",
    "getpath",
]


class BiolinkAdapter:
    """
    Performs various functions to integrate the Biolink ontology.

    Todo:
        - refer to pythonised biolink model from YAML
    """

    def __init__(
        self,
        leaves: dict,
        schema: Optional[
            Union[
                Literal["biocypher", "biolink"],
                str,
                dict,
            ]
        ] = None,
    ):
        """
        Args:
            leaves:
                A dictionary representing the constituents of the graph
                to be built. These are the "leaves" of the ontology
                hierarchy tree.
            schema:
                Either a label referring to a built-in schema, or a path
                to a YAML file with the schema. If not provided, the default
                built-in schema will be used.
        """

        self.leaves = leaves
        self.schema = schema
        self.biolink_leaves = None

        logger.debug("Instantiating Biolink Adapter.")

        self.main()

    def main(self):
        # select with schema to use
        self.set_schema()
        # initialise biolink toolkit
        self.init_toolkit()
        # translate leaves
        self.translate_leaves_to_biolink()

    def set_schema(self):

        schemata_builtin = {
            "biocypher": "biocypher-biolink-model",
            "biolink": "biolink-model",
        }

        self.schema = self.schema or "biocypher"

        self.schema_name = (
            self.schema if isinstance(self.schema, str) else "custom"
        )

        if self.schema in schemata_builtin:

            label = schemata_builtin[self.schema]
            self.schema = module_data_path(label)

    def init_toolkit(self):
        """ """

        # TODO explain: isn't schma_yaml automatically at least
        # 'biocypher' after running set_schema? How would we get default?
        # - yes it is, we should default to biocypher, isn't it?
        logger.info(
            f"Creating BioLink model toolkit from `{self.schema_name}` model.",
        )

        self.toolkit = (
            bmt.Toolkit(self.schema) if self.schema else bmt.Toolkit()
        )

    def translate_leaves_to_biolink(self):
        """
        Translates the leaves (direct constituents of the graph) given
        in the `schema_config.yaml` to Biolink-conforming nomenclature.
        Simultaneously get the structure in the form of the parents of
        each leaf.

        Additionally adds child leaves for each leaf that has multiple
        identifiers.

        TODO: add class definition id_prefixes check
        """

        logger.info("Translating BioCypher config leaves to Biolink.")

        l = {}

        for entity in self.leaves.keys():

            e = self.toolkit.get_element(entity)  # element name

            # find element in bmt
            if e is not None:
                ancestors = trim_biolink_ancestry(
                    self.toolkit.get_ancestors(entity, formatted=True)
                )

                # check for signs of virtual leaves:
                # - nodes
                #   - multiple inputs and multiple identifiers
                # - edges
                #   - multiple inputs and multiple sources
                #   - multiple inputs and multiple targets?

                # TODO can there be virtual leaves without multiple
                # inputs?

                # TODO does it even play a role whether they are
                # represented as nodes vs edges?
                input_label = self.leaves[entity].get("label_in_input")

                # check for multiple inputs as well as multiple
                # identifiers or multiple sources: otherwise, no virtual
                # leaves necessary
                if isinstance(input_label, list):

                    # if entity is node
                    if self.leaves[entity]["represented_as"] == "node":

                        # if node is rel as node
                        if self.leaves[entity].get("source"):

                            # add child leaves for rel as node
                            if isinstance(
                                self.leaves[entity].get("source"), list
                            ):

                                # add child leaves for multiple sources
                                for source in self.leaves[entity]["source"]:
                                    name = source + "." + entity
                                    se = ClassDefinition(name)
                                    se.is_a = entity
                                    sancestors = list(ancestors)
                                    sancestors.insert(0, name)
                                    l[name] = {
                                        "class_definition": se,
                                        "ancestors": sancestors,
                                    }

                            elif isinstance(
                                self.leaves[entity].get("target"), list
                            ):
                                logger.error(
                                    "Multiple targets not implemented yet."
                                )

                        # "named thing" node (not rel as node)
                        elif isinstance(
                            self.leaves[entity].get("preferred_id"), list
                        ):
                            # add child leaves for node
                            for id in self.leaves[entity]["preferred_id"]:
                                name = id + "." + entity
                                se = ClassDefinition(name)
                                se.is_a = entity
                                sancestors = list(ancestors)
                                sancestors.insert(0, name)
                                l[name] = {
                                    "class_definition": se,
                                    "ancestors": sancestors,
                                }

                    # if entity is edge
                    else:
                        # add child leaves for edge
                        logger.error(
                            "Edge virtual leaves not implemented yet."
                        )

                # create dict of biolink class definition and biolink
                # ancestors
                l[entity] = {"class_definition": e, "ancestors": ancestors}
            else:
                if "virtual" in self.leaves[entity].keys():
                    logger.info(
                        f"{entity} is a virtual leaf, but not in the "
                        f"Biolink model. Skipping."
                    )
                elif "is_a" in self.leaves[entity].keys():
                    parent = self.leaves[entity]["is_a"]
                    if isinstance(parent, list):
                        logger.info(
                            f"Received ad hoc multiple inheritance information; "
                            f"updating pseudo-Biolink entry by setting {entity} "
                            f"as a child of {parent}."
                        )
                        # assume biolink entity is last in list
                        bl_parent = parent.pop()
                        ancestors = trim_biolink_ancestry(
                            self.toolkit.get_ancestors(
                                bl_parent, formatted=True
                            )
                        )
                        while parent:
                            # create class definitions for all ancestors
                            # in reverse order
                            child = parent.pop()
                            se = ClassDefinition(child)
                            se.is_a = parent
                            ancestors = list(ancestors)
                            ancestors.insert(0, child)
                            l[child] = {
                                "class_definition": se,
                                "ancestors": ancestors,
                            }

                        # finally top-level class definition
                        se = ClassDefinition(entity)
                        se.is_a = parent
                        ancestors = list(ancestors)
                        ancestors.insert(0, entity)
                        l[entity] = {
                            "class_definition": se,
                            "ancestors": ancestors,
                        }

                    else:
                        logger.info(
                            f"Received ad hoc inheritance information; "
                            f"updating pseudo-Biolink entry by setting {entity} "
                            f"as a child of {parent}."
                        )
                        ancestors = trim_biolink_ancestry(
                            self.toolkit.get_ancestors(parent, formatted=True)
                        )
                        se = ClassDefinition(entity)
                        se.is_a = parent
                        sancestors = list(ancestors)
                        sancestors.insert(0, entity)
                        l[entity] = {
                            "class_definition": se,
                            "ancestors": sancestors,
                        }
                else:
                    logger.warning("Entity not found in Biolink: " + entity)
                    l[entity] = None

        self.biolink_leaves = l


def trim_biolink_ancestry(ancestry: list):
    """
    Trims "biolink:" prefix from Biolink ancestry elements.
    """

    # replace 'biolink:' with ''
    return [a.replace("biolink:", "") for a in ancestry]


"""
Biolink toolkit wiki:
https://biolink.github.io/biolink-model-toolkit/example_usage.html
"""

# -------------------------------------------
# Create nodes and edges from separate inputs
# -------------------------------------------


def gen_translate_nodes(leaves, id_type_prop_tuples):
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
    if isinstance(id_type_prop_tuples, list):
        logger.debug(
            f"Translating {len(id_type_prop_tuples)} nodes to BioCypher."
        )
    else:
        logger.debug(f"Translating nodes to BioCypher from generator.")

    for _id, _type, _props in id_type_prop_tuples:
        # find the node in leaves that represents biolink node type
        _bl_type = _get_bl_type(leaves, _type)

        if _bl_type is not None:
            # filter properties for those specified in schema_config if any
            _filtered_props = _filter_props(leaves, _bl_type, _props)

            # preferred id
            _preferred_id = _get_preferred_id(leaves, _bl_type)

            yield BioCypherNode(
                node_id=_id,
                node_label=_bl_type,
                preferred_id=_preferred_id,
                properties=_filtered_props,
            )

        else:
            logger.warning("No Biolink equivalent found for type " + _type)


def _get_preferred_id(leaves, _bl_type):
    """
    Returns the preferred id for the given Biolink type.
    """

    if _bl_type in leaves.keys():
        if "preferred_id" in leaves[_bl_type].keys():
            return leaves[_bl_type]["preferred_id"]
        else:
            return "id"
    else:
        return "id"


def _filter_props(leaves: dict, bl_type: str, props: dict):
    """
    Filters properties for those specified in schema_config if any.
    """
    filter_props = leaves[bl_type].get("properties")
    if filter_props:
        filtered_props = {
            k: v for k, v in props.items() if k in filter_props.keys()
        }
        missing_props = [
            k for k in filter_props.keys() if k not in filtered_props.keys()
        ]
        if missing_props:
            # add missing properties with default values
            for k in missing_props:
                filtered_props[k] = None
        return filtered_props
    else:
        return props


def gen_translate_edges(leaves, src_tar_type_prop_tuples):
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

    if isinstance(src_tar_type_prop_tuples, list):
        logger.debug(
            f"Translating {len(src_tar_type_prop_tuples)} edges to BioCypher.",
        )
    else:
        logger.debug(f"Translating edges to BioCypher from generator.")

    for _src, _tar, _type, _props in src_tar_type_prop_tuples:
        # match the input label (_type) to a Biolink label from schema_config
        bl_type = _get_bl_type(leaves, _type)

        if bl_type is not None:
            # filter properties for those specified in schema_config if any
            _filtered_props = _filter_props(leaves, bl_type, _props)

            rep = leaves[bl_type]["represented_as"]

            if rep == "node":
                node_id = (
                    str(_src)
                    + "_"
                    + str(_tar)
                    + "_"
                    + "_".join(str(v) for v in _filtered_props.values())
                )
                n = BioCypherNode(
                    node_id=node_id,
                    node_label=bl_type,
                    properties=_filtered_props,
                )
                # directionality check TODO generalise to account for
                # different descriptions of directionality or find a
                # more consistent solution for indicating directionality
                if _filtered_props.get("directed") == True:
                    l1 = "IS_SOURCE_OF"
                    l2 = "IS_TARGET_OF"
                else:
                    l1 = l2 = "IS_PART_OF"
                e_s = BioCypherEdge(
                    source_id=_src,
                    target_id=node_id,
                    relationship_label=l1,
                    # additional here
                )
                e_t = BioCypherEdge(
                    source_id=_tar,
                    target_id=node_id,
                    relationship_label=l2,
                    # additional here
                )
                yield BioCypherRelAsNode(n, e_s, e_t)

            else:
                edge_label = leaves[bl_type].get("label_as_edge")
                if edge_label is None:
                    edge_label = bl_type
                yield BioCypherEdge(
                    source_id=_src,
                    target_id=_tar,
                    relationship_label=edge_label,
                    properties=_filtered_props,
                )

        else:
            logger.warning("No Biolink equivalent found for type " + _type)


def _get_bl_type(dict, value):
    """
    For each given input type ("label_in_input"), find the corresponding
    Biolink type in the leaves dictionary.

    Args:
        dict: the dict to search (leaves from `schema_config.yaml`)
        value: the input type to find (`label_in_input` in `schema_config.yaml`)
    """
    for k, v in dict.items():
        if "label_in_input" in v:
            l = v["label_in_input"]
            if isinstance(l, list):
                if value in l:
                    return k
            elif v["label_in_input"] == value:
                return k
