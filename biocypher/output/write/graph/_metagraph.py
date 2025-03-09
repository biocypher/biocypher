import copy
import logging
from rdflib import RDFS
import networkx as nx
from biocypher.output.write._writer import _Writer

logger = logging.getLogger()

class _MetaGraphWriter(_Writer):
    """Dumps schema as a graph with statistics as properties.
    """

    def __init__(
        self,
        translator,#: Translator,
        deduplicator,#: Deduplicator,
        output_directory: str | None = None,
        strict_mode: bool = False,
        use_IRI: bool = False,
        *args,
        **kwargs,
    ):
        """Abstract class for writing node and edge representations to disk.

        Args:
        ----
            translator (Translator): Instance of :py:class:`Translator` to enable translation of
                nodes and manipulation of properties.
            deduplicator (Deduplicator): Instance of :py:class:`Deduplicator` to enable deduplication
                of nodes and edges.
            output_directory (str, optional): Path for exporting CSV files. Defaults to None.
            strict_mode (bool, optional): Whether to enforce source, version, and license properties. Defaults to False.

        """
        super().__init__(
            translator,
            deduplicator,
            output_directory,
            strict_mode,
            *args,
            **kwargs,
        )
        self.taxonomy = self.translator.ontology.get_rdf_graph()

        self._use_IRI = use_IRI

        # Reverse name mapping.
        self.BC_to_IRI = {}
        self.IRI_to_BC = {}
        for IRI,BC in self.translator.ontology.get_renaming().items():
            logger.debug(f"{BC} == {IRI}")
            self.BC_to_IRI[BC] = str(IRI)
            self.IRI_to_BC[str(IRI)] = BC

        self.metagraph = nx.DiGraph()

        # Property names.
        self.keys = {
            "NBINS": "nb_instances",
            "ISA": "subClassOf",
        }

        self.metaprops = {
            self.keys["NBINS"]: 0,
        }

        # Write guards because Biocypher has `write_nodes` and `write_edges`,
        # but not `write`, so we need to ensure to call both.
        self._has_nodes = False
        self._has_edges = False


        self._init_metagraph()


    def _init_metagraph(self):
        # Add the taxonomy in the metagraph.
        for s,p,o in self.taxonomy.triples((None, RDFS.subClassOf, None)):
            logger.debug(f"({s})--[{p}]->({o})")

            if str(s) not in self.IRI_to_BC:
                logger.error(f"{s} never seen in loaded ontologies or extensions, skipped.")
                continue
            if str(o) not in self.IRI_to_BC:
                logger.error(f"{o} never seen in loaded ontologies or extensions, skipped.")
                continue

            if self._use_IRI:
                source = str(s)
                target = str(o)
            else:
                 source = self.IRI_to_BC[str(s)]
                 target = self.IRI_to_BC[str(o)]

            logger.debug(f"({source})--[{self.keys['ISA']}]->({target})")

            self.metagraph.add_node(source, **copy.copy(self.metaprops))

            self.metagraph.add_node(target, **copy.copy(self.metaprops))

            edge_props = copy.copy(self.metaprops)
            if self._use_IRI:
                edge_props[self.keys["ISA"]] = str(p)
            self.metagraph.add_edge(source, target, **edge_props)

    def _add_element(self, element):
        id = element.get_id()
        # properties = element.get_properties() TODO properties stats
        label = element.get_label()
        if label not in self.BC_to_IRI:
            self.BC_to_IRI[label] = f"adhoc:{label}"
            self.IRI_to_BC[f"adhoc:{label}"] = label

            if self._use_IRI:
                s = str(self.BC_to_IRI[label])
                o = str(self.BC_to_IRI[self.translator.ontology._head_ontology._root_label])
            else:
                s = label
                o = self.translator.ontology._head_ontology._root_label

            logger.error(f"'{label}' not found in any seen ontology or user extension, I'll register it as '{s}' attached to the root of head ontology: '{o}'")

            self.metagraph.add_node(s, **copy.copy(self.metaprops))

            edge_props = copy.copy(self.metaprops)
            edge_props[self.keys["ISA"]] = o
            self.metagraph.add_edge(s, o, **edge_props)

        # From here, we know label is a type.
        if self._use_IRI:
            type = str(self.BC_to_IRI[label])
            logger.debug(f"{label} == {type}")
        else:
            type = label

        # Count this use for all ancestor types.
        ancestor_labels = nx.dfs_preorder_nodes(self.metagraph, type)

        for label in ancestor_labels:
            self.metagraph.nodes[type][self.keys["NBINS"]] += 1


    def _write_node_data(
        self,
        nodes,#: Iterable[BioCypherNode | BioCypherEdge | BioCypherRelAsNode],
    ) -> bool:
        """Implement how to output.write nodes to disk.

        Args:
        ----
            nodes (Iterable): An iterable of BioCypherNode / BioCypherEdge / BioCypherRelAsNode objects.

        Returns:
        -------
            bool: The return value. True for success, False otherwise.

        """
        logger.debug("NODES...")
        for n in nodes:
            self._add_element(n)

        self._has_nodes = True
        return True

    def _write_edge_data(
        self,
        edges,#: Iterable[BioCypherNode | BioCypherEdge | BioCypherRelAsNode],
    ) -> bool:
        """Implement how to output.write edges to disk.

        Args:
        ----
            edges (Iterable): An iterable of BioCypherNode / BioCypherEdge / BioCypherRelAsNode objects.

        Returns:
        -------
            bool: The return value. True for success, False otherwise.

        """
        logger.debug("EDGES...")
        for e in edges:
            self._add_element(e)

        self._has_edges = True
        return True

    def _construct_import_call(self) -> str:
        """Function to construct the import call detailing folder and
        individual node and edge headers and data files, as well as
        delimiters and database name. Built after all data has been
        processed to ensure that nodes are called before any edges.

        Returns
        -------
            str: command for importing the output files into a DBMS.

        """
        if self._has_nodes and self._has_edges:
            nx.write_graphml(self.metagraph, "metagraph.gml")
            logger.debug(nx.to_dict_of_dicts(self.metagraph))

    def _get_import_script_name(self) -> str:
        """Returns the name of the import script.

        Returns
        -------
            str: The name of the import script (ending in .sh)

        """
        return "metagraph.gml"
