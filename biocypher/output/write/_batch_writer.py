"""Abstract base class for all batch writers."""

import glob
import os
import re

from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from collections.abc import Iterable

import networkx

from biocypher._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode
from biocypher._deduplicate import Deduplicator
from biocypher._logger import logger
from biocypher._translate import Translator
from biocypher.output.write._writer import _Writer


class _BatchWriter(_Writer, ABC):
    """Abstract batch writer class."""

    @abstractmethod
    def _quote_string(self, value: str) -> str:
        """Quote a string.

        Escaping is handled by the database-specific writer.
        """
        msg = "Database writer must override '_quote_string'"
        logger.error(msg)
        raise NotImplementedError(msg)

    @abstractmethod
    def _get_default_import_call_bin_prefix(self):
        """Provide the default string for the import call bin prefix.

        Returns
        -------
            str: The database-specific string for the path to the import call bin prefix

        """
        msg = "Database writer must override '_get_default_import_call_bin_prefix'"
        logger.error(msg)
        raise NotImplementedError(msg)

    @abstractmethod
    def _write_array_string(self, string_list):
        """Write the string representation of an array into a .csv file.

        Different databases require different formats of array to optimize
        import speed.

        Args:
        ----
            string_list (list): list of ontology strings

        Returns:
        -------
            str: The database-specific string representation of an array

        """
        msg = "Database writer must override '_write_array_string'"
        logger.error(msg)
        raise NotImplementedError(msg)

    @abstractmethod
    def _write_node_headers(self):
        """Write header files for nodes.

        Write header files (node properties) for nodes as per the
        definition in the `schema_config.yaml`.

        Returns
        -------
            bool: The return value. True for success, False otherwise.

        """
        msg = "Database writer must override '_write_node_headers'"
        logger.error(msg)
        raise NotImplementedError(msg)

    @abstractmethod
    def _write_edge_headers(self):
        """Write a database import-file for an edge.

        Write a database import-file for an edge as per the definition in
        the `schema_config.yaml`, containing only the header for this type
        of edge.

        Returns
        -------
            bool: The return value. True for success, False otherwise.

        """
        msg = "Database writer must override '_write_edge_headers'"
        logger.error(msg)
        raise NotImplementedError(msg)

    @abstractmethod
    def _construct_import_call(self) -> str:
        """Construct the import call.

        Construct the import call detailing folder and individual node and
        edge headers and data files, as well as delimiters and database name.
        Built after all data has been processed to ensure that nodes are
        called before any edges.

        Returns
        -------
            str: A bash command for csv import.

        """
        msg = "Database writer must override '_construct_import_call'"
        logger.error(msg)
        raise NotImplementedError(msg)

    @abstractmethod
    def _get_import_script_name(self) -> str:
        """Return the name of the import script.

        The name will be chosen based on the used database.

        Returns
        -------
            str: The name of the import script (ending in .sh)

        """
        msg = "Database writer must override '_get_import_script_name'"
        logger.error(msg)
        raise NotImplementedError(msg)

    def __init__(
        self,
        translator: "Translator",
        deduplicator: "Deduplicator",
        delimiter: str,
        array_delimiter: str = ",",
        quote: str = '"',
        output_directory: str | None = None,
        db_name: str = "neo4j",
        import_call_bin_prefix: str | None = None,
        import_call_file_prefix: str | None = None,
        wipe: bool = True,
        strict_mode: bool = False,
        skip_bad_relationships: bool = False,
        skip_duplicate_nodes: bool = False,
        db_user: str = None,
        db_password: str = None,
        db_host: str = None,
        db_port: str = None,
        file_format: str = None,
        rdf_namespaces: dict = {},
        labels_order: str = "Ascending",
        node_labels_order: str = "Ascending",
        edge_labels_order: str = "Ascending",
        **kwargs,
    ):
        """Write node and edge representations to disk.

        Abstract parent class for writing node and edge representations to disk
        using the format specified by each database type. The database-specific
        functions are implemented by the respective child-classes. This abstract
        class contains all methods expected by a bach writer instance, some of
        which need to be overwritten by the child classes.

        Each batch writer instance has a fixed representation that needs to be
        passed at instantiation via the `schema` argument. The instance
        also expects an ontology adapter via `ontology_adapter` to be
        able to convert and extend the hierarchy.

        Requires the following methods to be overwritten by database-specific
        writer classes:

            - _write_node_headers
            - _write_edge_headers
            - _construct_import_call
            - _write_array_string
            - _get_import_script_name

        Args:
        ----
            translator:
                Instance of :py:class:`Translator` to enable translation of
                nodes and manipulation of properties.

            deduplicator:
                Instance of :py:class:`Deduplicator` to enable deduplication
                of nodes and edges.

            delimiter:
                The delimiter to use for the CSV files.

            array_delimiter:
                The delimiter to use for array properties.

            quote:
                The quote character to use for the CSV files.

            output_directory:
                Path for exporting CSV files.

            db_name:
                Name of the database that will be used in the generated
                commands.

            import_call_bin_prefix:
                Path prefix for the admin import call binary.

            import_call_file_prefix:
                Path prefix for the data files (headers and parts) in the import
                call.

            wipe:
                Whether to force import (removing existing DB content).
                    (Specific to Neo4j.)

            strict_mode:
                Whether to enforce source, version, and license properties.

            skip_bad_relationships:
                Whether to skip relationships that do not have a valid
                start and end node. (Specific to Neo4j.)

            skip_duplicate_nodes:
                Whether to skip duplicate nodes. (Specific to Neo4j.)

            db_user:
                The database user.

            db_password:
                The database password.

            db_host:
                The database host. Defaults to localhost.

            db_port:
                The database port.

            file_format:
                The format of RDF.

            rdf_namespaces:
                The namespaces for RDF.

            labels_order:
                The order of node and edges labels, reflecting the types of ancestors in the taxonomy.
                Options are:
                    * "Ascending": From more specific to more generic (the default).
                    * "Descending": From more generic to more specific.
                    * "Alphabetical": Alphabetically. Legacy option.
                    * "Leaves": Only the most specific label.

            node_labels_order:
                The order of node labels, reflecting the types of ancestors in the taxonomy.
                Options are:
                    * "None": Use labels_order (the default).
                    * "Ascending": From more specific to more generic.
                    * "Descending": From more generic to more specific.
                    * "Alphabetical": Alphabetically. Legacy option.
                    * "Leaves": Only the most specific label.

            edge_labels_order:
                The order of edge labels, reflecting the types of ancestors in the taxonomy.
                Options are:
                    * "None": Use labels_order (the default).
                    * "Ascending": From more specific to more generic.
                    * "Descending": From more generic to more specific.
                    * "Alphabetical": Alphabetically. Legacy option.
                    * "Leaves": Only the most specific label.

        """
        super().__init__(
            translator=translator,
            deduplicator=deduplicator,
            output_directory=output_directory,
            strict_mode=strict_mode,
        )
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host or "localhost"
        self.db_port = db_port
        self.file_format = file_format
        self.rdf_namespaces = rdf_namespaces

        self.delim, self.escaped_delim = self._process_delimiter(delimiter)
        self.adelim, self.escaped_adelim = self._process_delimiter(array_delimiter)
        self.quote = quote
        self.skip_bad_relationships = skip_bad_relationships
        self.skip_duplicate_nodes = skip_duplicate_nodes

        if import_call_bin_prefix is None:
            self.import_call_bin_prefix = self._get_default_import_call_bin_prefix()
        else:
            self.import_call_bin_prefix = import_call_bin_prefix

        self.wipe = wipe
        self.strict_mode = strict_mode

        self.translator = translator
        self.deduplicator = deduplicator
        self.node_property_dict = {}
        self.edge_property_dict = {}
        self.import_call_nodes = set()
        self.import_call_edges = set()

        self.outdir = output_directory

        self._import_call_file_prefix = import_call_file_prefix

        self.parts = {}  # dict to store the paths of part files for each label

        # map of node label -> {property signature: group key}. Nodes of a
        # label that present different property sets (e.g. schemaless input
        # with optional properties) are split into separate output groups so
        # that each part file conforms to its own header. The first signature
        # encountered keeps the plain label as its group key (i.e. legacy file
        # names and import call); further signatures get a suffixed key.
        self._node_property_groups = defaultdict(dict)

        self._labels_orders = ["Alphabetical", "Ascending", "Descending", "Leaves", "None"]
        self.labels_order = labels_order
        self.node_labels_order = node_labels_order
        self.edge_labels_order = edge_labels_order
        self._check_labels_order()

        # TODO not memory efficient, but should be fine for most cases; is
        # there a more elegant solution?

    def _check_labels_order(self):
        # Check for legit values.
        for order in ["labels_order", "node_labels_order", "edge_labels_order"]:
            if getattr(self, order) is None:
                msg = (
                    f"A batch writer `{order}` parameter must be set, "
                    f"it must be one of: {', '.join(self._labels_orders)}.",
                )
                logger.error(msg)
                raise ValueError(msg)

            if getattr(self, order) not in self._labels_orders:
                msg = (
                    f"A batch writer `{order}` parameter cannot be `{getattr(self, order)}`, "
                    f"it must be one of: {', '.join(self._labels_orders)}.",
                )
                logger.error(msg)
                raise ValueError(msg)

        # Check consistency of the triplet.
        # *_labels_order are the real parameters,
        # labels_order is just a shortcut to set the two others.
        if self.labels_order == "None" and (self.node_labels_order == "None" or self.edge_labels_order == "None"):
            msg = (
                "You have to set either `labels_order` or "
                "both `node_labels_order` and `edge_labels_order`."
                "Current setting:\n"
                f"- labels_order = `{self.labels_order}`\n"
                f"- node_labels_order = `{self.node_labels_order}`\n"
                f"- edge_labels_order = `{self.edge_labels_order}`\n"
            )
            logger.error(msg)
            raise ValueError(msg)

        if self.labels_order != "None":
            if self.edge_labels_order != self.labels_order or self.node_labels_order != self.labels_order:
                msg = (
                    f"`labels_order`=`{self.labels_order}` "
                    "superseded by either "
                    f"`node_labels_order`=`{self.node_labels_order}` "
                    f"or `edge_labels_order`=`{self.edge_labels_order}`."
                )
                logger.info(msg)

            if self.node_labels_order == "None":
                msg = f"`node_labels_order` set to `labels_order`=`{self.labels_order}`."
                self.node_labels_order = self.labels_order
                logger.info(msg)

            if self.edge_labels_order == "None":
                msg = f"`node_labels_order` set to `labels_order`=`{self.labels_order}`."
                self.edge_labels_order = self.labels_order
                logger.info(msg)

        assert self.node_labels_order != "None", "node_labels_order must be set"
        assert self.edge_labels_order != "None", "edge_labels_order must be set"

    @property
    def import_call_file_prefix(self):
        """Property for output directory path."""
        if self._import_call_file_prefix is None:
            return self.outdir
        return self._import_call_file_prefix

    def _process_delimiter(self, delimiter: str) -> str:
        """Process a delimited to escape correctly.

        Args:
        ----
            delimiter (str): The delimiter to process.

        Returns:
        -------
            tuple: The delimiter and its escaped representation.

        """
        if delimiter == "\\t":
            return "\t", "\\t"

        return delimiter, delimiter

    def write_nodes(self, nodes, batch_size: int = int(1e6), force: bool = False):
        """Write nodes and their headers.

        Args:
        ----
            nodes (BioCypherNode): an iterable of nodes in
                :py:class:`BioCypherNode` format

            batch_size (int): The batch size for writing nodes.

            force (bool): Whether to force writing nodes even if their type is
                not present in the schema.


        Returns:
        -------
            bool: The return value. True for success, False otherwise.

        """
        # TODO check represented_as

        # write node data
        passed = self._write_node_data(nodes, batch_size, force)
        if not passed:
            logger.error("Error while writing node data.")
            return False
        # pass property data to header writer per node type written
        passed = self._write_node_headers()
        if not passed:
            logger.error("Error while writing node headers.")
            return False

        return True

    def write_edges(
        self,
        edges: Iterable,
        batch_size: int = int(1e6),
    ) -> bool:
        """Write edges and their headers.

        Args:
        ----
            edges (BioCypherEdge): an iterable of edges in
                :py:class:`BioCypherEdge` or :py:class:`BioCypherRelAsNode`
                format

        Returns:
        -------
            bool: The return value. True for success, False otherwise.

        """
        passed = True
        empty = True
        has_node = False

        consume_nodes, flush_nodes = self._create_write_node_data_handlers(batch_size)
        consume_edges, flush_edges = self._create_write_edge_data_handlers(batch_size)
        for edge in edges:
            empty = False
            if isinstance(edge, BioCypherRelAsNode):
                # check if relationship has already been written, if so skip
                if self.deduplicator.rel_as_node_seen(edge):
                    continue

                passed = (
                    consume_nodes(edge.get_node())
                    and consume_edges(edge.get_source_edge())
                    and consume_edges(edge.get_target_edge())
                )
                if not passed:
                    break

                has_node = True
            else:
                # check if relationship has already been written, if so skip
                if self.deduplicator.edge_seen(edge):
                    continue

                passed = consume_edges(edge)
                if not passed:
                    break

        passed = passed and flush_nodes() and flush_edges()

        if empty:
            logger.debug(
                "No edges to write, possibly due to no matched Biolink classes.",
            )

        if not passed:
            logger.error("Error while writing edge data.")
            return False

        if has_node:
            # pass property data to header writer per node type written
            passed = self._write_node_headers()
            if not passed:
                logger.error("Error while writing node headers.")
                return False

        # pass property data to header writer per edge type written
        passed = self._write_edge_headers()
        if not passed:
            logger.error("Error while writing edge headers.")
            return False

        return True

    def _get_all_labels(self, label, labels_order, force: bool = False):
        all_labels = {}
        # get label hierarchy
        # multiple labels:
        if not force:
            # If the type label is not in the taxonomy
            # (i.e. it has been set with `label_as_edge`).
            # FIXME deprecate label_as_edge.
            try:
                all_labels = self.translator.ontology.get_ancestors(label)
            except networkx.exception.NetworkXError:
                # There's no ancestor.
                all_labels = [label]
        else:
            all_labels = None

        if all_labels:
            # convert to pascal case
            all_labels = [self.translator.name_sentence_to_pascal(label) for label in all_labels]
            # remove duplicates
            all_labels = list(OrderedDict.fromkeys(all_labels))
            match labels_order:
                case "Ascending":
                    pass  # Default from get_ancestors.
                case "Alphabetical":
                    all_labels.sort()
                case "Descending":
                    all_labels.reverse()
                case "Leaves":
                    if len(all_labels) < 1:
                        msg = "Labels list cannot be empty when using 'Leaves' order."
                        raise ValueError(msg)
                    all_labels = [all_labels[0]]
                case _:
                    # In case someone touched _label_orders after constructor.
                    if labels_order not in self._labels_orders:
                        msg = f"Invalid labels_order: {labels_order}. Must be one of {self._labels_orders}"
                        raise ValueError(msg)
            # concatenate with array delimiters
            all_labels = self._write_array_string(all_labels)
        else:
            all_labels = self.translator.name_sentence_to_pascal(label)

        return all_labels

    def _get_node_property_types(self, node, label: str) -> dict:
        """Determine the property names and types of a single node.

        Properties are taken from the schema configuration if the label is
        configured, otherwise they are inferred from the node itself
        (schemaless input). The returned dict maps property name to a type
        string and is used both to build the CSV header and to assign the node
        to a property-signature group.

        Args:
        ----
            node: the BioCypherNode to inspect

            label (str): the primary (ontology) label of the node

        Returns:
        -------
            dict: property name -> type string

        """
        # get properties from config if present
        if label in self.translator.ontology.mapping.extended_schema:
            cprops = self.translator.ontology.mapping.extended_schema.get(label).get(
                "properties",
            )
        else:
            cprops = None

        if cprops:
            d = dict(cprops)

            # add id and preferred id to properties; these are
            # created in node creation (`_create.BioCypherNode`)
            d["id"] = "str"
            d["preferred_id"] = "str"

            # add strict mode properties
            if self.strict_mode:
                d["source"] = "str"
                d["version"] = "str"
                d["licence"] = "str"

        else:
            d = dict(node.get_properties())
            # encode property type
            for k, v in d.items():
                if v is not None:
                    if isinstance(v, list):
                        elem_type = type(v[0]).__name__ if v else "str"
                        d[k] = f"{elem_type}[]"
                    else:
                        d[k] = type(v).__name__

        return d

    def _get_node_group_key(self, label: str, prop_dict: dict) -> str:
        """Assign a node to an output group based on its property signature.

        Nodes that share the same set of properties and types are written to
        the same group (header + part files + import call entry). The first
        signature seen for a label keeps the plain label as its key, so the
        common case (schema-configured or homogeneous data) is unchanged and
        produces the same single header as before. Additional signatures get a
        distinct, file-name-safe suffix.

        Args:
        ----
            label (str): the primary (ontology) label of the node

            prop_dict (dict): property name -> type string for the node

        Returns:
        -------
            str: the group key to use for buffering, file naming and headers

        """
        # order-invariant, type-aware signature
        signature = tuple(sorted(prop_dict.items()))
        groups = self._node_property_groups[label]

        if signature not in groups:
            # first signature keeps the legacy label (and thus legacy file
            # names); subsequent signatures are suffixed
            groups[signature] = label if not groups else f"{label} group{len(groups)}"

        return groups[signature]

    def _write_node_data(self, nodes, batch_size, force: bool = False):
        """Write biocypher nodes to CSV.

        Conforms to the headers created with `_write_node_headers()`, and
        is actually required to be run before calling `_write_node_headers()`
        to set the :py:attr:`self.node_property_dict` for passing the node
        properties to the instance. Expects list or generator of nodes from
        the :py:class:`BioCypherNode` class.

        Args:
        ----
            nodes (BioCypherNode): an iterable of nodes in
                :py:class:`BioCypherNode` format

            batch_size (int): The number of nodes per type to buffer before
                flushing a CSV part file.

            force (bool): Whether to bypass ontology lookups for labels while
                writing node labels.

        Returns:
        -------
            bool: The return value. True for success, False otherwise.

        """
        if not isinstance(nodes, Iterable):
            logger.error("Nodes must be passed as an iterable.")
            return False

        consume, flush = self._create_write_node_data_handlers(batch_size, force)
        for node in nodes:
            if not consume(node):
                return False
        return flush()

    def _create_write_node_data_handlers(self, batch_size, force: bool = False):
        """Create node-writing closures for streamed input.

        The returned `consume` closure consumes one
        :py:class:`BioCypherNode` at a time and flushes full batches to disk.
        The returned `flush` closure writes remaining buffered nodes and stores
        discovered node properties in :py:attr:`self.node_property_dict`.

        Args:
        ----
            batch_size (int): The number of nodes per type to buffer before
                writing a part file.

            force (bool): Whether to bypass ontology lookups for labels while
                writing node labels.

        Returns:
        -------
            tuple[Callable, Callable]: `(consume, flush)` where `consume`
                processes one node and `flush` writes all remaining buffers.

        """
        empty = True
        bins = defaultdict(list)  # dict to store a list for each
        # label that is passed in
        bin_l = {}  # dict to store the length of each list for
        # batching cutoff
        reference_props = defaultdict(
            dict,
        )  # dict to store a dict of properties
        # for each label to check for consistency and their type
        # for now, relevant for `int`
        labels = {}  # dict to store the additional labels for each

        # primary graph constituent from biolink hierarchy
        def consume(node):
            nonlocal empty
            if empty:
                logger.debug("Writing node CSV from generator.")
                empty = False

            # check if node has already been written, if so skip
            if self.deduplicator.node_seen(node):
                return True

            _id = node.get_id()
            label = node.get_label()

            # check for non-id
            if not _id:
                logger.warning(f"Node {label} has no id; skipping.")
                return True

            # determine the node's property types and route it to the output
            # group for its property signature. Schema-configured or otherwise
            # homogeneous data yields a single group per label (identical to
            # the previous behaviour); schemaless data with varying property
            # sets is split into one group per distinct set, so each part file
            # conforms to its own header instead of raising a mismatch error.
            d = self._get_node_property_types(node, label)
            gkey = self._get_node_group_key(label, d)

            if gkey not in bins:
                # start new list for this group
                bins[gkey].append(node)
                bin_l[gkey] = 1

                reference_props[gkey] = d
                labels[gkey] = self._get_all_labels(label, self.node_labels_order, force)

            else:
                # add to list
                bins[gkey].append(node)
                bin_l[gkey] += 1
                if not bin_l[gkey] < batch_size:
                    # batch size controlled here
                    passed = self._write_single_node_list_to_file(
                        bins[gkey],
                        gkey,
                        reference_props[gkey],
                        labels[gkey],
                    )

                    if not passed:
                        return False

                    bins[gkey] = []
                    bin_l[gkey] = 0

            return True

        def flush():
            nonlocal empty
            if empty:
                return True

            # after generator depleted, write remainder of bins (keyed by
            # property-signature group, see consume())
            for gkey, nl in bins.items():
                passed = self._write_single_node_list_to_file(
                    nl,
                    gkey,
                    reference_props[gkey],
                    labels[gkey],
                )

                if not passed:
                    return False

            # one header per group; groups with varying property sets were
            # already separated in consume(), so each header matches its parts
            for gkey in reference_props:
                self.node_property_dict[gkey] = reference_props[gkey]

            return True

        return consume, flush

    def _write_single_node_list_to_file(
        self,
        node_list: list,
        label: str,
        prop_dict: dict,
        labels: str,
    ):
        """Write a list of biocypher nodes to a CSV file.

        This function takes one list of biocypher nodes and writes them
        to a Neo4j admin import compatible CSV file.

        Args:
        ----
            node_list (list): list of BioCypherNodes to be written
            label (str): the primary label of the node
            prop_dict (dict): properties of node class passed from parsing
                function and their types
            labels (str): string of one or several concatenated labels
                for the node class

        Returns:
        -------
            bool: The return value. True for success, False otherwise.

        """
        if not all(isinstance(n, BioCypherNode) for n in node_list):
            logger.error("Nodes must be passed as type BioCypherNode.")
            return False

        # from list of nodes to list of strings
        lines = []

        for n in node_list:
            # check for deviations in properties
            # node properties
            n_props = n.get_properties()
            n_keys = list(n_props.keys())
            # reference properties
            ref_props = list(prop_dict.keys())

            # compare lists order invariant
            if set(ref_props) != set(n_keys):
                onode = n.get_id()
                oprop1 = set(ref_props).difference(n_keys)
                oprop2 = set(n_keys).difference(ref_props)
                logger.error(
                    f"At least one node of the class {n.get_label()} "
                    f"has more or fewer properties than another. "
                    f"Offending node: {onode!r}, offending property: "
                    f"{max([oprop1, oprop2])}. "
                    f"All reference properties: {ref_props}, "
                    f"All node properties: {n_keys}.",
                )
                return False

            line = [n.get_id()]

            if ref_props:
                plist = []
                # make all into strings, put actual strings in quotes
                for k, v in prop_dict.items():
                    p = n_props.get(k)
                    if p is None:  # TODO make field empty instead of ""?
                        plist.append("")
                    elif v in ["bool", "boolean"]:
                        plist.append(str(p).lower())
                    elif v in [
                        "int",
                        "integer",
                        "long",
                        "float",
                        "double",
                        "dbl",
                    ]:
                        plist.append(str(p))
                    elif isinstance(p, list):
                        plist.append(self._write_array_string(p))
                    else:
                        plist.append(f"{self.quote}{p!s}{self.quote}")

                line.append(self.delim.join(plist))
            line.append(labels)

            lines.append(self.delim.join(line) + "\n")

        # avoid writing empty files
        if lines:
            self._write_next_part(label, lines)

        return True

    def _write_edge_data(self, edges, batch_size):
        """Write biocypher edges to CSV.

        Writes biocypher edges to CSV conforming to the headers created
        with `_write_edge_headers()`, and is actually required to be run
        before calling `_write_node_headers()` to set the
        :py:attr:`self.edge_property_dict` for passing the edge
        properties to the instance. Expects list or generator of edges
        from the :py:class:`BioCypherEdge` class.

        Args:
        ----
            edges (BioCypherEdge): an iterable of edges in
                :py:class:`BioCypherEdge` format

        Returns:
        -------
            bool: The return value. True for success, False otherwise.

        Todo:
        ----
            - currently works for mixed edges but in practice often is
              called on one iterable containing one type of edge only

        """
        if not isinstance(edges, Iterable):
            logger.error("Edges must be passed as iterable.")
            return False

        consume, flush = self._create_write_edge_data_handlers(batch_size)
        for edge in edges:
            if not consume(edge):
                return False
        return flush()

    # No `force` arg: only nodes need to bypass ontology lookup, for the
    # synthetic `schema_info` node written by `_core.py`.
    def _create_write_edge_data_handlers(self, batch_size):
        """Create edge-writing closures for streamed input.

        The returned `consume` closure consumes one
        :py:class:`BioCypherEdge` at a time and flushes full batches to disk.
        The returned `flush` closure writes remaining buffered edges and stores
        discovered edge properties in :py:attr:`self.edge_property_dict`.
        This must run before `_write_edge_headers()`.

        Args:
        ----
            batch_size (int): The number of edges per type to buffer before
                writing a part file.

        Returns:
        -------
            tuple[Callable, Callable]: `(consume, flush)` where `consume`
                processes one edge and `flush` writes all remaining buffers.

        Todo:
        ----
            - currently works for mixed edges but in practice often is
              called on one iterable containing one type of edge only

        """
        empty = True
        bins = defaultdict(list)  # dict to store a list for each
        # label that is passed in
        bin_l = {}  # dict to store the length of each list for
        # batching cutoff
        reference_props = defaultdict(
            dict,
        )  # dict to store a dict of properties

        # for each label to check for consistency and their type
        # for now, relevant for `int`
        def consume(edge):
            nonlocal empty
            if empty:
                logger.debug("Writing edge CSV from generator.")
                empty = False

            if not (edge.get_source_id() and edge.get_target_id()):
                logger.error(
                    f"Edge must have source and target node. Caused by: {edge}",
                )
                return True

            label = edge.get_label()

            if label not in bins:
                # start new list
                bins[label].append(edge)
                bin_l[label] = 1

                # get properties from config if present

                # check whether label is in ontology_adapter.leaves
                # (may not be if it is an edge that carries the
                # "label_as_edge" property)
                cprops = None
                if label in self.translator.ontology.mapping.extended_schema:
                    cprops = self.translator.ontology.mapping.extended_schema.get(label).get(
                        "properties",
                    )
                else:
                    # try via "label_as_edge"
                    for (
                        k,
                        v,
                    ) in self.translator.ontology.mapping.extended_schema.items():
                        if isinstance(v, dict):
                            if v.get("label_as_edge") == label:
                                cprops = v.get("properties")
                                logger.warning(
                                    "`label_as_edge` will be deprecated in a future version,"
                                    "please use edge types that exists in your ontology's taxonomy.",
                                )
                                break
                if cprops:
                    d = dict(cprops)

                    # add strict mode properties
                    if self.strict_mode:
                        d["source"] = "str"
                        d["version"] = "str"
                        d["licence"] = "str"

                else:
                    d = dict(edge.get_properties())
                    # encode property type
                    for k, v in d.items():
                        if v is not None:
                            if isinstance(v, list):
                                elem_type = type(v[0]).__name__ if v else "str"
                                d[k] = f"{elem_type}[]"
                            else:
                                d[k] = type(v).__name__
                # else use first encountered edge to define
                # properties for checking; could later be by
                # checking all edges but much more complicated,
                # particularly involving batch writing (would
                # require "do-overs"). for now, we output a warning
                # if edge properties diverge from reference
                # properties (in write_single_edge_list_to_file)
                # TODO

                reference_props[label] = d

            else:
                # add to list
                bins[label].append(edge)
                bin_l[label] += 1
                if not bin_l[label] < batch_size:
                    # batch size controlled here
                    passed = self._write_single_edge_list_to_file(
                        bins[label],
                        label,
                        reference_props[label],
                    )

                    if not passed:
                        return False

                    bins[label] = []
                    bin_l[label] = 0

            return True

        def flush():
            nonlocal empty
            if empty:
                return True

            # after generator depleted, write remainder of bins
            for label, nl in bins.items():
                passed = self._write_single_edge_list_to_file(
                    nl,
                    label,
                    reference_props[label],
                )

                if not passed:
                    return False

            # use complete bin list to write header files
            # TODO if a edge type has varying properties
            # (ie missingness), we'd need to collect all possible
            # properties in the generator pass

            # save first-edge properties to instance attribute
            for label in reference_props:
                self.edge_property_dict[label] = reference_props[label]

            return True

        return consume, flush

    def _write_single_edge_list_to_file(
        self,
        edge_list: list,
        label: str,
        prop_dict: dict,
    ):
        """Write a list of biocypher edges to a CSV file.

        This function takes one list of biocypher edges and writes them
        to a Neo4j admin import compatible CSV file.

        Args:
        ----
            edge_list (list): list of BioCypherEdges to be written

            label (str): the label (type) of the edge

            prop_dict (dict): properties of node class passed from parsing
                function and their types

        Returns:
        -------
            bool: The return value. True for success, False otherwise.

        """
        if not all(isinstance(n, BioCypherEdge) for n in edge_list):
            logger.error("Edges must be passed as type BioCypherEdge.")
            return False

        # from list of edges to list of strings
        lines = []
        for e in edge_list:
            # check for deviations in properties
            # edge properties
            e_props = e.get_properties()
            e_keys = list(e_props.keys())
            ref_props = list(prop_dict.keys())

            # compare list order invariant
            if set(ref_props) != set(e_keys):
                oedge = f"{e.get_source_id()}-{e.get_target_id()}"
                oprop1 = set(ref_props).difference(e_keys)
                oprop2 = set(e_keys).difference(ref_props)
                logger.error(
                    f"At least one edge of the class {e.get_label()} "
                    f"has more or fewer properties than another. "
                    f"Offending edge: {oedge!r}, offending property: "
                    f"{max([oprop1, oprop2])}. "
                    f"All reference properties: {ref_props}, "
                    f"All edge properties: {e_keys}.",
                )
                return False

            plist = []
            # make all into strings, put actual strings in quotes
            for k, v in prop_dict.items():
                p = e_props.get(k)
                if p is None:  # TODO make field empty instead of ""?
                    plist.append("")
                elif v in ["bool", "boolean"]:
                    plist.append(str(p).lower())
                elif v in [
                    "int",
                    "integer",
                    "long",
                    "float",
                    "double",
                    "dbl",
                ]:
                    plist.append(str(p))
                elif isinstance(p, list):
                    plist.append(self._write_array_string(p))
                else:
                    plist.append(self.quote + str(p) + self.quote)

            entries = [e.get_source_id()]

            skip_id = False
            schema_label = None

            if label in ["IS_SOURCE_OF", "IS_TARGET_OF", "IS_PART_OF"]:
                skip_id = True
            elif not self.translator.ontology.mapping.extended_schema.get(label):
                # find label in schema by label_as_edge
                for (
                    k,
                    v,
                ) in self.translator.ontology.mapping.extended_schema.items():
                    if v.get("label_as_edge") == label:
                        schema_label = k
                        break
            else:
                schema_label = label

            if schema_label:
                if (
                    self.translator.ontology.mapping.extended_schema.get(
                        schema_label,
                    ).get("use_id")
                    == False  # noqa: E712 (seems to not work with 'not')
                ):
                    skip_id = True

            if not skip_id:
                entries.append(e.get_id() or "")

            if ref_props:
                entries.append(self.delim.join(plist))

            entries.append(e.get_target_id())

            all_labels = self._get_all_labels(label, self.edge_labels_order)
            entries.append(all_labels)

            lines.append(
                self.delim.join(entries) + "\n",
            )

        # avoid writing empty files
        if lines:
            self._write_next_part(label, lines)

        return True

    def _write_next_part(self, label: str, lines: list):
        """Write a list of strings to a new part file.

        Args:
        ----
            label (str): the label (type) of the edge; internal
            representation sentence case -> needs to become PascalCase
            for disk representation

            lines (list): list of strings to be written

        Returns:
        -------
            bool: The return value. True for success, False otherwise.

        """
        # translate label to PascalCase
        label_pascal = self.translator.name_sentence_to_pascal(parse_label(label))

        # list files in self.outdir
        files = glob.glob(os.path.join(self.outdir, f"{label_pascal}-part*.csv"))
        # find file with highest part number
        if not files:
            next_part = 0

        else:
            next_part = (
                max(
                    [int(f.split(".")[-2].split("-")[-1].replace("part", "")) for f in files],
                )
                + 1
            )

        # write to file
        padded_part = str(next_part).zfill(3)
        logger.info(
            f"Writing {len(lines)} entries to {label_pascal}-part{padded_part}.csv",
        )

        # store name only in case import_call_file_prefix is set
        part = f"{label_pascal}-part{padded_part}.csv"
        file_path = os.path.join(self.outdir, part)

        with open(file_path, "w", encoding="utf-8") as f:
            # concatenate with delimiter
            f.writelines(lines)

        if not self.parts.get(label):
            self.parts[label] = [part]
        else:
            self.parts[label].append(part)

    def get_import_call(self) -> str:
        """Eeturn the import call.

        Return the import call detailing folder and individual node and
        edge headers and data files, as well as delimiters and database name.

        Returns
        -------
            str: a bash command for the database import

        """
        return self._construct_import_call()

    def write_import_call(self) -> str:
        """Write the import call.

        Function to write the import call detailing folder and
        individual node and edge headers and data files, as well as
        delimiters and database name, to the export folder as txt.

        Returns
        -------
            str: The path of the file holding the import call.

        """
        file_path = os.path.join(self.outdir, self._get_import_script_name())
        logger.info(f"Writing {self.db_name + ' ' if self.db_name else ''}import call to `{file_path}`.")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self._construct_import_call())

        return file_path


