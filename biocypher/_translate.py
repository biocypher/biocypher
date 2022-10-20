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
from collections.abc import Iterable, Generator

from ._logger import logger

logger.debug(f'Loading module {__name__}.')

from typing import Any, Union, Literal, Optional
import os
import re
import collections

from bmt.utils import sentencecase_to_camelcase
from more_itertools import peekable
from linkml_runtime.linkml_model.meta import ClassDefinition
import bmt

from . import _misc
from ._config import _read_yaml, module_data_path
from ._create import BC_TYPES, BioCypherEdge, BioCypherNode, BioCypherRelAsNode

__all__ = ['BiolinkAdapter', 'Translator']


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
                Literal['biocypher', 'biolink'],
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

        logger.debug('Instantiating Biolink Adapter.')

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
            'biocypher': 'biocypher-biolink-model',
            'biolink': 'biolink-model',
        }

        self.schema = self.schema or 'biocypher'

        self.schema_name = (
            self.schema if isinstance(self.schema, str) else 'custom'
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
            f'Creating BioLink model toolkit from `{self.schema_name}` model.',
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

        TODO: where do we use sentence case, which is the
        official internal biolink representation, and where do
        we switch to pascal case?
        """

        logger.info('Translating BioCypher config leaves to Biolink.')

        self.biolink_leaves = {}

        # ontology parents first
        for entity, values in self.leaves.items():

            entity_biolink_class = self.toolkit.get_element(
                entity,
            )  # element name

            if entity_biolink_class:

                # find ancestors of biolink type in PascalCase
                ancestors = self.trim_biolink_ancestry(
                    self.toolkit.get_ancestors(entity, formatted=True),
                )

                input_label = values.get('label_in_input')

                # add translation mappings
                bc_name = (
                    values.get('label_as_edge')
                    if values.get('label_as_edge')
                    else entity
                )
                self._add_translation_mappings(input_label, bc_name)

                # create dict of biolink class definition and biolink
                # ancestors, add to biolink leaves
                self.biolink_leaves[entity] = {
                    'class_definition': entity_biolink_class,
                    'ancestors': ancestors,
                }

        # secondly check explicit children
        for entity, values in self.leaves.items():

            if values.get('is_a') and not values.get('virtual'):

                # build class definition for explicit child
                self._build_biolink_class(entity, values)

        # lastly check virtual leaves (implicit children)
        for entity, values in self.leaves.items():

            if values.get('virtual'):

                # build class definition for virtual leaf
                self._build_biolink_class(entity, values)

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
            query = query.replace(':' + key, ':' + self.mappings[key])
        return query

    def reverse_translate(self, query):
        """
        Reverse translate a cypher query. Only translates labels as of
        now.
        """
        for key in self.reverse_mappings:

            a = ':' + key + ')'
            b = ':' + key + ']'
            # TODO this conditional probably does not cover all cases
            if a in query or b in query:
                if isinstance(self.reverse_mappings[key], list):
                    raise NotImplementedError(
                        'Reverse translation of multiple inputs not '
                        'implemented yet. Many-to-one mappings are '
                        'not reversible. '
                        f'({key} -> {self.reverse_mappings[key]})',
                    )
                else:
                    query = query.replace(
                        a, ':' + self.reverse_mappings[key] + ')',
                    ).replace(b, ':' + self.reverse_mappings[key] + ']')
        return query

    def _add_translation_mappings(self, original_name, biocypher_name):
        """
        Add translation mappings for a label and name. We use here the
        PascalCase version of the BioCypher name, since sentence case is
        not useful for Cypher queries.
        """
        if isinstance(original_name, list):
            for on in original_name:
                self.mappings[on] = self.name_sentence_to_pascal(
                    biocypher_name,
                )
        else:
            self.mappings[original_name] = self.name_sentence_to_pascal(
                biocypher_name,
            )

        if isinstance(biocypher_name, list):
            for bn in biocypher_name:
                self.reverse_mappings[
                    self.name_sentence_to_pascal(bn)
                ] = original_name
        else:
            self.reverse_mappings[
                self.name_sentence_to_pascal(biocypher_name)
            ] = original_name

    def _build_biolink_class(self, entity, values):
        """
        Build a Biolink class definition from a Biolink entity name and
        property dict.
        """
        if values.get('represented_as') == 'node':
            return self._build_biolink_node_class(entity, values)
        else:
            return self._build_biolink_edge_class(entity, values)

    def _build_biolink_node_class(self, entity: str, values: dict) -> None:
        """
        Build a Biolink node class definition from a Biolink entity name
        and property dict.
        """

        input_label = values.get('label_in_input')
        parents = _misc.to_list(values.get('is_a'))
        ancestors = []

        logger.info(
            'Received ad hoc multiple inheritance '
            'information; updating pseudo-Biolink node '
            f'by setting `{entity}` as a child of `{parents[0]}`.',
        )

        while parents:
            parent = parents.pop(0)
            if self.biolink_leaves.get(parent):
                ancestors += self.biolink_leaves.get(parent).get('ancestors')
                break
            elif self.toolkit.get_ancestors(parent):
                bla = _misc.to_list(
                    self.trim_biolink_ancestry(
                        self.toolkit.get_ancestors(parent, formatted=True),
                    ),
                )
                ancestors += bla
                break
            else:
                ancestors += [self.name_sentence_to_pascal(parent)]

        if ancestors:
            ancestors.insert(0, self.name_sentence_to_pascal(entity))
        else:
            raise ValueError(
                f'Parent `{parent}` of `{entity}` not found in Biolink '
                'model.',
            )

        # create class definition
        se = ClassDefinition(entity)
        se.is_a = parent
        self.biolink_leaves[entity] = {
            'class_definition': se,
            'ancestors': ancestors,
        }

        # add translation mappings
        self._add_translation_mappings(input_label, entity)

    def _build_biolink_edge_class(self, entity: str, values: dict) -> None:
        """
        Build a Biolink edge class definition from a Biolink entity name
        and property dict.
        """

        input_label = values.get('label_in_input')
        parents = _misc.to_list(values.get('is_a'))
        ancestors = []

        logger.info(
            'Received ad hoc multiple inheritance '
            'information; updating pseudo-Biolink edge '
            f'by setting `{entity}` as a child of `{parents[0]}`.',
        )

        while parents:
            parent = parents.pop(0)
            if self.biolink_leaves.get(parent):
                ancestors += self.biolink_leaves.get(parent).get('ancestors')
                break
            elif self.toolkit.get_ancestors(parent):
                bla = _misc.to_list(
                    self.trim_biolink_ancestry(
                        self.toolkit.get_ancestors(parent, formatted=True),
                    ),
                )
                ancestors += bla
                break
            else:
                ancestors += [self.name_sentence_to_pascal(parent)]

        if ancestors:
            ancestors.insert(0, self.name_sentence_to_pascal(entity))
        else:
            raise ValueError(
                f'Parent `{parent}` of `{entity}` not found in Biolink '
                'model.',
            )

        # create class definition
        se = ClassDefinition(entity)
        se.is_a = parent
        self.biolink_leaves[entity] = {
            'class_definition': se,
            'ancestors': ancestors,
        }

        # add translation mappings
        bc_name = (
            values.get('label_as_edge')
            if values.get('label_as_edge')
            else entity
        )
        self._add_translation_mappings(input_label, bc_name)

    @staticmethod
    def trim_biolink_ancestry(ancestry: list[str]) -> list[str]:
        """
        Trims "biolink:" prefix from Biolink ancestry elements.
        """

        # replace 'biolink:' with ''
        return [re.sub('^biolink:', '', a) for a in ancestry]

    @staticmethod
    def name_sentence_to_pascal(name: str) -> str:
        """
        Converts a name in sentence case to pascal case.
        """
        # split on dots if dot is present
        if '.' in name:
            return '.'.join(
                [sentencecase_to_camelcase(n) for n in name.split('.')],
            )
        else:
            return sentencecase_to_camelcase(name)


"""
Biolink toolkit wiki:
https://biolink.github.io/biolink-model-toolkit/example_usage.html
"""


# -------------------------------------------
# Create nodes and edges from separate inputs
# -------------------------------------------


class Translator:

    INPUT_TYPES = (
        tuple[str, str, dict] |
        tuple[str, str, str, dict] |
        tuple[str, str, str, str, dict]
    )

    def __init__(self, leaves: dict[str, dict]):
        """
        Translate components to their biocypher representations.

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

        # record nodes without biolink type configured in schema_config.yaml
        self.notype = collections.defaultdict(int)

    def translate(
            self,
            items: INPUT_TYPES | Iterable[INTPUT_TYPES]
        ) -> Generator[BC_TYPES, None, None]:
        """
        Translate graph components to the current schema.

        Translates input node representation to a representation that
        conforms to the schema of the given BioCypher graph. For now
        requires explicit statement of node type on pass.

        Args:
            items:
                Tuples representing graph components.

        Yields:
            Graph components as objects that are suitable to be inserted
            into the database.
        """

        self._log_begin_translate(items, 'components')

        items = peekable(items)
        first = items.peek()

        if isinstance(first, _misc.SIMPLE_TYPES):

            items = (first,)

        for i in items:

            bc_i = (
                self.node(*i)
                    if len(i) < 4 else
                self.edge(*i)
                    if len(i) == 4 else
                self.edge(*i[1:], _id = i[0])
            )

            if bc_i: yield bc_i

        self._log_finish_translate('components')

    def edge(
            self,
            source: str,
            target: str,
            _type: str,
            props: dict,
            _id: str = None,
        ) -> BioCypherEdge | BioCypherRelAsNode | None:
        """
        Creates one BioCypherEdge.

        Args:
            source:
                ID of the source node.
            target:
                ID of the target node.
            _type:
                Type of the entity represented by the edge.
            props:
                Arbitrary properties.
            _id:
                ID property of the edge. If not provided, the source,
                target, type and all properties will be concatenated to
                create a unique ID for the edge. Used only if the relation
                is represented as a node.

        Returns:
            An edge in BioCypher representation, if the entity type can be
            found in the schema.
        """

        # match the input label (_type) to
        # a Biolink label from schema_config
        bl_type = self._get_bl_type(_type)

        if not bl_type:

            self._record_no_type(_type, (source, target))

        else:

            filtered_props = self._filter_props(bl_type, props)
            rep = self.leaves[bl_type]['represented_as']

            if rep == 'node':

                return self._rel_as_node(
                    source = source,
                    target = target,
                    bl_type = bl_type,
                    _id = _id,
                    props = filtered_props,
                )

            edge_label = self.leaves[bl_type].get('label_as_edge') or bl_type

            return BioCypherEdge(
                source_id = source,
                target_id = target,
                relationship_label = edge_label,
                properties = filtered_props,
            )

    def _rel_as_node(
            self,
            source: str,
            target: str,
            bl_type: str,
            props: dict,
            _id: str | None = None,
        ) -> BioCypherRelAsNode:
        """
        Create node representation of a record represented by edge by default.

        Args:
            source:
                ID of the source node.
            target:
                ID of the target node.
            bl_type:
                The Biolink type to be used as node label.
            props:
                Arbitrary properties, already filtered by ``_filter_props``.
            _id:
                ID property of the node. If not provided, the source,
                target, type and all properties will be concatenated to
                create a unique ID for the edge.

        Returns:
            A triplet of one node and two edges in BioCypher representation.
        """

        if _id:
            # if it brings its own ID, use it
            node_id = _id

        else:

            props_str = _misc.dict_str(dct = props, sep = '_')
            # source target concat
            node_id = f'{src}_{tar}_{props_str}'

        n = BioCypherNode(
            node_id = node_id,
            node_label = bl_type,
            properties = props,
        )

        # directionality check TODO generalise to account for
        # different descriptions of directionality or find a
        # more consistent solution for indicating directionality
        if props.get('directed'):

            reltype1 = 'IS_SOURCE_OF'
            reltype2 = 'IS_TARGET_OF'

        else:

            reltype1 = props.get('src_role') or 'IS_PART_OF'
            reltype2 = props.get('tar_role') or 'IS_PART_OF'

        e_s = BioCypherEdge(
            source_id = source,
            target_id = node_id,
            relationship_label = reltype1,
        )

        e_t = BioCypherEdge(
            source_id = target,
            target_id = node_id,
            relationship_label = reltype2,
        )

        yield BioCypherRelAsNode(n, e_s, e_t)


    def node(
            self,
            _id: str,
            _type: str,
            props: dict,
        ) -> BioCypherNode | None:
        """
        Creates one BioCypherNode.

        Args:
            _id:
                The node ID.
            _type:
                Type of the represented entity.
            props:
                Arbitrary properties.

        Returns:
            A node in BioCypher representation, if the entity type can be
            found in the schema.
        """

        # find the node in leaves that represents biolink node type
        bl_type = self._get_bl_type(_type)

        if not bl_type:

            self._record_no_type(_type, _id)

        else:

            # filter properties for those specified in schema_config if any
            filtered_props = self._filter_props(bl_type, props)
            preferred_id = self._get_preferred_id(bl_type)

            return BioCypherNode(
                node_id = _id,
                node_label = bl_type,
                preferred_id = preferred_id,
                properties = filtered_props,
            )


    def _get_preferred_id(self, _bl_type: str) -> str:
        """
        Returns the preferred id for the given Biolink type.
        """

        return self.leaves.get(_bl_type, {}).get('preferred_id', 'id')

    def _filter_props(self, bl_type: str, props: dict) -> dict:
        """
        Filters properties for those specified in schema_config if any.
        """

        filter_props = self.leaves[bl_type].get('properties', {})
        exclude_props = set(
            _misc.to_list(
                self.leaves[bl_type].get('exclude_properties', []),
            ),
        )

        prop_keys = (
            (set(props.keys()) - exclude_props) &
            set(filter_props.keys())
        )

        props = {k: props[k] for k in prop_keys}

        missing_keys = (
            set(filter_props.keys()) -
            exclude_props -
            set(props.keys())
        )

        # add missing properties with default values
        props.update({k: None for k in missing_keys})

        return props

    def _record_no_type(self, _type: Any, what: Any) -> None:
        """
        Records the type of a node or edge that is not represented in the
        schema_config.
        """

        logger.debug(f'No Biolink type defined for `{_type}`: {what}')

        self.notype[_type] += 1

    def get_missing_bl_types(self) -> dict:
        """
        Returns a dictionary of types that were not represented in the
        schema_config.
        """

        return self.notype

    @staticmethod
    def _log_begin_translate(_input: Iterable, what: str):

        n = f'{len(_input)} ' if hasattr(_input, '__len__') else ''

        logger.debug(f'Translating {n}{what} to BioCypher')

    @staticmethod
    def _log_finish_translate(what: str):

        logger.debug(f'Finished translating {what} to BioCypher.')

    def _update_bl_types(self):
        """
        Creates a dictionary to translate from input labels to Biolink labels.

        If multiple input labels, creates mapping for each.
        """

        self._bl_types = {}

        for key, value in self.leaves.items():

            if isinstance(value.get('label_in_input'), str):
                self._bl_types[value.get('label_in_input')] = key

            elif isinstance(value.get('label_in_input'), list):
                for label in value['label_in_input']:
                    self._bl_types[label] = key

    def _get_bl_type(self, label: str) -> Optional[str]:
        """
        For each given input type ("label_in_input"), find the corresponding
        Biolink type in the leaves dictionary.

        Args:
            label:
                The input type to find (`label_in_input` in
                `schema_config.yaml`).
        """

        # commented out until behaviour of _update_bl_types is fixed
        return self._bl_types.get(label, None)
