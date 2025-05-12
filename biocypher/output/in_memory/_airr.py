from __future__ import annotations

import re

from typing import TYPE_CHECKING, Any

from biocypher._deduplicate import Deduplicator
from biocypher.output.in_memory._in_memory_kg import _InMemoryKG

if TYPE_CHECKING:
    from biocypher._create import BioCypherNode

try:
    from scirpy.io import AirrCell
    HAS_SCIRPY = True
except ImportError:
    HAS_SCIRPY = False


class AirrKG(_InMemoryKG):
    def __init__(
        self,
        deduplicator=None,
        sequence_entity_types: dict[str, str] | None = None,
        chain_relationship_types: list[str] | None = None,
        chain_to_epitope_relationship_types: list[str] | None = None,
        metadata_entity_types: list[str] | None = None,
    ):
        """Initialize AirrKG with configurable node and edges types definitions.

        Args:
        ----
            deduplicator: Deduplicator instance
            sequence_entity_types: Dict mapping entity types to chain types (e.g. {"tra sequence": "TRA"})
            chain_relationship_types: List of relationship types that connect chains
            chain_to_epitope_relationship_types: List of relationship types that connect chains to epitopes
            metadata_entity_types: List of entity types that contain metadata

        """
        super().__init__()
        self.deduplicator = deduplicator or Deduplicator()
        # Default mappings if none provided
        self.sequence_entity_types = sequence_entity_types or {"tra sequence": "TRA", "trb sequence": "TRB"}
        self.chain_relationship_types = chain_relationship_types or ["alpha sequence to beta sequence association"]
        self.chain_to_epitope_relationship_types = chain_to_epitope_relationship_types or ["t cell receptor sequence to epitope association"]
        self.metadata_entity_types = metadata_entity_types or ["epitope"]

        # Initialize storage for processed cells
        self.adjacency_list = {}
        self.airr_cells = []

    def _check_dependencies(self):
        """Verify that scirpy is available."""
        if not HAS_SCIRPY:
            msg = (
                "AirrCell module from scirpy not detected. "
                "Install it with 'poetry add biocypher[scirpy]' or 'poetry add scirpy'."
            )
            raise ImportError(msg)

    def get_kg(self):
        """Convert directly to AIRR format using AirCell from scirpy."""
        self._check_dependencies()
        if not self.airr_cells:
            self.airr_cells = self.to_airr_cells(self.adjacency_list)
        return self.airr_cells

    def add_nodes(self, nodes):
        """Add BioCypher nodes, organizing them by type."""
        self._add_to_entities_by_type(nodes)

    def add_edges(self, edges):
        """Add BioCypher edges, organizing them by type."""
        self._add_to_entities_by_type(edges)

    def _add_to_entities_by_type(self, entities):
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

        for entity_type, entities_list in entities.items():
            if entity_type in self.sequence_entity_types:
                sequence_nodes.update({node.get_id(): node for node in entities_list})
            elif entity_type in self.metadata_entity_types:
                metadata_nodes.update({node.get_id(): node for node in entities_list})
            elif entity_type in self.chain_to_epitope_relationship_types:
                self._update_receptor_epitope_mapping(entities_list, receptor_epitope_mapping)

        return sequence_nodes, metadata_nodes, receptor_epitope_mapping

    def _update_receptor_epitope_mapping(self, edges: list[Any], mapping: dict):
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
        sequence_nodes: dict,
        metadata_nodes: dict,
        receptor_epitope_mapping: dict,
    ) -> tuple[list[AirrCell], set]:
        """Process paired chains and generate AIRR cells.

        Args:
        ----
            entities: Dictionary of all entities
            sequence_nodes: Dictionary of sequence nodes
            metadata_nodes: Dictionary of metadata nodes
            receptor_epitope_mapping: Dictionary of receptor-epitope mappings

        Returns:
        -------
            tuple: (list of generated cells, set of processed chain IDs)
        """
        airr_cells = []
        processed_chains = set()

        for entity_type, edges in entities.items():
            if entity_type in self.chain_relationship_types:
                for edge in edges:
                    metadata = self._get_chain_metadata(edge, receptor_epitope_mapping)
                    metadata_nodes_list = self._get_metadata_nodes(metadata, metadata_nodes)
                    
                    cell = self._generate_airr_cell(
                        cell_id=edge.get_id(),
                        source_node=sequence_nodes.get(edge.get_source_id()),
                        target_node=sequence_nodes.get(edge.get_target_id()),
                        metadata_nodes=metadata_nodes_list,
                        paired=True,
                    )

                    airr_cells.extend(cell)
                    processed_chains.update([edge.get_source_id(), edge.get_target_id()])

        return airr_cells, processed_chains

    def _get_chain_metadata(self, edge: Any, receptor_epitope_mapping: dict) -> set:
        """Get metadata for both chains in an edge.

        Args:
        ----
            edge: Edge connecting two chains
            receptor_epitope_mapping: Dictionary of receptor-epitope mappings

        Returns:
        -------
            set: Combined metadata from both chains
        """
        return (
            receptor_epitope_mapping.get(edge.get_source_id(), set()) |
            receptor_epitope_mapping.get(edge.get_target_id(), set())
        )

    def _get_metadata_nodes(self, metadata: set, metadata_nodes: dict) -> list:
        """Get metadata nodes for a set of metadata IDs.

        Args:
        ----
            metadata: Set of metadata IDs
            metadata_nodes: Dictionary of metadata nodes

        Returns:
        -------
            list: List of metadata nodes
        """
        return [
            metadata_nodes[ep_id] for ep_id in metadata
            if ep_id in metadata_nodes
        ]

    def _process_unpaired_chains(
        self,
        receptor_epitope_mapping: dict,
        sequence_nodes: dict,
        metadata_nodes: dict,
        processed_chains: set,
    ) -> list[AirrCell]:
        """Process unpaired chains and generate AIRR cells.

        Args:
        ----
            receptor_epitope_mapping: Dictionary of receptor-epitope mappings
            sequence_nodes: Dictionary of sequence nodes
            metadata_nodes: Dictionary of metadata nodes
            processed_chains: Set of already processed chain IDs

        Returns:
        -------
            list: List of generated cells
        """
        airr_cells = []
        
        for chain_id in receptor_epitope_mapping:
            if chain_id not in processed_chains:
                metadata_nodes_list = self._get_metadata_nodes(
                    receptor_epitope_mapping[chain_id],
                    metadata_nodes
                )
                cell = self._generate_airr_cell(
                    cell_id=f"unpaired_{chain_id}",
                    source_node=sequence_nodes.get(chain_id),
                    target_node=None,
                    metadata_nodes=metadata_nodes_list,
                    paired=False,
                )
                airr_cells.append(cell)

        return airr_cells

    def to_airr_cells(self, entities: dict[str, list[Any]]):
        """Convert BioCypher entities to AIRR cells using configurable mappings.

        Args:
        ----
            entities: Dictionary mapping entity types to lists of BioCypherNode/BioCypherEdge objects

        Returns:
        -------
            list: List of generated AIRR cells
        """
        if not entities:
            raise ValueError("No entities provided for conversion.")

        print("\nStarting conversion to AIRR cells")

        # Process all entities
        sequence_nodes, metadata_nodes, receptor_epitope_mapping = self._process_entities(entities)

        # Process paired chains
        print("\nProcessing paired chains")
        airr_cells, processed_chains = self._process_paired_chains(
            entities,
            sequence_nodes,
            metadata_nodes,
            receptor_epitope_mapping
        )

        # Process unpaired chains
        print("\nProcessing unpaired chains")
        unpaired_cells = self._process_unpaired_chains(
            receptor_epitope_mapping,
            sequence_nodes,
            metadata_nodes,
            processed_chains
        )
        airr_cells.extend(unpaired_cells)

        print(f"\nGenerated total of {len(airr_cells)} AIRR cells")
        return airr_cells

    def _generate_airr_cell(
        self,
        cell_id: str,
        source_node: BioCypherNode,
        target_node: BioCypherNode,
        metadata_nodes: list[BioCypherNode],
        paired: bool,
    ) -> AirrCell:
        cell = AirrCell(cell_id=cell_id)

        # Process both chains
        for node in [source_node, target_node]:
            if not node:  # Skip if node is None
                continue

            props = node.get_properties()
            chain = AirrCell.empty_chain_dict()

            # Find v_call and j_call columns using regex
            v_call_key = next((k for k in props if re.search(r"v[_]?gene|v[_]?call", k, re.IGNORECASE)), "")
            j_call_key = next((k for k in props if re.search(r"j[_]?gene|j[_]?call", k, re.IGNORECASE)), "")
            locus = self.sequence_entity_types.get(node.get_label(), node.get_label())

            chain.update({
                "locus": locus,
                "junction_aa": extract_sequence_from_id(node.get_id()),
                "v_call": props.get(v_call_key, ""),
                "j_call": props.get(j_call_key, ""),
                "consensus_count": 0,
                "productive": True,
            })
            cell.add_chain(chain)

        # Add metadata
        cells = add_metadata(metadata_nodes, cell, paired)
        return cells

