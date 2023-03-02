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
from collections.abc import Mapping, Iterable, Generator
import itertools

from ._logger import logger

logger.debug(f'Loading module {__name__}.')

from typing import Any, Union, Optional
import os
import re
import json
import pickle
import hashlib

from bmt.utils import sentencecase_to_camelcase
from more_itertools import peekable
from linkml_runtime.linkml_model.meta import TypeDefinition, ClassDefinition
from networkx.algorithms.traversal.depth_first_search import dfs_tree
import bmt
import obonet
import appdirs
import networkx as nx

from . import _misc
from ._config import _read_yaml, module_data_path
from ._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode

__all__ = ['BiolinkAdapter', 'Translator']


class OntologyAdapter:
    """
    Generic ontology adapter class. Can ingest OBO files and build a hybrid
    ontology from them. Uses Biolink as the default head ontology if no URL is
    given.

    TODO:
        build visualisation only for parts of the schema_config also for tail
        ontology

        update show ontology structure to print also tail ontology info

        genericise leaves creation beyond biolink
    """
    def __init__(
        self,
        head_ontology_url: Optional[str] = None,
        biolink_adapter: Optional['BiolinkAdapter'] = None,
        tail_ontologies: Optional[Iterable] = None,
    ):
        """
        Args:
            head_ontology_url:
                URL to the head ontology.

            biolink_adapter:
                A BiolinkAdapter instance. To be supplied if no head ontology URL
                is given.

            tail_ontologies:
                A list of dictionaries carrying the URL and join nodes for each
                tail ontology to be joined to the head ontology. Keywords are
                'url' for the location of the OBO file, 'head_join_node' for the
                class name of the node in the head ontology to be hybridised to,
                and 'tail_join_node' for the class name of the node in the tail
                ontology to be joined to the head ontology.
        """

        if not head_ontology_url and not biolink_adapter:
            raise ValueError(
                'Either head_ontology_url or biolink_adapter must be supplied.'
            )

        self.head_ontology_url = head_ontology_url
        self.biolink_adapter = biolink_adapter
        self.tail_ontology_meta = tail_ontologies

        # pass on leaves from biolink adapter, only works for the case of
        # Biolink as head ontology; TODO generalise
        if self.biolink_adapter:
            self.leaves = self.biolink_adapter.leaves
            self.biolink_leaves = self.biolink_adapter.biolink_leaves

        self.head_ontology = None
        self.tail_ontology_list = None
        self.hybrid_ontology = None

        self.main()

    def main(self):
        """
        Main method to be run on instantiation. Loads the ontologies, joins
        them, and returns the hybrid ontology. Loads only the Biolink ontology
        if nothing else is given.
        """
        self.load_ontologies()

        if self.tail_ontology_list:
            for onto_dict in self.tail_ontology_list:
                onto_dict = self.find_join_nodes(onto_dict)
                self.join_ontologies(onto_dict)

    def load_ontologies(self):
        """
        Loads the ontologies using obonet. Importantly, obonet orients edges not
        from parent to child, but from child to parent, which goes against the
        assumptions in networkx. For instance, for subsetting the ontology, the
        .reverse() method needs to be called first. If head ontology is loaded
        from Biolink, it is reversed to be consistent with obonet. Currently,
        we use the names of the nodes instead of accessions, so we reverse the
        name and ID mapping. The accession becomes the 'id' attribute of the
        node data.
        """

        # use Biolink as the head ontology if no URL is given
        if self.head_ontology_url:

            self.head_ontology = obonet.read_obo(self.head_ontology_url)

            self.head_ontology = self.reverse_name_and_accession(
                self.head_ontology
            )

        else:

            self.head_ontology = self.biolink_adapter.get_networkx_graph(
            ).reverse()

        # tail ontologies are always loaded from URL
        if self.tail_ontology_meta:

            self.tail_ontology_list = []

            for meta_dict in self.tail_ontology_meta:

                onto_net = obonet.read_obo(meta_dict['url'])
                head_join_node = meta_dict['head_join_node']
                tail_join_node = meta_dict['tail_join_node']

                onto_net, head_join_node, tail_join_node = self.reverse_name_and_accession(
                    onto_net,
                    head_join_node,
                    tail_join_node,
                )

                self.tail_ontology_list.append(
                    {
                        'tail_ontology': onto_net,
                        'head_join_node': head_join_node,
                        'tail_join_node': tail_join_node,
                    }
                )

    def find_join_nodes(self, onto_dict: dict):
        """
        Finds the join nodes in the ontologies. If the join nodes are not
        found, the method will raise an error.

        Args:
            onto_dict:
                A dictionary containing the networkx graph of the ontology,
                the name of the head join node, and the name of the tail join
                node.
        """

        head_join_node = onto_dict['head_join_node']
        tail_join_node = onto_dict['tail_join_node']
        tail_ontology = onto_dict['tail_ontology']

        if head_join_node not in self.head_ontology.nodes:

            if self.head_ontology_url:

                head_join_node = self.find_join_node_by_name(
                    self.head_ontology, head_join_node
                )

            else:

                raise ValueError(
                    f'Head join node {head_join_node} not found in '
                    f'head ontology.'
                )

        if tail_join_node not in tail_ontology.nodes:

            tail_join_node = self.find_join_node_by_name(
                tail_ontology, tail_join_node
            )

            if not tail_join_node:

                raise ValueError(
                    f'Tail join node {tail_join_node} not found in '
                    f'tail ontology.'
                )

        return {
            'head_join_node': head_join_node,
            'tail_join_node': tail_join_node,
            'tail_ontology': tail_ontology,
        }

    def find_join_node_by_name(self, ontology, node_name):
        """
        Finds the join node in the ontology by name. If the join node is not
        found, the method will return None.
        """
        name_to_id = {
            data.get('name'): _id
            for _id, data in ontology.nodes(data=True)
        }

        return name_to_id.get(node_name)

    def reverse_name_and_accession(
        self,
        ontology,
        head_join_node: Optional[str] = None,
        tail_join_node: Optional[str] = None,
    ):
        """
        Reverses the name and ID of the ontology nodes. Replaces underscores in
        the node names with spaces. Currently standard for consistency with
        Biolink, although we lose the original ontology's spelling. Replaces the
        underscores in the join node names as well.

        Args:
            ontology:
                The networkx graph of the ontology.
            head_join_node:
                The name of the head join node.
            tail_join_node:
                The name of the tail join node.
        """

        if head_join_node:
            head_join_node = head_join_node.replace('_', ' ')

        if tail_join_node:
            tail_join_node = tail_join_node.replace('_', ' ')

        id_to_name = {}
        for _id, data in ontology.nodes(data=True):
            data['accession'] = _id
            id_to_name[_id] = data.get('name').replace('_', ' ')

        ontology = nx.relabel_nodes(ontology, id_to_name)

        return ontology, head_join_node, tail_join_node

    def join_ontologies(self, onto_dict: dict):
        """
        Joins the ontologies by adding the tail ontology as a subgraph to the
        head ontology at the specified join nodes. Note that the tail ontology
        needs to be reversed before creating the subgraph, as obonet orients
        edges from child to parent.

        Args:
            onto_dict:
                A dictionary containing the networkx graph of the ontology,
                the name of the head join node, and the name of the tail join
                node.
        """

        self.hybrid_ontology = self.head_ontology.copy()

        head_join_node = onto_dict['head_join_node']
        tail_join_node = onto_dict['tail_join_node']
        tail_ontology = onto_dict['tail_ontology']

        # subtree of tail ontology at join node
        tail_ontology_subtree = dfs_tree(
            tail_ontology.reverse(), tail_join_node
        ).reverse()

        # transfer node attributes from tail ontology to subtree
        for node in tail_ontology_subtree.nodes:
            tail_ontology_subtree.nodes[node].update(tail_ontology.nodes[node])

        # rename tail join node to match head join node
        if not tail_join_node == head_join_node:
            tail_ontology_subtree = nx.relabel_nodes(
                tail_ontology_subtree, {tail_join_node: head_join_node}
            )

        # combine head ontology and tail subtree
        self.hybrid_ontology = nx.compose(
            self.hybrid_ontology, tail_ontology_subtree
        )

    def show_ontology_structure(self):
        """
        Show the ontology structure using treelib.
        """

        msg = 'Showing ontology structure,'

        if self.hybrid_ontology:

            ontology = self.hybrid_ontology

        else:

            ontology = self.head_ontology

        tree = _misc.create_tree_visualisation(ontology)

        msg += f' based on Biolink {self.biolink_adapter.biolink_version}:'
        print(msg)

        # add synonym information
        for class_name in self.leaves:
            if self.leaves[class_name].get('synonym_for'):
                tree.nodes[class_name].tag = (
                    f'{class_name} = '
                    f"{self.leaves[class_name].get('synonym_for')}"
                )

        tree.show()

        return tree

    def get_node_ancestry(self, node: str):
        """
        Returns the ancestry of a node in the ontology.
        """
        if self.hybrid_ontology:

            ontology = self.hybrid_ontology

        else:

            ontology = self.head_ontology

        # check if node in ontology
        if node not in ontology.nodes:
            return None

        return list(dfs_tree(ontology, node))


