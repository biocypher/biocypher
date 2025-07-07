from typing import Any, Optional

from biocypher._create import BioCypherEdge, BioCypherNode
from biocypher._deduplicate import Deduplicator
from biocypher._logger import logger
from biocypher.output.in_memory._in_memory_kg import _InMemoryKG

try:
    from scirpy.io import AirrCell

    HAS_SCIRPY = True
except ImportError:
    HAS_SCIRPY = False


class AirrKG(_InMemoryKG):
    """Knowledge graph for AIRR (Adaptive Immune Receptor Repertoire) data.

    This class implements the AIRR data model for representing immune receptor sequences
    (antibodies and T cell receptors) and their annotations. To ensure proper conversion
    to AIRR format, your schema file should define immune receptor entities with property
    names that match the AIRR standards.

    Key property names in your schema for immune receptor entities:
    - locus: The gene locus (e.g., "TRA", "TRB", "IGH", "IGK", "IGL")
    - junction_aa: The amino acid sequence of the junction region (CDR3)
    - v_call: The V gene assignment
    - j_call: The J gene assignment
    - productive: Whether the sequence is productive

    Pairing Strategies specified in get_kg method:
    - Indirect pairings allowed:
        Epitope is only matched with ONE of the paired receptors -> the "paired" AIRR cell will be created
    - Indirect pairings not allowed:
        Epitope is only matched with ONE of the paired receptors -> no "paired" AIRR cell will be created

    For a complete list of available fields and their descriptions, see:
    https://docs.airr-community.org/en/stable/datarep/rearrangements.html#fields

    All properties from the biocypher schema defined by user will be preserved in the AIRR format.
    """

    # Constants for internal property filtering
    _INTERNAL_PROPERTIES = frozenset(["node_id", "node_label", "id", "preferred_id"])

    def __init__(
        self,
        deduplicator: Optional["Deduplicator"] = None,
        metadata_entity_type: str = "epitope",
    ) -> None:
        """Initialize AirrKG with configurable metadata node type.

        Args:
        ----
            deduplicator: Deduplicator instance
            metadata_entity_type: String specifying the metadata node type (default: "epitope")

        """
        super().__init__()
        self.deduplicator = deduplicator or Deduplicator()
        self.metadata_entity_type = metadata_entity_type

        # Initialize storage for processed cells
        self.adjacency_list = {}
        self.airr_cells = []

        # These will be populated when nodes and edges are added
        self.sequence_entity_types = {}
        self.chain_relationship_types = []
        self.chain_to_epitope_relationship_types = []

    def _check_dependencies(self) -> None:
        """Verify that scirpy is available."""
        if not HAS_SCIRPY:
            msg = (
                "AirrCell module from scirpy not detected. "
                "Install it with 'poetry add biocypher[scirpy]' or 'poetry add scirpy'."
            )
            raise ImportError(msg)

    def get_kg(self, indirect_pairings: bool = True) -> list[AirrCell]:
        """Convert directly to AIRR format using AirCell from scirpy.

        Args:
        ----
            indirect_pairings: Boolean controlling pairing strategy (default: True)
                - True:
                    Epitope is only matched with ONE of the paired receptors -> the "paired" AIRR cell will be created
                - False:
                    Epitope is only matched with ONE of the paired receptors -> no "paired" AIRR cell will be created

        Returns:
        -------
            list: List of generated AIRR cells

        """
        self._check_dependencies()
        if not self.airr_cells:
            self.airr_cells = self._to_airr_cells(self.adjacency_list, indirect_pairings)
        return self.airr_cells

    def add_nodes(self, nodes: list[BioCypherNode]) -> None:
        """Add BioCypher nodes, organizing them by type."""
        self._add_to_entities_by_type(nodes)

    def add_edges(self, edges: list[BioCypherEdge]) -> None:
        """Add BioCypher edges, organizing them by type."""
        self._add_to_entities_by_type(edges)

    def _add_to_entities_by_type(self, entities: dict[str, list[Any]]) -> None:
        """Add all entities (both nodes and edges) to a common adj. list."""
        lists = self._separate_entity_types(entities)
        for _type, _entities in lists.items():
            if _type not in self.adjacency_list:
                self.adjacency_list[_type] = []
            self.adjacency_list[_type].extend(_entities)

    def _process_entities(self, entities: dict[str, list[Any]]) -> tuple[dict, dict, dict]:
        """Process entities and organize them into sequence nodes, metadata nodes, and receptor-epitope mappings.

        Args:
        ----
            entities: Dictionary mapping entity types to lists of BioCypherNode/BioCypherEdge objects

        Returns:
        -------
            tuple: (sequence_nodes, metadata_nodes, receptor_epitope_mapping)

        """
        sequence_nodes = {}
        metadata_nodes = {}
        receptor_epitope_mapping = {}

        # Determine entity types while processing
        all_node_types = set()
        all_edge_types = set()

        for entity_type, entities_list in entities.items():
            if not entities_list:  # Skip empty lists
                continue

            # Determine if this is a node or edge type
            if isinstance(entities_list[0], BioCypherNode):
                all_node_types.add(entity_type)
                if entity_type == self.metadata_entity_type:
                    metadata_nodes.update({node.get_id(): node for node in entities_list})
                else:
                    sequence_nodes.update({node.get_id(): node for node in entities_list})
                    self.sequence_entity_types[entity_type] = entity_type.replace(" sequence", "").upper()
            elif isinstance(entities_list[0], BioCypherEdge):
                all_edge_types.add(entity_type)

        # Update relationship types
        self.chain_relationship_types = [
            edge_type for edge_type in all_edge_types if self.metadata_entity_type not in edge_type.lower()
        ]

        self.chain_to_epitope_relationship_types = [
            edge_type for edge_type in all_edge_types if self.metadata_entity_type in edge_type.lower()
        ]

        # Process chain-to-epitope relationships
        for entity_type in self.chain_to_epitope_relationship_types:
            self._update_receptor_epitope_mapping(entities[entity_type], receptor_epitope_mapping)

        return sequence_nodes, metadata_nodes, receptor_epitope_mapping

    def _update_receptor_epitope_mapping(self, edges: list[BioCypherEdge], mapping: dict[str, set]) -> None:
        """Update receptor-epitope mapping with new edges.

        Args:
        ----
            edges: List of edges to process
            mapping: Dictionary to update with receptor-epitope mappings

        """
        for edge in edges:
            source_id = edge.get_source_id()
            if source_id not in mapping:
                mapping[source_id] = set()
            mapping[source_id].add(edge.get_target_id())

    def _process_paired_chains(
        self,
        entities: dict[str, list[Any]],
        sequence_nodes: dict[str, BioCypherNode],
        metadata_nodes: dict[str, BioCypherNode],
        receptor_epitope_mapping: dict[str, set],
        indirect_pairings: bool = True,
    ) -> tuple[list[AirrCell], set[str], int]:
        """Process paired chains and generate AIRR cells.

        Args:
        ----
            entities: Dictionary of all entities
            sequence_nodes: Dictionary of sequence nodes
            metadata_nodes: Dictionary of metadata nodes
            receptor_epitope_mapping: Dictionary of receptor-epitope mappings
            indirect_pairings: Boolean controlling pairing strategy

        Returns:
        -------
            tuple: (list of generated cells, set of processed chain IDs, count of cells with multiple epitopes)

        """
        airr_cells = []
        processed_chains = set()
        n_metacells = 0

        for entity_type, edges in entities.items():
            if entity_type in self.chain_relationship_types:
                for edge in edges:
                    source_id, target_id = edge.get_source_id(), edge.get_target_id()
                    processed_chains.update([source_id, target_id])

                    # Use conditional logic for pairing strategy
                    source_metadata = receptor_epitope_mapping.get(source_id, set())
                    target_metadata = receptor_epitope_mapping.get(target_id, set())

                    if indirect_pairings:
                        # Union: create paired cell if either chain binds epitopes
                        metadata_ids = source_metadata | target_metadata

                        metadata_nodes_cell = self._get_metadata_nodes(metadata_ids, metadata_nodes)
                        if metadata_nodes_cell:
                            cell_s = self._generate_airr_cell(
                                cell_id=edge.get_id(),
                                source_node=sequence_nodes.get(source_id),
                                target_node=sequence_nodes.get(target_id),
                                metadata_nodes=metadata_nodes_cell,
                                paired=True,
                                receptor_epitope_mapping=receptor_epitope_mapping,
                            )
                            airr_cells.extend(cell_s)
                            if len(cell_s) > 1:
                                n_metacells += 1
                    else:
                        # Intersection: create paired cell only if both chains bind same epitopes
                        shared_metadata_ids = source_metadata & target_metadata

                        # Create paired cell if there are shared epitopes
                        if shared_metadata_ids:
                            shared_metadata_nodes = self._get_metadata_nodes(shared_metadata_ids, metadata_nodes)
                            if shared_metadata_nodes:
                                cell_s = self._generate_airr_cell(
                                    cell_id=edge.get_id(),
                                    source_node=sequence_nodes.get(source_id),
                                    target_node=sequence_nodes.get(target_id),
                                    metadata_nodes=shared_metadata_nodes,
                                    paired=True,
                                    receptor_epitope_mapping=receptor_epitope_mapping,
                                )
                                airr_cells.extend(cell_s)
                                if len(cell_s) > 1:
                                    n_metacells += 1

                        # Create unpaired cells for chains with non-overlapping epitopes
                        source_only_metadata = source_metadata - target_metadata
                        target_only_metadata = target_metadata - source_metadata

                        # Create unpaired cell for source chain if it has unique epitopes
                        if source_only_metadata:
                            source_only_nodes = self._get_metadata_nodes(source_only_metadata, metadata_nodes)
                            if source_only_nodes:
                                source_cells = self._generate_airr_cell(
                                    cell_id=f"unpaired_{source_id}",
                                    source_node=sequence_nodes.get(source_id),
                                    target_node=None,
                                    metadata_nodes=source_only_nodes,
                                    paired=False,
                                    receptor_epitope_mapping=receptor_epitope_mapping,
                                )
                                airr_cells.extend(source_cells)
                                if len(source_cells) > 1:
                                    n_metacells += 1

                        # Create unpaired cell for target chain if it has unique epitopes
                        if target_only_metadata:
                            target_only_nodes = self._get_metadata_nodes(target_only_metadata, metadata_nodes)
                            if target_only_nodes:
                                target_cells = self._generate_airr_cell(
                                    cell_id=f"unpaired_{target_id}",
                                    source_node=sequence_nodes.get(target_id),
                                    target_node=None,
                                    metadata_nodes=target_only_nodes,
                                    paired=False,
                                    receptor_epitope_mapping=receptor_epitope_mapping,
                                )
                                airr_cells.extend(target_cells)
                                if len(target_cells) > 1:
                                    n_metacells += 1

        return airr_cells, processed_chains, n_metacells

    def _process_unpaired_chains(
        self,
        receptor_epitope_mapping: dict[str, set],
        sequence_nodes: dict[str, BioCypherNode],
        metadata_nodes: dict[str, BioCypherNode],
        processed_chains: set[str],
    ) -> tuple[list[AirrCell], int]:
        """Process unpaired chains and generate AIRR cells.

        Args:
        ----
            receptor_epitope_mapping: Dictionary of receptor-epitope mappings
            sequence_nodes: Dictionary of sequence nodes
            metadata_nodes: Dictionary of metadata nodes
            processed_chains: Set of already processed chain IDs

        Returns:
        -------
            tuple: (List of generated cells, count of cells with multiple epitopes)

        """
        airr_cells = []
        n_metacells = 0

        for chain_id in receptor_epitope_mapping:
            if chain_id not in processed_chains:
                # Get all metadata nodes for this unpaired chain
                metadata_nodes_cell = self._get_metadata_nodes(receptor_epitope_mapping[chain_id], metadata_nodes)

                if metadata_nodes_cell:
                    cell_s = self._generate_airr_cell(
                        cell_id=f"unpaired_{chain_id}",
                        source_node=sequence_nodes.get(chain_id),
                        target_node=None,
                        metadata_nodes=metadata_nodes_cell,
                        paired=False,
                        receptor_epitope_mapping=receptor_epitope_mapping,
                    )
                    airr_cells.extend(cell_s)
                    # Check if multiple cells were generated (indicating multiple epitopes)
                    if len(cell_s) > 1:
                        n_metacells += 1

        return airr_cells, n_metacells

    def _to_airr_cells(self, entities: dict[str, list[Any]], indirect_pairings: bool = True) -> list[AirrCell]:
        """Convert BioCypher entities to AIRR cells using configurable mappings.

        Args:
        ----
            entities: Dictionary mapping entity types to lists of BioCypherNode/BioCypherEdge objects
            indirect_pairings: Boolean controlling pairing strategy (default: True)
                - True:
                    Epitope is only matched with ONE of the paired receptors -> the "paired" AIRR cell will be created
                - False:
                    Epitope is only matched with ONE of the paired receptors -> no "paired" AIRR cell will be created

        Returns:
        -------
            list: List of generated AIRR cells

        """
        if not entities:
            msg = "No entities provided for conversion."
            raise ValueError(msg)

        logger.info("Starting conversion to AIRR cells")

        # Process all entities
        sequence_nodes, metadata_nodes, receptor_epitope_mapping = self._process_entities(entities)

        # Process paired chains
        airr_cells, processed_chains, paired_metacells = self._process_paired_chains(
            entities,
            sequence_nodes,
            metadata_nodes,
            receptor_epitope_mapping,
            indirect_pairings,
        )

        # Process unpaired chains
        unpaired_cells, unpaired_metacells = self._process_unpaired_chains(
            receptor_epitope_mapping,
            sequence_nodes,
            metadata_nodes,
            processed_chains,
        )
        airr_cells.extend(unpaired_cells)

        # Calculate total cells with multiple epitopes
        total_metacells = paired_metacells + unpaired_metacells

        # Log information about cells
        logger.info(f"Generated total of {len(airr_cells)} AIRR cells")
        if total_metacells > 0:
            logger.info(f"{total_metacells} cells with more than 1 epitope were detected")

        return airr_cells

    def _get_metadata_nodes(
        self,
        metadata_ids: set[str],
        metadata_nodes: dict[str, BioCypherNode],
    ) -> list[BioCypherNode]:
        """Get metadata nodes for a set of metadata IDs.

        Args:
        ----
            metadata_ids: Set of metadata IDs
            metadata_nodes: Dictionary of metadata nodes

        Returns:
        -------
            list: List of metadata nodes

        """
        return [metadata_nodes[ep_id] for ep_id in metadata_ids if ep_id in metadata_nodes]

    def _generate_airr_cell(
        self,
        cell_id: str,
        source_node: BioCypherNode | None,
        target_node: BioCypherNode | None,
        metadata_nodes: list[BioCypherNode],
        paired: bool,
        receptor_epitope_mapping: dict[str, set] | None = None,
    ) -> list[AirrCell]:
        cell = AirrCell(cell_id=cell_id)

        # Process both chains
        for node in [source_node, target_node]:
            if not node:  # Skip if node is None
                continue

            props = node.get_properties()
            chain = AirrCell.empty_chain_dict()

            # Add all properties except internal ones
            for key, value in props.items():
                if key not in self._INTERNAL_PROPERTIES:
                    chain[key] = value

            # Add locus based on node type
            chain["locus"] = self.sequence_entity_types.get(node.get_label(), node.get_label())
            chain["consensus_count"] = 0
            chain["productive"] = True

            # Add binds_epitope field based on receptor_epitope_mapping
            if receptor_epitope_mapping and node.get_id() in receptor_epitope_mapping:
                chain["validated_epitope"] = bool(receptor_epitope_mapping[node.get_id()])
            else:
                chain["validated_epitope"] = False

            cell.add_chain(chain)

        # Add metadata
        return self.add_metadata(metadata_nodes, cell, paired)

    def add_metadata(self, metadata_nodes: list[BioCypherNode], cell: AirrCell, paired: bool) -> list[AirrCell]:
        """Add metadata from nodes to cell(s) and return a list of cells.

        Args:
        ----
            metadata_nodes: List of metadata nodes to add
            cell: Base cell to add metadata to
            paired: Whether the cell is paired

        Returns:
        -------
            List of cells with metadata added

        """
        cells = []
        if not metadata_nodes:
            cell["data_source"] = "BioCypher"
            cell["is_paired"] = paired
            cells.append(cell)
        else:
            for i, node in enumerate(metadata_nodes):
                # Create a new AirrCell for each metadata node
                if i > 0:
                    cell_id_new = f"{cell.cell_id}_meta{i+1}"
                    meta_cell = AirrCell(cell_id=cell_id_new)
                    for chain in cell.chains:
                        meta_cell.add_chain(chain)
                else:
                    meta_cell = cell
                props = node.get_properties()
                for key, value in props.items():
                    if key not in self._INTERNAL_PROPERTIES:
                        meta_cell[key] = value

                meta_cell["data_source"] = "BioCypher"
                meta_cell["is_paired"] = paired

                cells.append(meta_cell)
        return cells