def parse_label(label: str) -> str:
    """Check if the label is compliant with Neo4j naming conventions.

    Check against https://neo4j.com/docs/cypher-manual/current/syntax/naming/,
    and if not compliant, remove non-compliant characters.

    Args:
    ----
        label (str): The label to check
    Returns:
        str: The compliant label

    """
    # Check if the name contains only alphanumeric characters, underscore, or dollar sign
    # and dot (for class hierarchy of BioCypher)
    allowed_chars = r"a-zA-Z0-9_$ ."
    matches = re.findall(f"[{allowed_chars}]", label)
    non_matches = re.findall(f"[^{allowed_chars}]", label)
    if non_matches:
        non_matches = list(set(non_matches))
        logger.warning(
            f"Label is not compliant with Neo4j naming rules. Removed non compliant characters: {non_matches}",
        )

    def first_character_compliant(character: str) -> bool:
        return character.isalpha() or character == "$"

    if not matches:
        logger.warning("Label contains only non-compliant characters and will be empty.")
        return ""

    if not first_character_compliant(matches[0]):
        for c in matches:
            if first_character_compliant(c):
                matches = matches[matches.index(c) :]
                break
        logger.warning("Label does not start with an alphabetic character or with $. Removed non compliant characters.")
    return "".join(matches).strip()
