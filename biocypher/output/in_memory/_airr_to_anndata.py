import re
from datetime import datetime

from biocypher._deduplicate import Deduplicator
from biocypher.output.in_memory._in_memory_kg import _InMemoryKG

try:
    import scirpy.pp as scp
    from scirpy.io import AirrCell, from_airr_cells
    HAS_SCIRPY = True
except ImportError:
    HAS_SCIRPY = False

class AIRRtoAnnDataKG(_InMemoryKG):
    def __init__(self, deduplicator=None):
        super().__init__()
        self.deduplicator = deduplicator or Deduplicator()
        # Store entities by type directly
        self.entities_by_type = {}

    def _check_dependencies(self):
        """Verify that scirpy is available."""
        if not HAS_SCIRPY:
            raise ImportError(
                "scirpy package is required for AIRR to AnnData conversion. "
                "Install it with 'poetry add biocypher[scirpy]' or 'poetry add scirpy'."
            )

    def get_kg(self, verbose = True):
        """Convert directly to AnnData instead of going through DataFrames"""
        self._check_dependencies()
        airr_cells = self.to_airr_cells(verbose=verbose)
        return self.airr_cells_to_anndata(airr_cells, verbose=verbose)
    
        # return self.to_anndata()

    def add_nodes(self, nodes):
        """Add BioCypher nodes, organizing them by type."""
        lists = self._separate_entity_types(nodes)
        self._add_to_entities_by_type(lists)

    def add_edges(self, edges):
        """Add BioCypher edges, organizing them by type."""
        lists = self._separate_entity_types(edges)
        self._add_to_entities_by_type(lists)

    def _add_to_entities_by_type(self, lists):
        """Add entities from lists to the entities_by_type dictionary."""
        for _type, _entities in lists.items():
            if _type not in self.entities_by_type:
                self.entities_by_type[_type] = []
            self.entities_by_type[_type].extend(_entities)

    def to_airr_cells(self, verbose=False):
        """Convert BioCypher entities to the AIRR cells."""
        tra_nodes = self.entities_by_type.get("tra sequence", [])
        trb_nodes = self.entities_by_type.get("trb sequence", [])
        epitope_nodes = self.entities_by_type.get("epitope", [])
        tcr_edges = self.entities_by_type.get("alpha sequence to beta sequence association", [])
        tcr_epitope_edges = self.entities_by_type.get("t cell receptor sequence to epitope association", [])

        # Create efficient lookups directly from BioCypher objects
        tra_dict = {node.get_id(): node.get_properties() for node in tra_nodes}
        trb_dict = {node.get_id(): node.get_properties() for node in trb_nodes}
        epitope_dict = {node.get_id(): node.get_properties() for node in epitope_nodes}

        tcr_pairs = {} 
        receptor_to_epitopes = {} 
        processed_receptors = set()

        print("Processing epitope associations")
        for edge in tcr_epitope_edges:
            edge_dict = edge.get_dict()
            source_id = edge_dict["source_id"]  # TCR chain
            target_id = edge_dict["target_id"]  # Epitope

            if source_id not in receptor_to_epitopes:
                receptor_to_epitopes[source_id] = set()
            receptor_to_epitopes[source_id].add(target_id)
        
        print("Processing paired TCRs")
        for edge in tcr_edges:
            edge_dict = edge.get_dict()
            relationship_id = edge_dict["relationship_id"]
            tra_id = edge_dict["source_id"]
            trb_id = edge_dict["target_id"]

            tcr_pairs[relationship_id] = {"tra_id": tra_id, "trb_id": trb_id, "epitopes": set()}
            processed_receptors.update([tra_id, trb_id])

            # Initialize epitope tracking for receptors
            if tra_id in receptor_to_epitopes:
                tcr_pairs[relationship_id]["epitopes"].update(receptor_to_epitopes[tra_id])
            if trb_id in receptor_to_epitopes:
                tcr_pairs[relationship_id]["epitopes"].update(receptor_to_epitopes[trb_id])

        airr_cells = []

        for pair_id, pair_data in tcr_pairs.items():
            cell = self._generate_airr_cell(pair_id, pair_data["tra_id"], pair_data["trb_id"], pair_data["epitopes"], tra_dict, trb_dict, epitope_dict, paired=True)
            airr_cells.append(cell)

        print("Processing unpaired TCRs")
        for receptor_id, epitope_ids in receptor_to_epitopes.items():
            # Skip if in a pair or no epitopes
            if receptor_id in processed_receptors or not epitope_ids:
                continue

            cell = self._generate_airr_cell(f"unpaired_{receptor_id}", receptor_id, None, epitope_ids, tra_dict, trb_dict, epitope_dict, paired=False)
            airr_cells.append(cell)

        if verbose:
            print(f"Generated {len(airr_cells)} AIRR cells")
        return airr_cells

    def airr_cells_to_anndata(self, airr_cells, verbose=True):
        adata = from_airr_cells(airr_cells)
        scp.index_chains(adata)

        adata.uns["DB"] = {
            "name": "BioCypher_KG",
            "date_created": datetime.now().isoformat(),
            "cell_count": len(airr_cells),
            "paired_count": sum(1 for cell in airr_cells if cell.get("is_paired", True)),
            "unpaired_count": sum(1 for cell in airr_cells if not cell.get("is_paired", False)),
        }

        if verbose:
            print(f"Created AnnData object with {len(airr_cells)} cells")

        return adata

    def _generate_airr_cell(self, cell_id, tra_id, trb_id, epitope_ids, tra_dict, trb_dict, epitope_dict, paired):
        cell = AirrCell(cell_id=cell_id)
        if tra_id and tra_id in tra_dict:
            tra_data = tra_dict[tra_id]
            alpha_chain = AirrCell.empty_chain_dict()
            # Find v_call and j_call columns using regex
            v_call_key = next((k for k in tra_data if re.search(r"v[_]?gene|v[_]?call", k, re.IGNORECASE)), "")
            j_call_key = next((k for k in tra_data if re.search(r"j[_]?gene|j[_]?call", k, re.IGNORECASE)), "")
            alpha_chain.update({
                "locus": "TRA",
                "junction_aa": extract_sequence_from_id(tra_id),
                "v_call": tra_data.get(v_call_key, ""),
                "j_call": tra_data.get(j_call_key, ""),
                "consensus_count": 0,
                "productive": True,
            })
            cell.add_chain(alpha_chain)
        if trb_id and trb_id in trb_dict:
            trb_data = trb_dict[trb_id]
            beta_chain = AirrCell.empty_chain_dict()
            v_call_key = next((k for k in trb_data if re.search(r"v[_]?gene|v[_]?call", k, re.IGNORECASE)), "")
            j_call_key = next((k for k in trb_data if re.search(r"j[_]?gene|j[_]?call", k, re.IGNORECASE)), "")
            beta_chain.update({
                "locus": "TRB",
                "junction_aa": extract_sequence_from_id(trb_id),
                "v_call": trb_data.get(v_call_key, ""),
                "j_call": trb_data.get(j_call_key, ""),
                "consensus_count": 0,
                "productive": True,
            })
            cell.add_chain(beta_chain)
        if epitope_ids:
            add_epitope_metadata(epitope_dict, cell, epitope_ids)
        cell["data_source"] = "BioCypher"
        cell["is_paired"] = paired
        return cell

def extract_sequence_from_id(receptor_id):
    """Extract CDR3 sequence from receptor ID like 'tra:CIRSGSARQLTF'."""
    if ":" in receptor_id:
        seq = receptor_id.split(":", 1)[1]
        return seq
    return receptor_id


def add_epitope_metadata(epitope_dict, cell, epitope_ids):
    """Helper function to add epitope metadata to an AirrCell."""
    # TODO: now I only add the data about one epitope to the cell, figure how to store several
    for epitope_id in epitope_ids:
        if epitope_id in epitope_dict:
            if "properties" in epitope_dict[epitope_id]:
                epitope_data = epitope_dict[epitope_id]["properties"]
            else:
                epitope_data = epitope_dict[epitope_id]

            keys_to_remove = ["node_id", "node_label", "id", "preferred_id"]
            epitope_data = {key: value for key, value in epitope_data.items() if key not in keys_to_remove}

    for prop_key, prop_value in epitope_data.items():
        cell[prop_key] = prop_value

    return cell