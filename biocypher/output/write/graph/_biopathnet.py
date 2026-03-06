"""Module to provide the BioPathNet writer class."""

import os

import copy
import networkx as nx

from biocypher._logger import logger
from biocypher.output.write._writer import _Writer


class _BioPathNetWriter(_Writer):
    """
    Write BioCypher's property graph into a set of BioPathNet input files.

    Writes one skg for learning, validation or test as a list of lines each containing a triple.
    As BioPathNet is launched with the same entity_names and entity_types file,
    appends information in the entity_types and entity_names files. This way, these files can
    contain the information about all the entities from learning, validation and test graphs.
    """

    def __init__(
        self,
        output_directory: str | None = None,
        file_format: str = "txt",
        entity_types_file_stem: str = "entity_types",
        entity_names_file_stem: str = "entity_names",
        background_graph_file_stem: str = "brg",
#        learning_graph_file_stem: str = "train2",
        skg_file_stem: str = "skg",
        **kwargs,
    ):
        super().__init__(
            output_directory=output_directory,
            file_format=file_format,
            **kwargs,
        )

        if not output_directory:
            msg = "You need to indicate a 'output_directory'."
            logger.error(msg)
            raise RuntimeError(msg)

        self.file_format = "txt",
        self.entity_types_file_stem = entity_types_file_stem,
        self.entity_names_file_stem = entity_names_file_stem,
        self.background_graph_file_stem = background_graph_file_stem,
        self.skg_file_stem= skg_file_stem,

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
        dict_entity_types = {}
        str_nodes_props_graph = []

        graph_hierarchy = copy.copy(self.translator.ontology._head_ontology.get_nx_graph()).reverse()
        logger.debug(f"type(graph_hierarchy) = {type(graph_hierarchy)}")
        logger.debug(f"graph_hierarchy = {graph_hierarchy.nodes()}")
        ancestors_set = set()

        # all_types = set()

        for entity in nodes:
            semantic_type = entity.get_type()
            # all_types.add(semantic_type)
            entity_id = entity.get_id()
            # store the sematic types of each node of the graph to be
            # written in the entity_tyes.txt file of BioPathNet
            if entity_id not in dict_entity_types.keys():
                dict_entity_types[entity_id] = semantic_type

            properties = entity.get_properties()
            for key, value in properties.items():
                # only write value if it exists.
                if value:
                    str_nodes_props_graph.append("\t".join([entity_id, key, str(value)]))

            # Add all ancestors of the entity type in the set, in order to reconstruct
            # the useful part of the ontology for passing it to BioPathNet
            ancestors = nx.ancestors(graph_hierarchy, semantic_type )|{semantic_type}
            logger.debug(f"Adding the type : {semantic_type}")
            logger.debug(f"Ancestors : {ancestors}")
            ancestors_set.update(ancestors)

        # Reconstruct the subgraph corresponding to the usefull part of the ontology
        logger.debug(f"ancestors_set : {ancestors_set}")
        sub_hierarchy = graph_hierarchy.subgraph(ancestors_set)

        # Look for instances of all used types that are not in the graph,
        # to add them in the entity_types files, in order to use them for negative sampling
        # graph = copy.copy(self.translator.ontology._head_ontology.get_nx_graph())
        # for t in all_types:
        #     logger.info("t=", t, type(t))
        #     instances = graph.predecessors(t)
        #     for i in instances:
        #         logger.info("instance=", i, type(i))
        #         if i not in dict_entity_types.keys():
        #             dict_entity_types[i] = type
                    

        passed = self._write_semantic_types_in_file(dict_entity_types)
        if passed:
            passed = self._write_properties_in_file(str_nodes_props_graph)
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
        file_name = os.path.join(self.output_directory,
                                 f"{self.background_graph_file_stem[0]}.{self.file_format[0]}")
        file2_name = os.path.join(self.output_directory,
                                 f"{self.entity_types_file_stem[0]}.{self.file_format[0]}")
        file3_name = os.path.join(self.output_directory,
                                 f"{self.entity_names_file_stem[0]}.{self.file_format[0]}")
        with open(file_name, 'a+', encoding='utf-8') as f:
            with open(file2_name, 'a+', encoding='utf-8') as f2:
                with open(file3_name, 'a+', encoding='utf-8') as f3:
                    logger.debug(f"subgraph = {subgraph}")
                    logger.debug(f"subgraph.edges() = {subgraph.edges()}")
                    all_classes = set()
                    all_entities = set()
                    for edge in subgraph.edges():
                        source, target = edge
                        relation = "is_a"
                        str_line = "\t".join([target, relation, source])
                        f.write(str_line+'\n')
                        str_line2 = "\t".join([target, source])
                        f2.write(str_line2+'\n')
                        str_line3 = "\t".join([target, target])
                        f3.write(str_line3+'\n')
                        all_classes.add(source)
                        all_entities.add(target)
                    root_type = list(all_classes-all_entities)[0]
                    f2.write("\t".join([root_type, "THING"])+'\n')
                    f3.write("\t".join([root_type, root_type])+'\n')
                

        return True





    def _write_semantic_types_in_file(
        self,
        entities_semantic_types: dict,
    ) -> bool:
        """
        Write the list of entities semantic types in the entity_types.txt
        file required by BioPathNet

        For each entity of the graph, a line containing the following string:
            entity_id entity_semantic_type
        is written.
        """
        file_name = os.path.join(self.output_directory,
                                 f"{self.entity_types_file_stem[0]}.{self.file_format[0]}")
        file2_name = os.path.join(self.output_directory,
                                 f"{self.skg_file_stem[0]}.{self.file_format[0]}")
        file3_name = os.path.join(self.output_directory,
                                 f"{self.entity_names_file_stem[0]}.{self.file_format[0]}")
        logger.debug(f"In _biopathnet.py, output_directory = {self.output_directory}")
        logger.debug(f"In _biopathnet.py, entity_types_file_stem = {self.entity_types_file_stem}")
        logger.debug(f"In _biopathnet.py, file_format= {self.file_format}")
        logger.debug(f"In _biopathnet.py, filename = {file_name}")

        all_nodes = set()
        
        with open(file_name, 'a+', encoding='utf-8') as f:
            with open(file2_name, 'a+', encoding='utf-8') as f2:
                with open(file3_name, 'a+', encoding='utf-8') as f3:
                    for id, type in entities_semantic_types.items():
                        line1 = "\t".join([id, type])
                        f.write(line1+'\n')
                        # FIXME commented for now,
                        # to write all the type hierarchy in the BGR,
                        # but we should add an option to choose wether
                        # to write the hierarchy in the BGR or in the
                        # learning graph. 
                        # line2 = "\t".join([id, "is_a", type])
                        # f2.write(line2+'\n')
                        all_nodes.add(id)
                        all_nodes.add(type)
                    for n in all_nodes:
                        line3 = "\t".join([n, n])
                        f3.write(line3+'\n')

        return True

    def _write_properties_in_file(
        self,
        list_str_node_props: list,
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
        file_name = os.path.join(self.output_directory,
                                 f"{self.background_graph_file_stem[0]}.{self.file_format[0]}")
        file2_name = os.path.join(self.output_directory,
                                 f"{self.entity_types_file_stem[0]}.{self.file_format[0]}")
        file3_name = os.path.join(self.output_directory,
                                 f"{self.entity_names_file_stem[0]}.{self.file_format[0]}")
        with open(file_name, 'a+', encoding='utf-8') as f:
            with open(file2_name, 'a+', encoding='utf-8') as f2:
                with open(file3_name, 'a+', encoding='utf-8') as f3:
                    for str_prop in list_str_node_props:
                        entity, prop, value = str_prop.strip().split()
                        prefixed_value = "_".join([prop, value])
                        f.write("\t".join([entity, prop, prefixed_value])+'\n')
                        f2.write("\t".join([prefixed_value, "property_value"])+'\n')
                        f3.write("\t".join([prefixed_value, value])+'\n')
                        

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
        # FIXME : as of now, properties on relations are not added
        # to the learning graph.
        # It would require to transform the relations into nodes,
        # and thus add a lot of nodes to the BioPatNet NN.
        # See if it is needed or not. Fix if needed
        file_name = os.path.join(self.output_directory,
                                 f"{self.skg_file_stem[0]}.{self.file_format[0]}")
        with open(file_name, 'a', encoding='utf-8') as f:
            for edge in edges:
                source = edge.get_source_id()
                target = edge.get_target_id()
                relation = edge.get_label()
                #relation_properties = edge.get_properties()

                if relation is None:
                    relation = "".join([source, "_", target])

                f.write("\t".join([source, relation, target])+'\n')
        return True

    def _get_import_script_name(self) -> str:
        """Return the name of the BioPathNet import script.

        This function is not applicable for BioPathNet.

        Returns
        -------
            str: The name of the import script (ending in .sh)

        """
        return "noop.sh"

    def _construct_import_call(self) -> str:
        """Write the import call.

        This function is not applicable for BioPathNet.

        Returns
        -------
            bool: The return value. True for success, False otherwise.

        """
        return "# TODO?"
