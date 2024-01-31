#!/usr/bin/env python

#
# Copyright 2021, Heidelberg University Clinic
#
# File author(s): Sebastian Lobentanzer
#                 ...
#
# Distributed under MIT licence, see the file `LICENSE`.
#
"""
BioCypher 'ontology' module. Contains classes and functions to handle parsing
and representation of single ontologies as well as their hybridisation and
other advanced operations.
"""
import os

from ._logger import logger

logger.debug(f"Loading module {__name__}.")

from typing import Optional
from datetime import datetime

import rdflib
import networkx as nx

from ._misc import (
    to_list,
    to_lower_sentence_case,
    create_tree_visualisation,
    sentencecase_to_pascalcase,
)
from ._mapping import OntologyMapping


class OntologyAdapter:
    """
    Class that represents an ontology to be used in the Biocypher framework. Can
    read from a variety of formats, including OWL, OBO, and RDF/XML. The
    ontology is represented by a networkx.DiGraph object; an RDFlib graph is
    also kept. By default, the DiGraph reverses the label and identifier of the
    nodes, such that the node name in the graph is the human-readable label. The
    edges are oriented from child to parent. Going from the Biolink example,
    labels are formatted in lower sentence case. In some cases, this means that
    we replace underscores with spaces.
    """

    def __init__(
        self,
        ontology_file: str,
        root_label: str,
        format: Optional[str] = None,
        head_join_node: Optional[str] = None,
        merge_nodes: Optional[bool] = True,
        reverse_labels: bool = True,
        remove_prefixes: bool = True,
    ):
        """
        Initialize the OntologyAdapter class.

        Args:
            ontology_file (str): Path to the ontology file. Can be local or
                remote.

            root_label (str): The label of the root node in the ontology. In
                case of a tail ontology, this is the tail join node.

            head_join_node (str): Optional variable to store the label of the
                node in the head ontology that should be used to join to the
                root node of the tail ontology. Defaults to None.

            merge_nodes (bool): If True, head and tail join nodes will be
                merged, using the label of the head join node. If False, the
                tail join node will be attached as a child of the head join
                node.

            reverse_labels (bool): If True, the node names in the graph will be
                the human-readable labels. If False, the node names will be the
                identifiers. Defaults to True.

            remove_prefixes (bool): If True, the prefixes of the identifiers will
                be removed. Defaults to True.
        """

        logger.info(f"Instantiating OntologyAdapter class for {ontology_file}.")

        self._ontology_file = ontology_file
        self._root_label = root_label
        self._format = format
        self._merge_nodes = merge_nodes
        self._head_join_node = head_join_node
        self._reverse_labels = reverse_labels
        self._remove_prefixes = remove_prefixes

        # Load the ontology into a rdflib Graph according to the file extension
        self._rdf_graph = self._load_rdf_graph(ontology_file)

        self._nx_graph = self._rdf_to_nx(
            self._rdf_graph, root_label, reverse_labels
        )

    def _rdf_to_nx(self, g, root_label, switch_id_and_label=True):
        root = self._find_root_label(g, root_label)

        # Create a directed graph to represent the ontology as a tree
        G = nx.DiGraph()

        # Define a recursive function to add subclasses to the graph
        def add_subclasses(parent_node):
            if not has_label(parent_node, g):
                return

            nx_parent_node_id, nx_parent_node_label = _get_nx_id_and_label(
                parent_node
            )

            if nx_parent_node_id not in G:
                add_node(nx_parent_node_id, nx_parent_node_label)

            child_nodes = get_child_nodes(parent_node, g)

            if child_nodes:
                for child_node in child_nodes:
                    if not has_label(child_node, g):
                        continue
                    (
                        nx_child_node_id,
                        nx_child_node_label,
                    ) = _get_nx_id_and_label(child_node)
                    add_node(nx_child_node_id, nx_child_node_label)
                    G.add_edge(nx_child_node_id, nx_parent_node_id)
                for child_node in child_nodes:
                    add_subclasses(child_node)
                    add_parents(child_node)

        def add_parents(node):
            if not has_label(node, g):
                return

            nx_id, nx_label = _get_nx_id_and_label(node)

            # Recursively add all parents of the node to the graph
            for s, _, o in g.triples((node, rdflib.RDFS.subClassOf, None)):
                if not has_label(o, g):
                    continue

                o_id, o_label = _get_nx_id_and_label(o)

                # Skip if node already in the graph
                if o_id in G:
                    continue

                add_node(o_id, o_label)

                G.add_edge(nx_id, o_id)
                add_parents(o)

        def has_label(node: rdflib.URIRef, g: rdflib.Graph) -> bool:
            """Does the node have a label in g?

            Args:
                node (rdflib.URIRef): The node to check
                g (rdflib.Graph): The graph to check in

            Returns:
                bool: True if the node has a label, False otherwise
            """
            return (node, rdflib.RDFS.label, None) in g

        def add_node(nx_node_id: str, nx_node_label: str):
            """Add a node to the graph.

            Args:
                nx_node_id (str): The ID of the node
                nx_node_label (str): The label of the node
            """
            G.add_node(nx_node_id)
            G.nodes[nx_node_id]["label"] = nx_node_label

        def _get_nx_id_and_label(node):
            node_id_str = self._remove_prefix(str(node))
            node_label_str = str(g.value(node, rdflib.RDFS.label)).replace(
                "_", " "
            )
            node_label_str = to_lower_sentence_case(node_label_str)

            nx_id = node_label_str if switch_id_and_label else node_id_str
            nx_label = node_id_str if switch_id_and_label else node_label_str
            return nx_id, nx_label

        def get_child_nodes(
            parent_node: rdflib.URIRef, g: rdflib.Graph
        ) -> list:
            """Get the child nodes of a node in the ontology.
            Accounts for the case of multiple parents defined in intersectionOf.

            Args:
                parent_node (rdflib.URIRef): The parent node to get the children of
                g (rdflib.Graph): The graph to get the children from

            Returns:
                list: A list of the child nodes
            """
            child_nodes = []
            for s, p, o in g.triples((None, rdflib.RDFS.subClassOf, None)):
                if (o, rdflib.RDF.type, rdflib.OWL.Class) in g and (
                    o,
                    rdflib.OWL.intersectionOf,
                    None,
                ) in g:
                    # Check if node has multiple parent nodes defined in intersectionOf (one of them = parent_node)
                    parent_nodes = get_nodes_in_intersectionof(o)
                    if parent_node in parent_nodes:
                        child_nodes.append(s)
                        for node in parent_nodes:
                            add_parents(node)
                elif o == parent_node:
                    # only one parent node
                    child_nodes.append(s)
            return child_nodes

        def get_nodes_in_intersectionof(o: rdflib.URIRef) -> list:
            """Get the nodes in an intersectionOf node.

            Args:
                o (rdflib.URIRef): The intersectionOf node

            Returns:
                list: A list of the nodes in the intersectionOf node
            """
            anonymous_intersection_nodes = []
            for _, _, anonymous_object in g.triples(
                (o, rdflib.OWL.intersectionOf, None)
            ):
                anonymous_intersection_nodes.append(anonymous_object)
            anonymous_intersection_node = anonymous_intersection_nodes[0]
            nodes_in_intersection = retrieve_rdf_linked_list(
                anonymous_intersection_node
            )
            return nodes_in_intersection

        def retrieve_rdf_linked_list(subject: rdflib.URIRef) -> list:
            """Recursively retrieves a linked list from RDF.
            Example RDF list with the items [item1, item2]:
            list_node - first -> item1
            list_node - rest -> list_node2
            list_node2 - first -> item2
            list_node2 - rest -> nil

            Args:
                subject (rdflib.URIRef): One list_node of the RDF list

            Returns:
                list: The items of the RDF list
            """
            rdf_list = []
            for s, p, o in g.triples((subject, rdflib.RDF.first, None)):
                rdf_list.append(o)
            for s, p, o in g.triples((subject, rdflib.RDF.rest, None)):
                if o != rdflib.RDF.nil:
                    rdf_list.extend(retrieve_rdf_linked_list(o))
            return rdf_list

        # Add all subclasses of the root node to the graph
        add_subclasses(root)

        return G

    def _find_root_label(self, g, root_label):
        # Loop through all labels in the ontology
        for label_subject, _, label_in_ontology in g.triples(
            (None, rdflib.RDFS.label, None)
        ):
            # If the label is the root label, set the root node to the label's subject
            if str(label_in_ontology) == root_label:
                root = label_subject
                break
        else:
            raise ValueError(
                f"Could not find root node with label {root_label}"
            )
        return root

    def _remove_prefix(self, uri: str) -> str:
        """
        Remove the prefix of a URI. URIs can contain either "#" or "/" as a
        separator between the prefix and the local name. The prefix is
        everything before the last separator.
        """
        if self._remove_prefixes:
            return uri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]
        else:
            return uri

    def _load_rdf_graph(self, ontology_file):
        """
        Load the ontology into an RDFlib graph. The ontology file can be in
        OWL, OBO, or RDF/XML format.
        """
        g = rdflib.Graph()
        g.parse(ontology_file, format=self._get_format(ontology_file))
        return g

    def _get_format(self, ontology_file):
        """
        Get the format of the ontology file.
        """
        if self._format:
            if self._format == "owl":
                return "application/rdf+xml"
            elif self._format == "obo":
                raise NotImplementedError("OBO format not yet supported")
            elif self._format == "rdf":
                return "application/rdf+xml"
            elif self._format == "ttl":
                return self._format
            else:
                raise ValueError(
                    f"Could not determine format of ontology file {ontology_file}"
                )

        if ontology_file.endswith(".owl"):
            return "application/rdf+xml"
        elif ontology_file.endswith(".obo"):
            raise NotImplementedError("OBO format not yet supported")
        elif ontology_file.endswith(".rdf"):
            return "application/rdf+xml"
        elif ontology_file.endswith(".ttl"):
            return "ttl"
        else:
            raise ValueError(
                f"Could not determine format of ontology file {ontology_file}"
            )

    def get_nx_graph(self):
        """
        Get the networkx graph representing the ontology.
        """
        return self._nx_graph

    def get_rdf_graph(self):
        """
        Get the RDFlib graph representing the ontology.
        """
        return self._rdf_graph

    def get_root_label(self):
        """
        Get the label of the root node in the ontology.
        """
        return self._root_label

    def get_ancestors(self, node_label):
        """
        Get the ancestors of a node in the ontology.
        """
        return nx.dfs_preorder_nodes(self._nx_graph, node_label)

    def get_head_join_node(self):
        """
        Get the head join node of the ontology.
        """
        return self._head_join_node