class BiolinkAdapter:
    """
    Performs various functions to integrate the Biolink ontology.
    """
    def __init__(
        self,
        leaves: dict,
        translator: 'Translator',
        schema: str = None,
        build_from_biolink_version: str = None,
        clear_cache: bool = False,
    ):
        """
        Args:
            leaves:
                A dictionary representing the constituents of the graph
                to be built. These are the "leaves" of the ontology
                hierarchy tree.
            translator:
                A Translator instance.
            schema:
                A path to a YAML file with the schema. If not provided, the
                default Biolink schema will be used.
            build_from_biolink_version:
                The version of the Biolink schema to use to build the adapter.
                If not provided, the current default version will be used.
            clear_cache:
                If True, the Biolink model cache will be cleared and rebuilt.
        """

        self.translator = translator

        self.leaves = leaves
        self.schema = schema
        self.build_from_biolink_version = build_from_biolink_version
        self.biolink_version = None
        self.biolink_leaves = None

        # property to store ad hoc inheritance to log in case of cache load
        self._ad_hoc_inheritance = []
        self.inheritance_tree = None

        self.clear_cache = clear_cache

        # it makes no sense to provide a yaml and a version at the same time
        if self.schema and self.build_from_biolink_version:
            raise ValueError(
                'Please provide either a schema or a version, not both.',
            )

        logger.debug('Instantiating Biolink Adapter.')

        self.main()

    def main(self):
        """
        Initialises the Biolink Model Toolkit and builds the mappings.

        Since this is a time-consuming step that depends on online
        functionality, we can save the resulting objects (biolink leaves,
        mappings, and version) to a file and load them from there if they
        already exist. The cache is overwritten if the schema configuration has
        been updated. This is checked via a hash of the leaves dict.
        """

        # check if cache exists
        cache_dir = appdirs.user_cache_dir('biocypher')
        cache_path = os.path.join(cache_dir, 'biolink_cache.json')

        if self.clear_cache:
            if os.path.exists(cache_path):
                os.remove(cache_path)

        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                cache = json.load(f)
            cached_hash = cache.get('hash', None)
        else:
            cached_hash = None

        # check if schema config has changed
        current_hash = hashlib.md5(
            json.dumps(self.leaves, sort_keys=True).encode('utf-8'),
        ).hexdigest()

        if cached_hash == current_hash:
            # use cached version
            self.translator.mappings = cache['mappings']
            self.translator.reverse_mappings = cache['reverse_mappings']
            self.biolink_version = cache['version']
            self._ad_hoc_inheritance = cache['ad_hoc_inheritance']
            self.inheritance_tree = cache['inheritance_tree']
            self.nested_inheritance_tree = cache['nested_inheritance_tree']

            logger.info(
                'Using cached Biolink schema, Biolink model version: '
                f'{self.biolink_version}.'
            )

            if self._ad_hoc_inheritance:
                inherit_msg = 'Ad hoc inheritance found in cache:\n'
                for key, value in self._ad_hoc_inheritance:
                    inherit_msg += f'   {key} -> {value}\n'
                logger.info(inherit_msg)

            # load biolink leaves from pickle
            biolink_leaves_path = cache['biolink_leaves_path']
            with open(biolink_leaves_path, 'rb') as f:
                self.biolink_leaves = pickle.load(f)

        else:
            logger.info(
                'Building Biolink schema and saving to cache. '
                'This step can sometimes take several minutes for reasons '
                'related to LinkML online functions. It is so far not clear '
                'what exactly causes it, but an issue has been opened at '
                'the source. Please try again shortly.'
            )
            # initialise biolink toolkit
            self.init_toolkit()
            # translate leaves
            self.translate_leaves_to_biolink()
            # create complete ontology backbone
            self.create_ontology_backbone()

            if self._ad_hoc_inheritance:
                inherit_msg = 'Ad hoc inheritance found in config:\n'
                for key, value in self._ad_hoc_inheritance:
                    inherit_msg += f'   {key} -> {value}\n'
                logger.info(inherit_msg)

            # save JSON and picke to cache
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)

            # pickle biolink leaves to cache dir
            pickle_path = os.path.join(cache_dir, 'biolink_leaves.pickle')
            with open(pickle_path, 'wb') as f:
                pickle.dump(self.biolink_leaves, f)

            # save cache
            cache = {
                'biolink_leaves_path': pickle_path,
                'mappings': self.translator.mappings,
                'reverse_mappings': self.translator.reverse_mappings,
                'version': self.biolink_version,
                'hash': current_hash,
                'ad_hoc_inheritance': self._ad_hoc_inheritance,
                'inheritance_tree': self.inheritance_tree,
                'nested_inheritance_tree': self.nested_inheritance_tree,
            }
            with open(cache_path, 'w') as f:
                json.dump(cache, f)

    def init_toolkit(self):
        """
        Set Biolink schema to use. By default, BioCypher should use the public
        current version of the Biolink model for compatibility reasons. The user
        can define a custom schema in YAML format (conforming to LinkML and the
        Biolink model structure), which will be used instead.
        """

        if self.schema:
            # use custom schema
            self.toolkit = bmt.Toolkit(self.schema)
            logger.info(
                f'Creating BioLink model toolkit from `{self.schema}`.',
            )

            # TODO extract version from schema and update self.biolink_version

        elif self.build_from_biolink_version:

            # TODO use version to get schema from biolink repo
            # TODO use schema to create toolkit
            raise NotImplementedError(
                'Pinning Biolink versions is not implemented yet.',
            )

        else:
            # use default schema
            self.toolkit = bmt.Toolkit()
            self.biolink_version = self.toolkit.get_model_version()
            logger.info(
                'Creating BioLink model toolkit from default schema.'
                f' Biolink model version: {self.biolink_version}'
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

            # check whether valid biolink entity should be called by a synonym
            # in the KG (e.g. for readability reasons)
            if not values.get('synonym_for'):
                name_or_synonym = entity
            else:
                name_or_synonym = values['synonym_for']

            entity_biolink_class = self.toolkit.get_element(
                name_or_synonym
            )  # element name

            if entity_biolink_class:

                # find ancestors of biolink type in PascalCase
                ancestors = self.trim_biolink_ancestry(
                    self.toolkit.get_ancestors(name_or_synonym, formatted=True),
                )

                if values.get('synonym_for'):
                    # add synonym to ancestors
                    ancestors.insert(
                        0, self.translator.name_sentence_to_pascal(entity)
                    )

                input_label = values.get('label_in_input')

                # add translation mappings
                bc_name = (
                    values.get('label_as_edge')
                    if values.get('label_as_edge') else entity
                )
                self.translator._add_translation_mappings(input_label, bc_name)

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

    def create_ontology_backbone(self):
        """
        Create the backbone of the ontology by adding all classes that are
        ancestors of the leaves to receive a coherent parent-child structure.
        Also create a nested dictionary for creating a networkx instance of the
        ontology backbone.
        """

        # refactor inheritance tree to be compatible with treelib
        flat_treedict = {
            'entity': None,  # root node
            'mixin': ['entity'],
        }

        for class_name, properties in self.biolink_leaves.items():

            if isinstance(properties['class_definition'], TypeDefinition):
                logger.warning(
                    f'Leaf `{class_name}` is a type definition, not a class.'
                    ' This is not supported yet.'
                )
                continue

            if properties['class_definition']['is_a'] is not None:

                parent = [str(properties['class_definition']['is_a'])]

                mixins = list(properties['class_definition']['mixins'])

                if mixins:
                    parent.extend(mixins)

                # add to flat treedict
                flat_treedict[class_name] = parent

        # flatten values lists of flat_treedict to set of parents
        parents = set()
        for value in flat_treedict.values():
            if isinstance(value, list):
                for v in value:
                    parents.add(v)
            else:
                parents.add(value)

        parents.discard(None)
        children = set(flat_treedict.keys())

        # while there are still parents that are not in the tree
        while parents - children:
            missing = parents - children

            # add missing parents to tree
            for child in missing:
                element = self.toolkit.get_element(child)
                if element:
                    # get parent
                    parent = element['is_a']

                    if not parent:

                        if self.toolkit.is_mixin(child):

                            flat_treedict[child] = ['mixin']

                    else:

                        parent = [parent]

                        # get mixins
                        mixins = element['mixins']

                        if mixins:
                            parent.extend(mixins)

                        flat_treedict[child] = parent

            parents = set()
            for value in flat_treedict.values():
                if isinstance(value, list):
                    for v in value:
                        parents.add(v)
                else:
                    parents.add(value)
            parents.discard(None)
            children = set(flat_treedict.keys())

        # add all entries to a nested treedict starting from the entity node
        nested_treedict = {'entity': {}}

        in_tree = set(['entity'])
        # delete entity from todo
        flat_treedict.pop('entity')

        while flat_treedict:

            added = {}

            for child, parents in flat_treedict.items():
                parents = _misc.ensure_iterable(parents)
                for parent in parents:
                    if parent in in_tree:
                        # find parent recursively in nested treedict
                        nested_treedict = self._add_class_to_nested_treedict(
                            child,
                            parent,
                            {},
                            nested_treedict,
                        )
                        # add parent to child list of added
                        if child not in added:
                            added[child] = set([parent])
                        else:
                            added[child].update([parent])

            for key, parents in added.items():
                parents = _misc.ensure_iterable(parents)
                for parent in parents:
                    if parent not in flat_treedict[key]:
                        continue
                    # remove parent from flat_treedict[child]
                    flat_treedict[key].remove(parent)
                in_tree.add(key)

            # remove flat_treedict entries with empty parents list
            for key in list(flat_treedict):
                if not flat_treedict[key]:
                    flat_treedict.pop(key)

        self.nested_inheritance_tree = nested_treedict

    def _add_class_to_nested_treedict(
        self, class_name, parent, properties, nested_treedict
    ):
        """
        Add a class to the nested treedict recursively.
        """

        if parent not in nested_treedict:

            for key, value in nested_treedict.items():
                if isinstance(value, dict):
                    nested_treedict[key] = self._add_class_to_nested_treedict(
                        class_name,
                        parent,
                        properties,
                        value,
                    )

        else:
            if nested_treedict.get(parent) is None:
                nested_treedict[parent] = {class_name: properties}
            else:
                nested_treedict[parent].update({class_name: properties})

        return nested_treedict

    def _get_biolink_properties(self, class_name):
        """
        Get the properties of a Biolink class. Inserted into the nested
        treedict for networkx creation.
        """

        # check whether self has toolkit attribute
        if not hasattr(self, 'toolkit'):
            self.init_toolkit()

        props = {}

        values = self.leaves.get(class_name)

        if not values:

            classdef = self.toolkit.get_element(class_name)

        else:

            if not values.get('synonym_for'):

                name_or_synonym = class_name

            else:

                name_or_synonym = values['synonym_for']

            classdef = self.toolkit.get_element(name_or_synonym)

        if classdef:
            # use _get to get item from json object (parent of linkml classdef)
            props['exact_mappings'] = classdef._get('exact_mappings')
            props['close_mappings'] = classdef._get('close_mappings')
            props['narrow_mappings'] = classdef._get('narrow_mappings')
            props['broad_mappings'] = classdef._get('broad_mappings')
            props['is_a'] = classdef._get('is_a')
            props['description'] = classdef._get('description')
            props['class_uri'] = classdef._get('class_uri')
            props['id_prefixes'] = classdef._get('id_prefixes')
            props['name'] = classdef._get('name')

        return props

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

        self._ad_hoc_inheritance.append((parents[0], entity))

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
                ancestors += [self.translator.name_sentence_to_pascal(parent)]

        if ancestors:
            ancestors.insert(0, self.translator.name_sentence_to_pascal(entity))
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
        self.translator._add_translation_mappings(input_label, entity)

    def _build_biolink_edge_class(self, entity: str, values: dict) -> None:
        """
        Build a Biolink edge class definition from a Biolink entity name
        and property dict.
        """

        input_label = values.get('label_in_input')
        parents = _misc.to_list(values.get('is_a'))
        ancestors = []

        self._ad_hoc_inheritance.append((parents[0], entity))

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
                ancestors += [self.translator.name_sentence_to_pascal(parent)]

        if ancestors:
            ancestors.insert(0, self.translator.name_sentence_to_pascal(entity))
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
        bc_name = values.get('label_as_edge'
                            ) if values.get('label_as_edge') else entity
        self.translator._add_translation_mappings(input_label, bc_name)

    @staticmethod
    def trim_biolink_ancestry(ancestry: list[str]) -> list[str]:
        """
        Trims "biolink:" prefix from Biolink ancestry elements.
        """

        # replace 'biolink:' with ''
        return [re.sub('^biolink:', '', a) for a in ancestry]

    def get_networkx_graph(self) -> nx.DiGraph:
        """
        Get the ontology as a networkx graph.
        """

        # Empty directed graph
        graph = nx.DiGraph()

        # Add nodes and their data from nested inheritance tree
        queue = list(self.nested_inheritance_tree.items())
        while queue:
            parent_class, children = queue.pop()
            data = self._get_biolink_properties(parent_class)
            graph.add_node(parent_class, **data)
            for child_class, grandchildren in children.items():
                if isinstance(children, Mapping):
                    queue.append((child_class, grandchildren))

        # Add edges from nested inheritance tree
        queue = list(self.nested_inheritance_tree.items())
        while queue:
            parent_class, children = queue.pop()
            for child_class, grandchildren in children.items():
                graph.add_edge(parent_class, child_class)
                if isinstance(grandchildren, Mapping):
                    queue.append((child_class, grandchildren))

        return graph


# Biolink toolkit wiki:
# https://biolink.github.io/biolink-model-toolkit/example_usage.html

# -------------------------------------------
# Create nodes and edges from separate inputs
# -------------------------------------------


class Translator:
    """
    Class responsible for exacting the translation process that is configured in
    the schema_config.yaml file. Creates a mapping dictionary from that file,
    and, given nodes and edges, translates them into BioCypherNodes and
    BioCypherEdges. During this process, can also filter the properties of the
    entities if the schema_config.yaml file specifies a property whitelist or
    blacklist.

    Provides utility functions for translating between input and output labels
    and cypher queries.
    """
    def __init__(self, leaves: dict[str, dict], strict_mode: bool = False):
        """
        Args:
            leaves:
                Dictionary detailing the leaves of the hierarchy
                tree representing the structure of the graph; the leaves are
                the entities that will be direct components of the graph,
                while the intermediary nodes are additional labels for
                filtering purposes.
            strict_mode:
                If True, the translator will raise an error if input data do not
                carry source, licence, and version information.
        """

        self.leaves = leaves
        self.strict_mode = strict_mode
        self._update_ontology_types()

        # record nodes without biolink type configured in schema_config.yaml
        self.notype = {}

        # mapping functionality for translating terms and queries
        self.mappings = {}
        self.reverse_mappings = {}

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

        self._log_begin_translate(id_type_prop_tuples, 'nodes')

        for _id, _type, _props in id_type_prop_tuples:

            # check for strict mode requirements
            required_props = ['source', 'licence', 'version']

            if self.strict_mode:
                # rename 'license' to 'licence' in _props
                if _props.get('license'):
                    _props['licence'] = _props.pop('license')

                for prop in required_props:
                    if prop not in _props:
                        raise ValueError(
                            f'Property `{prop}` missing from node {_id}. '
                            'Strict mode is enabled, so this is not allowed.'
                        )

            # find the node in leaves that represents biolink node type
            _ontology_class = self._get_ontology_mapping(_type)

            if _ontology_class:

                # filter properties for those specified in schema_config if any
                _filtered_props = self._filter_props(_ontology_class, _props)

                # preferred id
                _preferred_id = self._get_preferred_id(_ontology_class)

                yield BioCypherNode(
                    node_id=_id,
                    node_label=_ontology_class,
                    preferred_id=_preferred_id,
                    properties=_filtered_props,
                )

            else:

                self._record_no_type(_type, _id)

        self._log_finish_translate('nodes')

    def _get_preferred_id(self, _bl_type: str) -> str:
        """
        Returns the preferred id for the given Biolink type.
        """

        return (
            self.leaves[_bl_type]['preferred_id']
            if 'preferred_id' in self.leaves.get(_bl_type, {}) else 'id'
        )

    def _filter_props(self, bl_type: str, props: dict) -> dict:
        """
        Filters properties for those specified in schema_config if any.
        """

        filter_props = self.leaves[bl_type].get('properties', {})

        # strict mode: add required properties (only if there is a whitelist)
        if self.strict_mode and filter_props:
            filter_props.update(
                {
                    'source': 'str',
                    'licence': 'str',
                    'version': 'str'
                },
            )

        exclude_props = self.leaves[bl_type].get('exclude_properties', [])

        if isinstance(exclude_props, str):
            exclude_props = [exclude_props]

        if filter_props and exclude_props:

            filtered_props = {
                k: v
                for k, v in props.items()
                if (k in filter_props.keys() and k not in exclude_props)
            }

        elif filter_props:

            filtered_props = {
                k: v
                for k, v in props.items() if k in filter_props.keys()
            }

        elif exclude_props:

            filtered_props = {
                k: v
                for k, v in props.items() if k not in exclude_props
            }

        else:

            return props

        missing_props = [
            k for k in filter_props.keys() if k not in filtered_props.keys()
        ]
        # add missing properties with default values
        for k in missing_props:

            filtered_props[k] = None

        return filtered_props

    def translate_edges(
        self,
        id_src_tar_type_prop_tuples: Iterable,
    ) -> Generator[Union[BioCypherEdge, BioCypherRelAsNode], None, None]:
        """
        Translates input edge representation to a representation that
        conforms to the schema of the given BioCypher graph. For now
        requires explicit statement of edge type on pass.

        Args:

            id_src_tar_type_prop_tuples (list of tuples):

                collection of tuples representing source and target of
                an interaction via their unique ids as well as the type
                of interaction in the original database notation, which
                is translated to BioCypher notation using the `leaves`.
                Can optionally possess its own ID.
        """
        # TODO:
        #    - id of interactions (now simple concat with "_")
        #    - do we even need one?

        self._log_begin_translate(id_src_tar_type_prop_tuples, 'edges')

        # legacy: deal with 4-tuples (no edge id)
        # TODO remove for performance reasons once safe
        id_src_tar_type_prop_tuples = peekable(id_src_tar_type_prop_tuples)
        if len(id_src_tar_type_prop_tuples.peek()) == 4:
            id_src_tar_type_prop_tuples = [
                (None, src, tar, typ, props)
                for src, tar, typ, props in id_src_tar_type_prop_tuples
            ]

        for _id, _src, _tar, _type, _props in id_src_tar_type_prop_tuples:

            # check for strict mode requirements
            if self.strict_mode:
                if not 'source' in _props:
                    raise ValueError(
                        f'Edge {_id if _id else (_src, _tar)} does not have a `source` property.',
                        ' This is required in strict mode.',
                    )
                if not 'licence' in _props:
                    raise ValueError(
                        f'Edge {_id if _id else (_src, _tar)} does not have a `licence` property.',
                        ' This is required in strict mode.',
                    )

            # match the input label (_type) to
            # a Biolink label from schema_config
            bl_type = self._get_ontology_mapping(_type)

            if bl_type:

                # filter properties for those specified in schema_config if any
                _filtered_props = self._filter_props(bl_type, _props)

                rep = self.leaves[bl_type]['represented_as']

                if rep == 'node':

                    if _id:
                        # if it brings its own ID, use it
                        node_id = _id

                    else:
                        # source target concat
                        node_id = (
                            str(_src) + '_' + str(_tar) + '_' +
                            '_'.join(str(v) for v in _filtered_props.values())
                        )

                    n = BioCypherNode(
                        node_id=node_id,
                        node_label=bl_type,
                        properties=_filtered_props,
                    )

                    # directionality check TODO generalise to account for
                    # different descriptions of directionality or find a
                    # more consistent solution for indicating directionality
                    if _filtered_props.get('directed') == True:

                        l1 = 'IS_SOURCE_OF'
                        l2 = 'IS_TARGET_OF'

                    elif _filtered_props.get(
                        'src_role',
                    ) and _filtered_props.get('tar_role'):

                        l1 = _filtered_props.get('src_role')
                        l2 = _filtered_props.get('tar_role')

                    else:

                        l1 = l2 = 'IS_PART_OF'

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

                    edge_label = self.leaves[bl_type].get('label_as_edge')

                    if edge_label is None:

                        edge_label = bl_type

                    yield BioCypherEdge(
                        relationship_id=_id,
                        source_id=_src,
                        target_id=_tar,
                        relationship_label=edge_label,
                        properties=_filtered_props,
                    )

            else:

                self._record_no_type(_type, (_src, _tar))

        self._log_finish_translate('edges')

    def _record_no_type(self, _type: Any, what: Any) -> None:
        """
        Records the type of a node or edge that is not represented in the
        schema_config.
        """

        logger.debug(f'No Biolink type defined for `{_type}`: {what}')

        if self.notype.get(_type, None):

            self.notype[_type] += 1

        else:

            self.notype[_type] = 1

    def get_missing_biolink_types(self) -> dict:
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

    def _update_ontology_types(self):
        """
        Creates a dictionary to translate from input labels to ontology labels.

        If multiple input labels, creates mapping for each.
        """

        self._ontology_mapping = {}

        for key, value in self.leaves.items():

            if isinstance(value.get('label_in_input'), str):
                self._ontology_mapping[value.get('label_in_input')] = key

            elif isinstance(value.get('label_in_input'), list):
                for label in value['label_in_input']:
                    self._ontology_mapping[label] = key

    def _get_ontology_mapping(self, label: str) -> Optional[str]:
        """
        For each given input type ("label_in_input"), find the corresponding
        ontology class in the leaves dictionary (from the `schema_config.yam`).

        Args:
            label:
                The input type to find (`label_in_input` in
                `schema_config.yaml`).
        """

        # commented out until behaviour of _update_bl_types is fixed
        return self._ontology_mapping.get(label, None)

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
                        a,
                        ':' + self.reverse_mappings[key] + ')',
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
                self.reverse_mappings[self.name_sentence_to_pascal(bn, )
                                     ] = original_name
        else:
            self.reverse_mappings[self.name_sentence_to_pascal(
                biocypher_name,
            )] = original_name

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
