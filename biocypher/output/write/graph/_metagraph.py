import os
import json
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
        keys: dict = {
            "NBINS": "nb_instances",
            "ISA": "is_a",
            "ANCESTORS": "ancestors",
            "IRI": "IRI",
        },
        property_values: str = True,
        nb_property_values: bool = True,
        nb_property_values_prefix: str = "#",
        split_separator: str = ",",
        join_separator: str = ",",
        change_property_name: dict = {
            "id": "biocypher_id",
        },
        file_format: str = "cytoscape.json",
        file_stem: str = "metagraph",
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

        logger.setLevel("DEBUG")

        # The ontology's hierarchy of types, as a NetworkX graph.
        self.taxonomy = self.translator.ontology.get_rdf_graph()

        # Do we want to use IRIs instead of RDFS:label?
        self._use_IRI = use_IRI
        logger.info(f"Write the metagraph using IRIs instead of BioCypher's labels: {use_IRI}")

        # Node label mapping: from BioCypher label to origina IRI.
        self.BC_to_IRI = {}
        # Node label mapping: from origin IRI to BioCypher label.
        self.IRI_to_BC = {}
        # Pouplate mappings with the translator's data.
        for IRI,BC in self.translator.ontology.get_renaming().items():
            logger.debug(f"{BC} == {IRI}")
            # Always serialize IRIs, which are rdflib.URIref objects.
            self.BC_to_IRI[BC] = str(IRI)
            self.IRI_to_BC[str(IRI)] = BC

        # Types of seen nodes.
        self.type_of = {}

        # The future result graph, in NetworkX.
        self.metagraph = nx.DiGraph()

        # Property names can be changed here.
        mandatory = ["NBINS","ISA","ANCESTORS","IRI"]
        if not all(k in keys for k in mandatory):
            msg = f"Default annotation names should be defined for keys: {', '.join(mandatory)}"
            logger.error(msg)
            raise RuntimeError(msg)
        self.keys = keys

        # Properties that are always attached to all elements.
        self.metaprops = {self.keys["NBINS"]: 0}

        self.property_values = property_values
        self.nb_property_values = nb_property_values
        self.nb_property_values_prefix = nb_property_values_prefix
        self.change_property_name = change_property_name

        self.split_separator = split_separator
        self.join_separator = join_separator

        available = ["cytoscape.json","dot","graphml","gefx","gml","pajek"]
        if file_format not in available:
            msg = f"The file_format: `{file_format}` is unknown, available ones: {','.join(available)}."
            logger.error(msg)
            raise RuntimeError(msg)
        self.file_format = file_format
        self.file_stem = file_stem

        # Write guards because Biocypher has `write_nodes` and `write_edges`,
        # but not `write`, so we need to ensure to call both,
        # because we output in a single file.
        self._has_nodes = False
        self._has_edges = False

        self._init_metagraph()


    def _init_metagraph(self):
        logging.debug("Add the taxonomy in the metagraph...")
        for s,p,o in self.taxonomy.triples((None, RDFS.subClassOf, None)):
            logger.debug(f"Found in taxonomy: ({s})--[{p}]->({o})")

            if str(s) not in self.IRI_to_BC:
                logger.warning(f" │ Source type `{s}` never seen in loaded ontologies or extensions, skipped.") # FIXME This should not happen.
                continue
            if str(o) not in self.IRI_to_BC:
                logger.warning(f" │ Target type `{o}` never seen in loaded ontologies or extensions, skipped.") # FIXME This should not happen.
                continue

            if self._use_IRI:
                source = str(s)
                target = str(o)
            else:
                source = self.IRI_to_BC[str(s)]
                target = self.IRI_to_BC[str(o)]

            logger.debug(f"Add to taxonomy: ({source})--[{self.keys['ISA']}]->({target})")

            source_props = copy.copy(self.metaprops)
            source_props[self.keys["IRI"]] = str(s)
            self.metagraph.add_node(source, **source_props)
            logger.debug(f" │ Source props: {source}: {self.metagraph.nodes[source]}")

            target_props = copy.copy(self.metaprops)
            target_props[self.keys["IRI"]] = str(o)
            self.metagraph.add_node(target, **target_props)
            logger.debug(f" │ Target props: {target}: {self.metagraph.nodes[target]}")

            edge_props = copy.copy(self.metaprops)
            if self._use_IRI:
                edge_props[self.keys["ISA"]] = str(p) # Generally, will be "subClassOf".
            else:
                edge_props[self.keys["IRI"]] = str(p) # Generally, will be "subClassOf".

            self.metagraph.add_edge(source, target, **edge_props)
            logger.debug(f" │ Edge props: {edge_props}")


    def _register_type(self, label):
        # If the element is unknown, then add it manually as a subclass of the root. FIXME this should not happen, the user's schema should be known!
        self.BC_to_IRI[label] = f"adhoc:{label}"
        self.IRI_to_BC[f"adhoc:{label}"] = label

        if self._use_IRI:
            s = str(self.BC_to_IRI[label])
            t = str(self.BC_to_IRI[self.translator.ontology._head_ontology._root_label])
        else:
            s = label
            t = self.translator.ontology._head_ontology._root_label

        # Log an ERROR because this should never happen.
        logger.warning(f"'Type `{label}` not found in any seen ontology or user extension, I'll register it as `{s}` attached to the root of head ontology: `{t}`") # FIXME this should not happen

        # Add the element anyway.
        self.metagraph.add_node(s, **copy.copy(self.metaprops))

        # "subclass of" link is a (meta)edge in the metagraph.
        edge_props = copy.copy(self.metaprops)
        edge_props[self.keys["ISA"]] = t
        self.metagraph.add_edge(s, t, **edge_props)


    def _add_node(self, element):
        id = element.get_id()
        label = element.get_label()
        properties = element.get_properties()

        # If the element is unknown, then add it manually as a subclass of the root. FIXME this should not happen, the user's schema should be known!
        if label not in self.BC_to_IRI:
            self._register_type(label)

        # From here, we know label is a type.
        if self._use_IRI:
            type = str(self.BC_to_IRI[label])
            logger.debug(f"{label} == {type}")
        else:
            type = label

        logger.debug(f"Add type: `{type}`")
        self.type_of[id] = type

        # Count this node type as seen.
        self.metagraph.nodes[type][self.keys["NBINS"]] += 1

        # Add the ancestors list.
        ancestor_labels = list(nx.dfs_preorder_nodes(self.metagraph, type))
        self.metagraph.nodes[type][self.keys["ANCESTORS"]] = self.join_separator.join(ancestor_labels)

        # Stats about properties
        for pname,pvalue in properties.items():
            if pname not in self.metagraph.nodes[type]:
                self.metagraph.nodes[type][pname] = set()
            for value in str(pvalue).split(self.split_separator):
                self.metagraph.nodes[type][pname].add(value.strip())


    def _add_edge(self, element):
        id = element.get_id()
        source_id = element.get_source_id()
        target_id = element.get_target_id()
        label = element.get_label()
        properties = element.get_properties()

        # If the element is unknown, then add it manually as a subclass of the root. FIXME this should not happen, the user's schema should be known!
        if label not in self.BC_to_IRI:
            self._register_type(label)

        # From here, we know label is a type.
        if self._use_IRI:
            type = str(self.BC_to_IRI[label])
            logger.debug(f"{label} == {type}")
        else:
            type = label

        logger.debug(f"Add type: `{type}`")
        # self.type_of[id] = type

        # "subclass of" link is a (meta)edge in the metagraph.
        if source_id not in self.type_of:
            logger.warning(f"Source instance `{source_id}` never seen among node instances, so I don't know its type, skipped.") # FIXME this should not happen
            return
        if target_id not in self.type_of:
            logger.warning(f"Target instance `{target_id}` never seen among node instances, so I don't know its type, skipped..") # FIXME this should not happen
            return

        s = self.type_of[source_id]
        t = self.type_of[target_id]
        if not self.metagraph.has_edge(s,t):
            logging.debug(f"Add edge between: {s} and {t}")
            edge_props = copy.copy(self.metaprops)
            # Some export engines do not allow typed edges,
            # so we add it as a metadata.
            edge_props[self.keys["ISA"]] = label
            self.metagraph.add_edge(s, t, **edge_props)

        # Count this edge type as seen.
        self.metagraph[s][t][self.keys["NBINS"]] += 1

        # Add the ancestors list.
        ancestor_labels = list(nx.dfs_preorder_nodes(self.metagraph, type))
        self.metagraph[s][t][self.keys["ANCESTORS"]] = self.join_separator.join(ancestor_labels)

        # Stats about properties
        for pname,pvalue in properties.items():
            if pname not in self.metagraph[s][t]:
                self.metagraph[s][t][pname] = set()
            for value in str(pvalue).split(self.split_separator):
                self.metagraph[s][t][pname].add(value.strip())


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
            logging.debug(f"Add node: `{n}`")
            self._add_node(n)

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
            logging.debug(f"Add edge: `{e}`")
            self._add_edge(e)

        self._has_edges = True
        return True


    def _seen_node(self, id):
        if self.metagraph.nodes[id][self.keys["NBINS"]] > 0:
            return True
        else:
            return False


    def _seen_edge(self, s, t):
        assert(self.keys["NBINS"] in self.metagraph[s][t])
        if self.metagraph[s][t][self.keys["NBINS"]] > 0:
            return True
        else:
            return False

    def _access_node(self, eid):
        nid = eid[0]
        return self.metagraph.nodes[nid]

    def _access_edge(self, eid):
        sid,tid = eid
        return self.metagraph[sid][tid]

    def _from_set_to_string(self, elements, access):
        # Transform all sets of properties into strings.
        if self.nb_property_values:
            counters = {}
        for kv in elements.data(True):
            elem = kv[0:-1]
            props = kv[-1]
            if self.nb_property_values:
                counters[elem] = {}
            for pname,pvalues in props.items():
                if type(pvalues) == set:
                    serialized = self.join_separator.join(sorted([str(i).strip() for i in pvalues]))
                    logger.debug(f"{access.__name__} '{elem}': '{pname}' = {len(pvalues)} # {pvalues} => '{serialized}'")
                    access(elem)[pname] = serialized
                    if self.nb_property_values:
                        counters[elem][f"{self.nb_property_values_prefix}{pname}"] = len(pvalues)
        if self.nb_property_values:
            # Add properties counters.
            for elem,counts in counters.items():
                access(elem).update(counts)

        for kv in elements.data(True):
            elem = kv[0:-1]
            props = kv[-1]
            for name in self.change_property_name:
                # "name" may be a reserved name
                # (e.g. "id" for Cytoscape),
                # so we take care of having one of our own.
                if name in props:
                    access(elem)[self.change_property_name[name]] = access(elem).pop(name)
                    if self.nb_property_values:
                        pname = self.nb_property_values_prefix + name
                        new_pname = self.nb_property_values_prefix + self.change_property_name[name]
                        access(elem)[new_pname] = access(elem).pop(pname)


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
            # Change all sets of unique values
            # to the related joined strings.
            self._from_set_to_string(self.metagraph.nodes, self._access_node)
            self._from_set_to_string(self.metagraph.edges, self._access_edge)

            # Filter out nodes and edges with no instances.
            seen_graph = nx.subgraph_view(self.metagraph,
                filter_node = self._seen_node,
                filter_edge = self._seen_edge,
            )

            outfname = os.path.join(self.output_directory, "{self.file_stem}.{self.file_format}")
            # NetworkX don't have a consistent export API.
            # So we have to enumerate.
            match self.file_format:
                case "cytoscape.json":
                    with open(outfname, 'w') as fd:
                        # NOTE: wait for bugfix https://github.com/networkx/networkx/issues/7913
                        data = json.dumps(nx.cytoscape_data(seen_graph))
                        fd.write(data)

                case "dot":
                    nx.drawing.nx_pydot.write_dot(seen_graph, outfname)

                case "graphml":
                    nx.write_graphml(seen_graph, outfname)

                case "gefx":
                    nx.write_gefx(seen_graph, outfname)

                case "gml":
                    nx.write_gml(seen_graph, outfname)

                case "pajek":
                    nx.write_pajek(seen_graph, outfname)

            return outfname

        elif self._has_edges and not self._has_nodes:
            msg = "_MetaGraphWriter requires that you call write_nodes BEFORE write_edges"
            logger.error(msg)
            raise RuntimeError(msg)

        else:
            msg = "_MetaGraphWriter requires that both write_nodes and write_edges are called before getting the import call."
            logger.error(msg)
            raise RuntimeError(msg)


    def _get_import_script_name(self) -> str:
        """Returns the name of the import script.

        Returns
        -------
            str: The name of the import script (ending in .sh)

        """
        return "show_in_cytoscape.sh"
