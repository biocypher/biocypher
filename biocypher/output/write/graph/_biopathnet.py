"""Module to provide the BioPathNet writer class."""

import copy
import os
import re

import networkx as nx

from biocypher._logger import logger
from biocypher.output.write._writer import _Writer


class _BioPathNetWriter(_Writer):
    """
    Write BioCypher's property graph into a set of BioPathNet input files.

    Writes one skg and one brg for learning, validation or test as a list of lines,
    each one containing a triple.

    As BioPathNet is launched with the same entity_names and entity_types file,
    appends information in the entity_types and entity_names files. This way, these files can
    contain the information about all the entities from learning, validation and test graphs.

    To generate the needed 3 graphs (learning, validation and test) for BioPathNet,
    the biocypher's BioPathNet writer must be called 3 tymes, with the corresponding
    3 SKGs.

    If the 'include_properties' option is True, the properties of each graph of the SKG are added
    to the backgroung regulatory graph (BRG).

    If the 'tagerted_relation' option is specified (not None), only the relations that follow the
    given signature (source_type, relation_type, target_type) are added to the (main) skg.
    The other relations are added to the brg.
    If the targeted_relation is not specified (None), then all relations are added to the
    main skg. In such cases, only properties may be added to the brg, according to the
    'include_properties' option.


    """

    def __init__(
        self,
        output_directory: str | None = None,
        file_format: str = "txt",
        entity_types_file_stem: str = "entity_types",
        entity_names_file_stem: str = "entity_names",
        background_graph_file_stem: str = "brg",
        skg_file_stem: str = "skg",
        targeted_relation: str | None = None,  # "(drug, drug has target, gene)",
        include_properties: bool = True,  # False,
        **kwargs,
    ):
        super().__init__(
            output_directory=output_directory,
            file_format=file_format,
            **kwargs,
        )

        if not output_directory:
            msg = "You need to indicate an 'output_directory'."
            logger.error(msg)
            raise RuntimeError(msg)

        self.file_format = ("txt",)
        self.entity_types_file_stem = (entity_types_file_stem,)
        self.entity_names_file_stem = (entity_names_file_stem,)
        self.background_graph_file_stem = (background_graph_file_stem,)
        self.skg_file_stem = (skg_file_stem,)
        self.targeted_relation = targeted_relation
        self.include_properties = include_properties

        self.dict_entity_types = {}
        self.dict_entity_names = {}

    def _write_node_data(
        self,
        nodes,
    ) -> bool:
        """Implement how to output.write nodes to disk.

        Args:
        ----
            nodes (Iterable): An iterable of BioCypherNode / BioCypherEdge / BioCypherRelAsNode objects.

        Returns:
        -------
            bool: The return value. True for success, False otherwise.

        """
        self.dict_entity_types = {}
        self.dict_entity_names = {}
        # str_nodes_props_graph = []
        list_nodes_props_graph = []

        graph_hierarchy = copy.copy(self.translator.ontology._nx_graph.reverse())
        ancestors_set = set()

        for entity in nodes:
            entity_id = entity.get_id()
            semantic_type = entity.get_label()
            # store the semantic types of each node of the graph to be
            # written in the `entity_types.txt` file of BioPathNet
            self.dict_entity_types[entity_id] = semantic_type
            # store the labels (= ids here) of each node of the graph to be
            # written in the `entity_names.txt` file of BioPathNet
            self.dict_entity_names[entity_id] = entity_id

            if self.include_properties:
                properties = entity.get_properties()
                for key, value in properties.items():
                    # only write value if it exists.
                    if value:
                        list_nodes_props_graph.append([entity_id, key, value])

            # Add all ancestors of the entity type in the set, in order to reconstruct
            # the useful part of the ontology for passing it to BioPathNet
            # If there is no node in the graph with the semantic_type of the current node,
            # we look for nodes
            # which types are synonyms of this semantic_type.
            if not graph_hierarchy.has_node(semantic_type):
                for n, d in graph_hierarchy.nodes().items():
                    if "synonym_for" in d:
                        if d["synonym_for"] == semantic_type:
                            semantic_type = n
                            break
            ancestors = nx.ancestors(graph_hierarchy, semantic_type) | {semantic_type}
            ancestors_set.update(ancestors)

        # Reconstruct the subgraph corresponding to the usefull part of the ontology
        sub_hierarchy = graph_hierarchy.subgraph(ancestors_set)

        passed = self._write_semantic_types_and_names_in_file(self.dict_entity_types, self.dict_entity_names)
        if passed:
            passed = self._write_properties_in_file(list_nodes_props_graph)
            if passed:
                passed = self._write_hierarchy_in_file(sub_hierarchy)

        if passed:
            return True
        else:
            return False

    def _write_hierarchy_in_file(
        self,
        subgraph: nx.DiGraph,
    ) -> bool:
        """
        Writes the list of edges of the used part of the ontology T-box
        in the BRG graph file.

        For each edge of the graph, a line containing the following string:
            source is_a target
        is written.

        the entity_types and entity_names files are completed with values of all the hierarchy nodes.
        """
        file_name = os.path.join(self.output_directory, f"{self.background_graph_file_stem[0]}.{self.file_format[0]}")
        file2_name = os.path.join(self.output_directory, f"{self.entity_types_file_stem[0]}.{self.file_format[0]}")
        file3_name = os.path.join(self.output_directory, f"{self.entity_names_file_stem[0]}.{self.file_format[0]}")
        with open(file_name, "a+", encoding="utf-8") as f:
            with open(file2_name, "a+", encoding="utf-8") as f2:
                with open(file3_name, "a+", encoding="utf-8") as f3:
                    all_classes = set()
                    all_entities = set()
                    for edge in subgraph.edges():
                        source, target = edge
                        relation = "is_a"
                        str_line = "\t".join([target, relation, source])
                        f.write(str_line + "\n")
                        str_line2 = "\t".join([target, source])
                        f2.write(str_line2 + "\n")
                        str_line3 = "\t".join([target, target])
                        f3.write(str_line3 + "\n")
                        all_classes.add(source)
                        all_entities.add(target)
                    root_types = list(all_classes - all_entities)
                    for r in root_types:
                        f2.write("\t".join([r, "THING"]) + "\n")
                        f3.write("\t".join([r, r]) + "\n")

        return True

    def _write_semantic_types_and_names_in_file(
        self,
        entities_semantic_types: dict,
        entities_names: dict,
    ) -> bool:
        """
        Write the list of entities semantic types in the entity_types.txt
        file required by BioPathNet

        For each entity of the graph, a line containing the following string:
            entity_id entity_semantic_type
        is written.
        """
        file_name = os.path.join(self.output_directory, f"{self.entity_types_file_stem[0]}.{self.file_format[0]}")
        file3_name = os.path.join(self.output_directory, f"{self.entity_names_file_stem[0]}.{self.file_format[0]}")

        all_nodes = set()
        all_types = set()

        with open(file_name, "a+", encoding="utf-8") as f:
            for id, type in entities_semantic_types.items():
                line1 = "\t".join([id, type])
                f.write(line1 + "\n")
                all_nodes.add(id)
                all_nodes.add(type)
                all_types.add(type)

            with open(file3_name, "a+", encoding="utf-8") as f3:
                for id, name in entities_names.items():
                    line = "\t".join([id, name])
                    f3.write(line + "\n")
                for n in all_nodes:
                    if n not in entities_names.keys():
                        line3 = "\t".join([n, n])
                        f3.write(line3 + "\n")

        return True

    def _write_properties_in_file(
        self,
        list_list_node_props: list,
    ) -> bool:
        """
        Write the properties of each entity node as a list of triples
        in the background graph file (train1.txt by default)
        file required by BioPathNet

        For each entity of the graph, this function write one line
        for each one of its properties.
        A line contains the following string:
            entity_id property_type property_value
        """
        file_name = os.path.join(self.output_directory, f"{self.background_graph_file_stem[0]}.{self.file_format[0]}")
        file2_name = os.path.join(self.output_directory, f"{self.entity_types_file_stem[0]}.{self.file_format[0]}")
        file3_name = os.path.join(self.output_directory, f"{self.entity_names_file_stem[0]}.{self.file_format[0]}")
        with open(file_name, "a+", encoding="utf-8") as f:
            with open(file2_name, "a+", encoding="utf-8") as f2:
                with open(file3_name, "a+", encoding="utf-8") as f3:
                    for list_prop in list_list_node_props:
                        assert len(list_prop) == 3
                        entity = list_prop[0]
                        prop = list_prop[1]
                        value = list_prop[2]
                        prefixed_value = "_".join([prop, value])
                        f.write("\t".join([entity, prop, prefixed_value]) + "\n")
                        f2.write("\t".join([prefixed_value, "property_value"]) + "\n")
                        f3.write("\t".join([prefixed_value, value]) + "\n")

        return True

    def _write_edge_data(
        self,
        edges,
    ) -> bool:
        """Implement how to output.write edges to disk.

        Args:
        ----
            edges (Iterable): An iterable of BioCypherNode / BioCypherEdge / BioCypherRelAsNode objects.

        Returns:
        -------
            bool: The return value. True for success, False otherwise.

        """
        # TODO: as of now, properties on relations are not added
        # to the learning graph.
        # It would require to transform the relations into nodes,
        # and thus add a lot of nodes to the BioPathNet NN.
        # See if it is needed or not. Fix if needed
        skg_file_name = os.path.join(self.output_directory, f"{self.skg_file_stem[0]}.{self.file_format[0]}")
        with open(skg_file_name, "a", encoding="utf-8") as f_skg:
            logger.info(f"targeted_relation = {self.targeted_relation}")
            if self.targeted_relation is None or self.targeted_relation == "None":  # not self.targeted_relation[0]:
                for edge in edges:
                    source = edge.get_source_id()
                    target = edge.get_target_id()
                    relation = edge.get_label()

                    if not relation:
                        relation = "".join([source, "_", target])

                    f_skg.write("\t".join([source, relation, target]) + "\n")

            else:
                # if a signature of targeted relation is given,
                # then only the relations following this signature are added to the main skg
                # others are added to the BRG
                brg_file_name = os.path.join(
                    self.output_directory, f"{self.background_graph_file_stem[0]}.{self.file_format[0]}"
                )
                with open(brg_file_name, "a", encoding="utf-8") as f_brg:
                    exp = re.compile("((?P<source_type>[^,]+), (?P<relation_type>[^,]+), (?P<target_type>.+))")
                    match = exp.match(self.targeted_relation)
                    relation_t = match.group("relation_type")
                    # TODO: use the type of source and target nodes to filter relations
                    # NB: test all the subtypes of the targeted source and target types
                    for edge in edges:
                        source = edge.get_source_id()
                        target = edge.get_target_id()
                        relation = edge.get_label()

                        if not relation:
                            relation = "".join([source, "_", target])
                        if relation == relation_t:
                            f_skg.write("\t".join([source, relation, target]) + "\n")
                        else:
                            f_brg.write("\t".join([source, relation, target]) + "\n")
        return True

    def _get_import_script_name(self) -> str:
        """Return the name of the BioPathNet import script.

        This function is not applicable for BioPathNet.

        Returns
        -------
            str: The name of the import script (ending in .sh)

        """
        with open("noop.sh", "w"):
            pass
        return "noop.sh"

    def _construct_import_call(self) -> str:
        """Function to construct the import call detailing folder and
        individual node and edge headers and data files, as well as
        delimiters and database name. Built after all data has been
        processed to ensure that nodes are called before any edges.

        Returns
        -------
            str: command for importing the output files into a DBMS.

        """
        with open("noop.sh", "w"):
            pass
        return "noop.sh"