class Ontology:
    """
    A class that represents the ontological "backbone" of a BioCypher knowledge
    graph. The ontology can be built from a single resource, or hybridised from
    a combination of resources, with one resource being the "head" ontology,
    while an arbitrary number of other resources can become "tail" ontologies at
    arbitrary fusion points inside the "head" ontology.
    """

    def __init__(
        self,
        head_ontology: dict,
        ontology_mapping: Optional["OntologyMapping"] = None,
        tail_ontologies: Optional[dict] = None,
    ):
        """
        Initialize the Ontology class.

        Args:
            head_ontology (OntologyAdapter): The head ontology.

            tail_ontologies (list): A list of OntologyAdapters that will be
                added to the head ontology. Defaults to None.
        """

        self._head_ontology_meta = head_ontology
        self.mapping = ontology_mapping
        self._tail_ontology_meta = tail_ontologies

        self._tail_ontologies = None
        self._nx_graph = None

        # keep track of nodes that have been extended
        self._extended_nodes = set()

        self._main()

    def _main(self) -> None:
        """
        Main method to be run on instantiation. Loads the ontologies, joins
        them, and returns the hybrid ontology. Loads only the head ontology
        if nothing else is given. Adds user extensions and properties from
        the mapping.
        """
        self._load_ontologies()

        if self._tail_ontologies:
            for adapter in self._tail_ontologies.values():
                self._assert_join_node(adapter)
                self._join_ontologies(adapter)
        else:
            self._nx_graph = self._head_ontology.get_nx_graph()

        if self.mapping:
            self._extend_ontology()

            # experimental: add connections of disjoint classes to entity
            self._connect_biolink_classes()

            self._add_properties()

    def _load_ontologies(self) -> None:
        """
        For each ontology, load the OntologyAdapter object and store it as an
        instance variable (head) or a dictionary (tail).
        """

        logger.info("Loading ontologies...")

        self._head_ontology = OntologyAdapter(
            ontology_file=self._head_ontology_meta["url"],
            root_label=self._head_ontology_meta["root_node"],
            format=self._head_ontology_meta.get("format", None),
        )

        if self._tail_ontology_meta:
            self._tail_ontologies = {}
            for key, value in self._tail_ontology_meta.items():
                self._tail_ontologies[key] = OntologyAdapter(
                    ontology_file=value["url"],
                    root_label=value["tail_join_node"],
                    head_join_node=value["head_join_node"],
                    format=value.get("format", None),
                    merge_nodes=value.get("merge_nodes", True),
                )

    def _assert_join_node(self, adapter: OntologyAdapter) -> None:
        """
        Tries to find the head join node of the given ontology adapter in the
        head ontology. If the join node is not found, the method will raise an
        error.

        Args:
            adapter (OntologyAdapter): The ontology adapter of which to find the
                join node in the head ontology.
        """

        head_join_node = adapter.get_head_join_node()

        if head_join_node not in self._head_ontology.get_nx_graph().nodes:
            raise ValueError(
                f"Head join node {head_join_node} not found in "
                f"head ontology."
            )

    def _join_ontologies(self, adapter: OntologyAdapter) -> None:
        """
        Joins the ontologies by adding the tail ontology as a subgraph to the
        head ontology at the specified join nodes.

        Args:
            adapter (OntologyAdapter): The ontology adapter of the tail ontology
                to be added to the head ontology.
        """

        if not self._nx_graph:
            self._nx_graph = self._head_ontology.get_nx_graph().copy()

        head_join_node = to_lower_sentence_case(adapter.get_head_join_node())
        tail_join_node = to_lower_sentence_case(adapter.get_root_label())
        tail_ontology = adapter.get_nx_graph()

        # subtree of tail ontology at join node
        tail_ontology_subtree = nx.dfs_tree(
            tail_ontology.reverse(), tail_join_node
        ).reverse()

        # transfer node attributes from tail ontology to subtree
        for node in tail_ontology_subtree.nodes:
            tail_ontology_subtree.nodes[node].update(tail_ontology.nodes[node])

        # if merge_nodes is False, create parent of tail join node from head
        # join node
        if not adapter._merge_nodes:
            # add head join node from head ontology to tail ontology subtree
            # as parent of tail join node
            tail_ontology_subtree.add_node(
                head_join_node,
                **self._head_ontology.get_nx_graph().nodes[head_join_node],
            )
            tail_ontology_subtree.add_edge(tail_join_node, head_join_node)

        # else rename tail join node to match head join node if necessary
        elif not tail_join_node == head_join_node:
            tail_ontology_subtree = nx.relabel_nodes(
                tail_ontology_subtree, {tail_join_node: head_join_node}
            )

        # combine head ontology and tail subtree
        self._nx_graph = nx.compose(self._nx_graph, tail_ontology_subtree)

    def _extend_ontology(self) -> None:
        """
        Adds the user extensions to the ontology. Tries to find the parent in
        the ontology, adds it if necessary, and adds the child and a directed
        edge from child to parent. Can handle multiple parents.
        """

        if not self._nx_graph:
            self._nx_graph = self._head_ontology.get_nx_graph().copy()

        for key, value in self.mapping.extended_schema.items():
            if not value.get("is_a"):
                if self._nx_graph.has_node(value.get("synonym_for")):
                    continue

                if not self._nx_graph.has_node(key):
                    raise ValueError(
                        f"Node {key} not found in ontology, but also has no "
                        "inheritance definition. Please check your schema for "
                        "spelling errors or a missing `is_a` definition."
                    )

                continue

            parents = to_list(value.get("is_a"))
            child = key

            while parents:
                parent = parents.pop(0)

                if parent not in self._nx_graph.nodes:
                    self._nx_graph.add_node(parent)
                    self._nx_graph.nodes[parent][
                        "label"
                    ] = sentencecase_to_pascalcase(parent)

                    # mark parent as user extension
                    self._nx_graph.nodes[parent]["user_extension"] = True
                    self._extended_nodes.add(parent)

                if child not in self._nx_graph.nodes:
                    self._nx_graph.add_node(child)
                    self._nx_graph.nodes[child][
                        "label"
                    ] = sentencecase_to_pascalcase(child)

                    # mark child as user extension
                    self._nx_graph.nodes[child]["user_extension"] = True
                    self._extended_nodes.add(child)

                self._nx_graph.add_edge(child, parent)

                child = parent

    def _connect_biolink_classes(self) -> None:
        """
        Experimental: Adds edges from disjoint classes to the entity node.
        """

        if not self._nx_graph:
            self._nx_graph = self._head_ontology.get_nx_graph().copy()

        if "entity" not in self._nx_graph.nodes:
            return

        # biolink classes that are disjoint from entity
        disjoint_classes = [
            "frequency qualifier mixin",
            "chemical entity to entity association mixin",
            "ontology class",
            "relationship quantifier",
            "physical essence or occurrent",
            "gene or gene product",
            "subject of investigation",
        ]

        for node in disjoint_classes:
            if not self._nx_graph.nodes.get(node):
                self._nx_graph.add_node(node)
                self._nx_graph.nodes[node][
                    "label"
                ] = sentencecase_to_pascalcase(node)

            self._nx_graph.add_edge(node, "entity")

    def _add_properties(self) -> None:
        """
        For each entity in the mapping, update the ontology with the properties
        specified in the mapping. Updates synonym information in the graph,
        setting the synonym as the primary node label.
        """

        for key, value in self.mapping.extended_schema.items():
            if key in self._nx_graph.nodes:
                self._nx_graph.nodes[key].update(value)

            if value.get("synonym_for"):
                # change node label to synonym
                if value["synonym_for"] not in self._nx_graph.nodes:
                    raise ValueError(
                        f'Node {value["synonym_for"]} not found in ontology.'
                    )

                self._nx_graph = nx.relabel_nodes(
                    self._nx_graph, {value["synonym_for"]: key}
                )

    def get_ancestors(self, node_label: str) -> list:
        """
        Get the ancestors of a node in the ontology.

        Args:
            node_label (str): The label of the node in the ontology.

        Returns:
            list: A list of the ancestors of the node.
        """

        return nx.dfs_tree(self._nx_graph, node_label)

    def show_ontology_structure(self, to_disk: str = None, full: bool = False):
        """
        Show the ontology structure using treelib or write to GRAPHML file.

        Args:

            to_disk (str): If specified, the ontology structure will be saved
                to disk as a GRAPHML file, to be opened in your favourite
                graph visualisation tool.

            full (bool): If True, the full ontology structure will be shown,
                including all nodes and edges. If False, only the nodes and
                edges that are relevant to the extended schema will be shown.
        """

        if not full and not self.mapping.extended_schema:
            raise ValueError(
                "You are attempting to visualise a subset of the loaded"
                "ontology, but have not provided a schema configuration. "
                "To display a partial ontology graph, please provide a schema "
                "configuration file; to visualise the full graph, please use "
                "the parameter `full = True`."
            )

        if not self._nx_graph:
            raise ValueError("Ontology not loaded.")

        if not self._tail_ontologies:
            msg = f"Showing ontology structure based on {self._head_ontology._ontology_file}"

        else:
            msg = f"Showing ontology structure based on {len(self._tail_ontology_meta)+1} ontologies: "

        logger.info(msg)

        if not full:
            # set of leaves and their intermediate parents up to the root
            filter_nodes = set(self.mapping.extended_schema.keys())

            for node in self.mapping.extended_schema.keys():
                filter_nodes.update(self.get_ancestors(node).nodes)

            # filter graph
            G = self._nx_graph.subgraph(filter_nodes)

        else:
            G = self._nx_graph

        if not to_disk:
            # create tree
            tree = create_tree_visualisation(G)

            # add synonym information
            for node in self.mapping.extended_schema:
                if not isinstance(self.mapping.extended_schema[node], dict):
                    continue
                if self.mapping.extended_schema[node].get("synonym_for"):
                    tree.nodes[node].tag = (
                        f"{node} = "
                        f"{self.mapping.extended_schema[node].get('synonym_for')}"
                    )

            logger.info(f"\n{tree}")

            return tree

        else:
            # convert lists/dicts to strings for vis only
            for node in G.nodes:
                # rename node and use former id as label
                label = G.nodes[node].get("label")

                if not label:
                    label = node

                G = nx.relabel_nodes(G, {node: label})
                G.nodes[label]["label"] = node

                for attrib in G.nodes[label]:
                    if type(G.nodes[label][attrib]) in [list, dict]:
                        G.nodes[label][attrib] = str(G.nodes[label][attrib])

            path = os.path.join(to_disk, "ontology_structure.graphml")

            logger.info(f"Writing ontology structure to {path}.")

            nx.write_graphml(G, path)

            return True

    def get_dict(self) -> dict:
        """
        Returns a dictionary compatible with a BioCypher node for compatibility
        with the Neo4j driver.
        """

        d = {
            "node_id": self._get_current_id(),
            "node_label": "BioCypher",
            "properties": {
                "schema": "self.ontology_mapping.extended_schema",
            },
        }

        return d

    def _get_current_id(self):
        """
        Instantiate a version ID for the current session. For now does simple
        versioning using datetime.

        Can later implement incremental versioning, versioning from
        config file, or manual specification via argument.
        """

        now = datetime.now()
        return now.strftime("v%Y%m%d-%H%M%S")
