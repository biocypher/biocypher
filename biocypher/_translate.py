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

    - type checking: use biolink classes for typing directly?
    
    - import ID types from pypath dictionary (later, externalised
      dictionary)? biolink?
"""

from ._logger import logger

logger.debug(f"Loading module {__name__}.")

from typing import Any, Generator, Iterable, Literal, Optional, Union
import os
import re

from linkml_runtime.linkml_model.meta import ClassDefinition
import bmt

from ._config import _read_yaml, module_data_path
from ._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode
from . import _misc

__all__ = [
    "BiolinkAdapter",
    "Translator",
    "getpath",
]


class BiolinkAdapter:
    """
    Performs various functions to integrate the Biolink ontology.

    Stores schema mappings to allow (reverse) translation of terms and
    queries.

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
        self.schema_name = None
        self.biolink_leaves = None

        # mapping functionality for translating terms and queries
        self.mappings = {}
        self.reverse_mappings = {}

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
                ancestors = self.trim_biolink_ancestry(
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
                                # input label to identifier is one to one
                                for label, source in zip(
                                    input_label, self.leaves[entity]["source"]
                                ):
                                    name = source + "." + entity
                                    se = ClassDefinition(name)
                                    se.is_a = entity
                                    sancestors = list(ancestors)
                                    sancestors.insert(0, name)
                                    l[name] = {
                                        "class_definition": se,
                                        "ancestors": sancestors,
                                    }

                                    # add translation mappings
                                    self._add_translation_mappings(label, name)

                            elif isinstance(
                                self.leaves[entity].get("target"), list
                            ):
                                logger.error(
                                    "Multiple targets not implemented yet."
                                )

                        # "named thing" node (not rel as node)
                        # input label to identifier is one to one
                        elif isinstance(
                            self.leaves[entity].get("preferred_id"), list
                        ):
                            # add child leaves for node
                            for label, id in zip(
                                input_label,
                                self.leaves[entity]["preferred_id"],
                            ):
                                name = id + "." + entity
                                se = ClassDefinition(name)
                                se.is_a = entity
                                sancestors = list(ancestors)
                                sancestors.insert(0, name)
                                l[name] = {
                                    "class_definition": se,
                                    "ancestors": sancestors,
                                }

                                # add translation mappings
                                self.mappings[label] = name
                                self.reverse_mappings[name] = label

                        # just multiple input labels
                        # input label to identifier is many to one
                        else:
                            for label in input_label:
                                # add translation mappings
                                self.mappings[label] = entity

                            self.reverse_mappings[entity] = input_label

                    # if entity is edge
                    else:
                        # add child leaves for edge
                        if isinstance(self.leaves[entity].get("source"), list):

                            # add child leaves for multiple sources
                            # input label to identifier is one to one
                            for label, source in zip(
                                input_label, self.leaves[entity]["source"]
                            ):
                                name = source + "." + entity
                                se = ClassDefinition(name)
                                se.is_a = entity
                                sancestors = list(ancestors)
                                sancestors.insert(0, name)
                                l[name] = {
                                    "class_definition": se,
                                    "ancestors": sancestors,
                                }

                                # add translation mappings
                                self._add_translation_mappings(label, name)

                        elif isinstance(
                            self.leaves[entity].get("target"), list
                        ):
                            logger.error(
                                "Multiple targets not implemented yet."
                            )

                        else:
                            # simple multiple inputs
                            # input label to identifier is many to one
                            for label in input_label:
                                # add translation mappings
                                self.mappings[label] = self.leaves[entity].get(
                                    "label_as_edge", entity
                                )
                            self.reverse_mappings[
                                self.leaves[entity].get(
                                    "label_as_edge", entity
                                )
                            ] = input_label

                else:
                    # add translation mappings
                    self._add_translation_mappings(
                        input_label,
                        self.leaves[entity].get("label_as_edge", entity),
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

                    # add translation mappings
                    if isinstance(
                        self.leaves[entity].get("label_in_input"), list
                    ):
                        for label in self.leaves[entity]["label_in_input"]:
                            self._add_translation_mappings(
                                label,
                                self.leaves[entity].get(
                                    "label_as_edge", entity
                                ),
                            )
                    else:
                        self._add_translation_mappings(
                            self.leaves[entity].get("label_in_input"),
                            self.leaves[entity].get("label_as_edge", entity),
                        )
                elif "is_a" in self.leaves[entity].keys():
                    parent = self.leaves[entity]["is_a"]
                    if isinstance(parent, list):
                        logger.info(
                            "Received ad hoc multiple inheritance "
                            "information; updating pseudo-Biolink entry "
                            f"by setting {entity} as a child of {parent}."
                        )
                        # assume biolink entity is last in list
                        bl_parent = parent.pop()
                        ancestors = self.trim_biolink_ancestry(
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
                            "Received ad hoc inheritance information; "
                            "updating pseudo-Biolink entry by setting "
                            f"{entity} as a child of {parent}."
                        )
                        ancestors = self.trim_biolink_ancestry(
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

    def translate_term(self, term):
        """
        Translate a single term.
        """

        return self.mappings.get(term, None)

    def reverse_translate_term(self, term):
        """
        Reverse translate a single term.
        """

        return self.reverse_mappings.get(term, None)

    def translate(self, query):
        """
        Translate a cypher query. Only translates labels as of now.
        """
        for key in self.mappings:
            query = query.replace(":" + key, ":" + self.mappings[key])
        return query

    def reverse_translate(self, query):
        """
        Reverse translate a cypher query. Only translates labels as of
        now.
        """
        for key in self.reverse_mappings:
            if ":" + key in query:
                if isinstance(self.reverse_mappings[key], list):
                    raise NotImplementedError(
                        "Reverse translation of multiple inputs not "
                        "implemented yet. Many-to-one mappings are "
                        "not reversible. "
                        f"({key} -> {self.reverse_mappings[key]})"
                    )
                else:
                    query = query.replace(
                        ":" + key, ":" + self.reverse_mappings[key]
                    )
        return query

    def _add_translation_mappings(self, original_name, biocypher_name):
        """
        Add translation mappings for a label and name.
        """
        self.mappings[original_name] = biocypher_name
        self.reverse_mappings[biocypher_name] = original_name


    @staticmethod
    def trim_biolink_ancestry(ancestry: list[str]) -> list[str]:
        """
        Trims "biolink:" prefix from Biolink ancestry elements.
        """

        # replace 'biolink:' with ''
        return [re.sub("^biolink:", "", a) for a in ancestry]


"""
Biolink toolkit wiki:
https://biolink.github.io/biolink-model-toolkit/example_usage.html
"""


# -------------------------------------------
# Create nodes and edges from separate inputs
# -------------------------------------------

class Translator:

    def __init__(self, leaves: dict[str, dict]):
        """
        Args:
            leaves:
                Dictionary detailing the leaves of the hierarchy
                tree representing the structure of the graph; the leaves are
                the entities that will be direct components of the graph,
                while the intermediary nodes are additional labels for
                filtering purposes.
        """

        self.leaves = leaves
        self._update_bl_types()


    def translate_nodes(
            self,
            id_type_prop_tuples: Iterable,
        ) -> Generator[BioCypherNode, None, None]:
        """
        Translates input node representation to a representation that
        conforms to the schema of the given BioCypher graph. For now
        requires explicit statement of node type on pass.

        Args:
            id_type_tuples (list of tuples): collection of tuples
                representing individual nodes by their unique id and a type
                that is translated from the original database notation to
                the corresponding BioCypher notation.

        """

        self._log_begin_translate(id_type_prop_tuples, "nodes")

        for _id, _type, _props in id_type_prop_tuples:

            # find the node in leaves that represents biolink node type
            _bl_type = self._get_bl_type(_type)

            if _bl_type:

                # filter properties for those specified in schema_config if any
                _filtered_props = self._filter_props(_bl_type, _props)

                # preferred id
                _preferred_id = self._get_preferred_id(_bl_type)

                yield BioCypherNode(
                    node_id=_id,
                    node_label=_bl_type,
                    preferred_id=_preferred_id,
                    properties=_filtered_props,
                )

            else:

                self._error_no_type(_type)

        self._log_finish_translate("nodes")


    def _get_preferred_id(self, _bl_type: str) -> str:
        """
        Returns the preferred id for the given Biolink type.
        """

        return (
            self.leaves[_bl_type]["preferred_id"]
                if "preferred_id" in self.leaves.get(_bl_type, {}) else
            "id"
        )


    def _filter_props(self, bl_type: str, props: dict) -> dict:
        """
        Filters properties for those specified in schema_config if any.
        """

        filter_props = self.leaves[bl_type].get("properties", None)

        if filter_props:

            filtered_props = {
                k: v
                for k, v in props.items()
                if k in filter_props.keys()
            }

            missing_props = [
                k
                for k in filter_props.keys()
                if k not in filtered_props.keys()
            ]

            # add missing properties with default values
            for k in missing_props:

                filtered_props[k] = None

            return filtered_props

        else:

            return props


    def translate_edges(
            self,
            src_tar_type_prop_tuples: Iterable,
        ) -> Generator[Union[BioCypherEdge, BioCypherRelAsNode], None, None]:
        """
        Translates input edge representation to a representation that
        conforms to the schema of the given BioCypher graph. For now
        requires explicit statement of edge type on pass.

        Args:
            src_tar_type_tuples (list of tuples): collection of tuples
                representing source and target of an interaction via their
                unique ids as well as the type of interaction in the
                original database notation, which is translated to BioCypher
                notation using the `leaves`.
        """
        # TODO:
        #    - id of interactions (now simple concat with "_")
        #    - do we even need one?

        self._log_begin_translate(src_tar_type_prop_tuples, "edges")

        for _src, _tar, _type, _props in src_tar_type_prop_tuples:

            # match the input label (_type) to
            # a Biolink label from schema_config
            bl_type = self._get_bl_type(_type)

            if bl_type:

                # filter properties for those specified in schema_config if any
                _filtered_props = _filter_props(bl_type, _props)

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

                    edge_label = self.leaves[bl_type].get("label_as_edge")

                    if edge_label is None:

                        edge_label = bl_type

                    yield BioCypherEdge(
                        source_id=_src,
                        target_id=_tar,
                        relationship_label=edge_label,
                        properties=_filtered_props,
                    )

            else:

                self._error_no_type(_type)

        self._log_finish_translate("edges")


    @staticmethod
    def _error_no_type(_type: Any):

        msg = f"No Biolink type defined for `{_type}`."
        logger.error(msg)

        raise ValueError(msg)


    @staticmethod
    def _log_begin_translate(_input: Iterable, what: str):

        n = f"{len(_input)} " if hasattr(_input, '__len__') else ""

        logger.debug(f"Translating {n}{what} to BioCypher")


    @staticmethod
    def _log_finish_translate(what: str):

        logger.debug(f"Finished translating {what} to BioCypher.")


    def _update_bl_types(self):

        self._bl_types = dict(
            (label, bcy_type)
            for bcy_type, schema_def in self.leaves.items()
            for label in _misc.to_list(schema_def.get("label_in_input", ()))
        )


    def _get_bl_type(self, label: str) -> Optional[str]:
        """
        For each given input type ("label_in_input"), find the corresponding
        Biolink type in the leaves dictionary.

        Args:
            label:
                The input type to find (`label_in_input` in
                `schema_config.yaml`).
        """

        return self._bl_types.get(label, None)