def extract_sequence_from_id(receptor_id: str) -> str:
    """Extract amino acid sequence from receptor ID.
    Handles various ID formats:
    - 'tra:SEQUENCE' -> 'SEQUENCE'
    - 'SEQUENCE' -> 'SEQUENCE'
    - 'receptor_123_SEQUENCE' -> 'SEQUENCE'
    - 'SEQUENCE_123' -> 'SEQUENCE'

    Args:
    ----
        receptor_id: String containing the receptor ID and/or sequence

    Returns:
    -------
        str: The extracted amino acid sequence

    """
    # If it's a simple sequence without any prefix/suffix, return as is
    if all(c in "ACDEFGHIKLMNPQRSTVWY" for c in receptor_id):
        return receptor_id

    # Try to extract sequence after common delimiters
    delimiters = [":", "_", "-", "."]
    for delimiter in delimiters:
        if delimiter in receptor_id:
            parts = receptor_id.split(delimiter)
            # Look for the part that looks like an amino acid sequence
            for part in parts:
                if all(c in "ACDEFGHIKLMNPQRSTVWY" for c in part):
                    return part

    # If no sequence found, return the original ID
    return receptor_id


def add_metadata(metadata_nodes: list[BioCypherNode], cell: AirrCell, paired: bool) -> list[AirrCell]:
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
            # Add metadata from this node
            props = node.get_properties()
            for key, value in props.items():
                if key not in ["node_id", "node_label", "id", "preferred_id"]:
                    meta_cell[key] = value
            meta_cell["data_source"] = "BioCypher"
            meta_cell["is_paired"] = paired
            cells.append(meta_cell)
    return cells
