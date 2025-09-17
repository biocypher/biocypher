import pytest
from biocypher.output.in_memory._airr import HAS_SCIRPY


def test_airr(in_memory_airr_kg):
    assert in_memory_airr_kg.adjacency_list == {}


# Tests using fixtures
def test_add_tcr_nodes(in_memory_airr_kg, tra_nodes, trb_nodes):
    in_memory_airr_kg.add_nodes([tra_nodes[0], trb_nodes[0]])

    assert "tra sequence" in in_memory_airr_kg.adjacency_list
    assert "trb sequence" in in_memory_airr_kg.adjacency_list
    assert len(in_memory_airr_kg.adjacency_list["tra sequence"]) == 1
    assert len(in_memory_airr_kg.adjacency_list["trb sequence"]) == 1


def test_add_tcr_epitope_edge(in_memory_airr_kg, tra_nodes, epitope_nodes, tcr_epitope_edges):
    in_memory_airr_kg.add_nodes([tra_nodes[0], epitope_nodes[0]])
    in_memory_airr_kg.add_edges([tcr_epitope_edges[0]])

    assert "t cell receptor sequence to epitope association" in in_memory_airr_kg.adjacency_list
    assert len(in_memory_airr_kg.adjacency_list["t cell receptor sequence to epitope association"]) == 1
    assert (
        in_memory_airr_kg.adjacency_list["t cell receptor sequence to epitope association"][0].get_source_id()
        == "tra:CAVRWGGKLSF"
    )
    assert (
        in_memory_airr_kg.adjacency_list["t cell receptor sequence to epitope association"][0].get_target_id()
        == "epitope:NLVPMVATV"
    )


def test_complete_tcr_graph(
    in_memory_airr_kg,
    tra_nodes,
    trb_nodes,
    epitope_nodes,
    tcr_pair_edges,
    tcr_epitope_edges,
):
    in_memory_airr_kg.add_nodes([tra_nodes[0], trb_nodes[0], epitope_nodes[0]])
    in_memory_airr_kg.add_edges([tcr_pair_edges[0], tcr_epitope_edges[0]])

    assert len(in_memory_airr_kg.adjacency_list["tra sequence"]) == 1
    assert len(in_memory_airr_kg.adjacency_list["trb sequence"]) == 1
    assert len(in_memory_airr_kg.adjacency_list["epitope"]) == 1
    assert len(in_memory_airr_kg.adjacency_list["alpha sequence to beta sequence association"]) == 1
    assert len(in_memory_airr_kg.adjacency_list["t cell receptor sequence to epitope association"]) == 1


@pytest.mark.skipif(not HAS_SCIRPY, reason="scirpy dependency not available")
def test_to_airr_cells_basic(in_memory_airr_kg, tra_nodes, trb_nodes, tcr_pair_edges):
    in_memory_airr_kg.add_nodes([tra_nodes[2], trb_nodes[2]])
    in_memory_airr_kg.add_edges([tcr_pair_edges[2]])
    airr_cells = in_memory_airr_kg.get_kg()
    assert isinstance(airr_cells, list)
    # No cells should be generated, since no metadata with epitopes was provided
    assert len(airr_cells) == 0


@pytest.mark.skipif(not HAS_SCIRPY, reason="scirpy dependency not available")
def test_to_airr_cells_with_epitope(
    in_memory_airr_kg,
    tra_nodes,
    trb_nodes,
    epitope_nodes,
    tcr_pair_edges,
    tcr_epitope_edges,
):
    in_memory_airr_kg.add_nodes([tra_nodes[2], trb_nodes[2], epitope_nodes[2]])
    in_memory_airr_kg.add_edges(tcr_pair_edges + tcr_epitope_edges)
    airr_cells = in_memory_airr_kg._to_airr_cells(in_memory_airr_kg.adjacency_list)

    assert len(airr_cells) == 1
    cell = airr_cells[0]
    assert cell["antigen_name"] == "M"
    assert cell["antigen_organism"] == "InfluenzaA"
    assert cell["MHC_class"] == "MHCI"


@pytest.mark.skipif(not HAS_SCIRPY, reason="scirpy dependency not available")
def test_multiple_epitopes_per_tcr(
    in_memory_airr_kg, tra_nodes, trb_nodes, epitope_nodes, tcr_epitope_edges, tcr_pair_edges
):
    in_memory_airr_kg.add_nodes(tra_nodes + trb_nodes + epitope_nodes)
    in_memory_airr_kg.add_edges(tcr_pair_edges + tcr_epitope_edges)
    airr_cells = in_memory_airr_kg._to_airr_cells(in_memory_airr_kg.adjacency_list)
    print(airr_cells)
    assert len(airr_cells) == 4
    alpha_junctions = [cell.chains[0]["junction_aa"] for cell in airr_cells]
    assert "CAVRWGGKLSF" in alpha_junctions
    assert "CAVDNNNDMRF" in alpha_junctions


@pytest.mark.skipif(not HAS_SCIRPY, reason="scirpy dependency not available")
def test_no_indirect_pairings(
    in_memory_airr_kg, tra_nodes, trb_nodes, epitope_nodes, tcr_epitope_edges, tcr_pair_edges
):
    in_memory_airr_kg.add_nodes(tra_nodes + trb_nodes + epitope_nodes)
    in_memory_airr_kg.add_edges(tcr_pair_edges + tcr_epitope_edges)
    airr_cells = in_memory_airr_kg._to_airr_cells(in_memory_airr_kg.adjacency_list, indirect_pairings=False)
    print(airr_cells)
    assert len(airr_cells) == 4
    alpha_junctions = [cell.chains[0]["junction_aa"] for cell in airr_cells]
    assert "CAVRWGGKLSF" in alpha_junctions
    assert "CAVDNNNDMRF" in alpha_junctions


# 1. Error Handling Tests
def test_missing_scirpy_raises_error(
    in_memory_airr_kg, tra_nodes, trb_nodes, epitope_nodes, tcr_pair_edges, tcr_epitope_edges
):
    """Test that missing scirpy dependency raises appropriate error."""
    # Add data to trigger AIRR cell generation
    in_memory_airr_kg.add_nodes([tra_nodes[0], trb_nodes[0], epitope_nodes[0]])
    in_memory_airr_kg.add_edges([tcr_pair_edges[0], tcr_epitope_edges[0]])

    # Mock HAS_SCIRPY = False by temporarily modifying the module
    import biocypher.output.in_memory._airr as airr_module

    original_has_scirpy = airr_module.HAS_SCIRPY
    airr_module.HAS_SCIRPY = False

    try:
        with pytest.raises(ImportError) as exc_info:
            in_memory_airr_kg.get_kg()
        assert "AirrCell module from scirpy not detected" in str(exc_info.value)
        assert "Install it with 'uv add biocypher[scirpy]'" in str(exc_info.value)
    finally:
        # Restore original value
        airr_module.HAS_SCIRPY = original_has_scirpy


@pytest.mark.skipif(not HAS_SCIRPY, reason="scirpy dependency not available")
def test_empty_adjacency_list(in_memory_airr_kg):
    """Test behavior with empty entity dictionary."""
    with pytest.raises(ValueError) as exc_info:
        in_memory_airr_kg._to_airr_cells({})
    assert "No entities provided for conversion" in str(exc_info.value)


@pytest.mark.skipif(not HAS_SCIRPY, reason="scirpy dependency not available")
def test_empty_entities_raises_error(in_memory_airr_kg):
    """Test that empty entities are handled gracefully."""
    # Test with empty list - should not raise error, just return empty result
    airr_cells = in_memory_airr_kg._to_airr_cells({"empty_type": []})
    assert airr_cells == []

    # Test with multiple empty lists
    airr_cells = in_memory_airr_kg._to_airr_cells({"empty_type1": [], "empty_type2": [], "empty_type3": []})
    assert airr_cells == []


# 2. Deduplication Tests
def test_deduplication_in_airr_kg(in_memory_airr_kg, tra_nodes, trb_nodes):
    """Test that deduplication works in AIRR context."""
    # Add the same node twice
    duplicate_node = tra_nodes[0]
    in_memory_airr_kg.add_nodes([duplicate_node, duplicate_node])

    # Check that only one instance is stored
    assert len(in_memory_airr_kg.adjacency_list["tra sequence"]) == 1

    # Verify deduplicator tracked the duplicate
    assert duplicate_node.get_id() in in_memory_airr_kg.deduplicator.duplicate_entity_ids


def test_deduplication_with_edges(in_memory_airr_kg, tra_nodes, trb_nodes, tcr_pair_edges):
    """Test deduplication with edges."""
    # Add duplicate edge
    duplicate_edge = tcr_pair_edges[0]
    in_memory_airr_kg.add_nodes([tra_nodes[0], trb_nodes[0]])
    in_memory_airr_kg.add_edges([duplicate_edge, duplicate_edge])

    # Check that only one edge is stored
    assert len(in_memory_airr_kg.adjacency_list["alpha sequence to beta sequence association"]) == 1


# 3. Configuration Tests
@pytest.mark.skipif(not HAS_SCIRPY, reason="scirpy dependency not available")
def test_custom_metadata_entity_type(tra_nodes, trb_nodes, epitope_nodes, tcr_epitope_edges):
    """Test with different metadata entity types."""
    # Create AIRR KG with custom metadata type
    from biocypher.output.in_memory._airr import AirrKG

    custom_kg = AirrKG(metadata_entity_type="antigen")

    # Add nodes with different metadata type
    custom_kg.add_nodes([tra_nodes[0], epitope_nodes[0]])
    custom_kg.add_edges([tcr_epitope_edges[0]])

    # Verify the nodes are stored with their actual node_label, not the custom metadata type
    assert "epitope" in custom_kg.adjacency_list  # Uses node_label, not metadata_entity_type
    assert "tra sequence" in custom_kg.adjacency_list
    assert len(custom_kg.adjacency_list["epitope"]) == 1
    assert len(custom_kg.adjacency_list["tra sequence"]) == 1

    # Verify the custom metadata entity type is configured
    assert custom_kg.metadata_entity_type == "antigen"

    # Test that the custom metadata type affects processing
    # The metadata_entity_type is used during AIRR cell generation, not storage
    custom_kg.get_kg()  # Should still work because the node_label "epitope" is recognized as metadata
    # even though metadata_entity_type is set to "antigen"


def test_metadata_entity_type_configuration():
    """Test that metadata entity type is properly configured."""
    from biocypher.output.in_memory._airr import AirrKG

    # Test default configuration
    default_kg = AirrKG()
    assert default_kg.metadata_entity_type == "epitope"

    # Test custom configuration
    custom_kg = AirrKG(metadata_entity_type="peptide")
    assert custom_kg.metadata_entity_type == "peptide"


# 4. AIRR Logic Tests
@pytest.mark.skipif(not HAS_SCIRPY, reason="scirpy dependency not available")
def test_unpaired_chain_processing(in_memory_airr_kg, tra_nodes, epitope_nodes, tcr_epitope_edges):
    """Test processing of unpaired chains."""
    # Add unpaired alpha chain with epitope binding
    in_memory_airr_kg.add_nodes([tra_nodes[0], epitope_nodes[0]])
    in_memory_airr_kg.add_edges([tcr_epitope_edges[0]])

    airr_cells = in_memory_airr_kg.get_kg()

    # Should create one AIRR cell for the unpaired chain
    assert len(airr_cells) == 1
    cell = airr_cells[0]

    # Should have one chain (alpha only)
    assert len(cell.chains) == 1
    assert cell.chains[0]["locus"] == "TRA"
    assert cell.chains[0]["junction_aa"] == "CAVRWGGKLSF"
    assert not cell["is_paired"]


@pytest.mark.skipif(not HAS_SCIRPY, reason="scirpy dependency not available")
def test_paired_chains_without_epitopes(in_memory_airr_kg, tra_nodes, trb_nodes, tcr_pair_edges):
    """Test paired chains that don't bind any epitopes."""
    # Add paired chains without epitope relationships
    in_memory_airr_kg.add_nodes([tra_nodes[0], trb_nodes[0]])
    in_memory_airr_kg.add_edges([tcr_pair_edges[0]])

    airr_cells = in_memory_airr_kg.get_kg()

    # Should not create any AIRR cells since no epitopes are bound
    assert len(airr_cells) == 0


@pytest.mark.skipif(not HAS_SCIRPY, reason="scirpy dependency not available")
def test_complex_epitope_mapping(
    in_memory_airr_kg, tra_nodes, trb_nodes, epitope_nodes, tcr_pair_edges, tcr_epitope_edges
):
    """Test complex epitope mapping scenarios."""
    # Add all nodes and edges to create complex scenario
    in_memory_airr_kg.add_nodes(tra_nodes + trb_nodes + epitope_nodes)
    in_memory_airr_kg.add_edges(tcr_pair_edges + tcr_epitope_edges)

    airr_cells = in_memory_airr_kg.get_kg()

    # Should create multiple AIRR cells
    assert len(airr_cells) > 0

    # Check that cells have proper epitope metadata
    for cell in airr_cells:
        assert "data_source" in cell
        assert cell["data_source"] == "BioCypher"
        # Should have epitope properties from metadata nodes
        assert any(key in cell for key in ["antigen_name", "antigen_organism", "MHC_class"])


@pytest.mark.skipif(not HAS_SCIRPY, reason="scirpy dependency not available")
def test_indirect_vs_direct_pairings(
    in_memory_airr_kg, tra_nodes, trb_nodes, epitope_nodes, tcr_pair_edges, tcr_epitope_edges
):
    """Test the difference between indirect and direct pairing strategies."""
    # Add paired chains where only one chain binds an epitope
    in_memory_airr_kg.add_nodes([tra_nodes[0], trb_nodes[0], epitope_nodes[0]])
    in_memory_airr_kg.add_edges([tcr_pair_edges[0], tcr_epitope_edges[0]])  # Only alpha binds epitope

    # Test indirect pairings (default)
    indirect_cells = in_memory_airr_kg._to_airr_cells(in_memory_airr_kg.adjacency_list, indirect_pairings=True)

    # Test direct pairings
    direct_cells = in_memory_airr_kg._to_airr_cells(in_memory_airr_kg.adjacency_list, indirect_pairings=False)

    # Indirect should create paired cell, direct should create unpaired cell
    assert len(indirect_cells) == 1
    assert indirect_cells[0]["is_paired"] is True

    # Direct should create unpaired cell for the chain that binds epitope
    assert len(direct_cells) == 1
    assert not direct_cells[0]["is_paired"]


# 5. Property Preservation Tests
@pytest.mark.skipif(not HAS_SCIRPY, reason="scirpy dependency not available")
def test_all_properties_preserved(
    in_memory_airr_kg, tra_nodes, trb_nodes, epitope_nodes, tcr_pair_edges, tcr_epitope_edges
):
    """Test that all user properties are preserved in AIRR cells."""
    # Add nodes with rich properties
    in_memory_airr_kg.add_nodes([tra_nodes[0], trb_nodes[0], epitope_nodes[0]])
    in_memory_airr_kg.add_edges([tcr_pair_edges[0], tcr_epitope_edges[0]])

    airr_cells = in_memory_airr_kg.get_kg()

    assert len(airr_cells) == 1
    cell = airr_cells[0]

    # Check that all chain properties are preserved
    alpha_chain = cell.chains[0]
    beta_chain = cell.chains[1]

    # Alpha chain properties
    assert alpha_chain["junction_aa"] == "CAVRWGGKLSF"
    assert alpha_chain["chain_1_type"] == "tra"
    assert alpha_chain["chain_1_organism"] == "HomoSapiens"
    assert alpha_chain["chain_1_v_gene"] == "TRAV3*01"
    assert alpha_chain["chain_1_j_gene"] == "TRAJ20*01"

    # Beta chain properties
    assert beta_chain["junction_aa"] == "CASSEGGVETQYF"
    assert beta_chain["chain_1_type"] == "trb"
    assert beta_chain["chain_1_organism"] == "HomoSapiens"
    assert beta_chain["chain_1_v_gene"] == "TRBV13*01"
    assert beta_chain["chain_1_j_gene"] == "TRBJ2-5*01"

    # Epitope properties
    assert cell["antigen_name"] == "pp65"
    assert cell["antigen_organism"] == "CMV"
    assert cell["MHC_class"] == "MHCI"


@pytest.mark.skipif(not HAS_SCIRPY, reason="scirpy dependency not available")
def test_internal_properties_filtered(
    in_memory_airr_kg, tra_nodes, trb_nodes, epitope_nodes, tcr_pair_edges, tcr_epitope_edges
):
    """Test that internal BioCypher properties are filtered out."""
    # Add nodes and edges
    in_memory_airr_kg.add_nodes([tra_nodes[0], trb_nodes[0], epitope_nodes[0]])
    in_memory_airr_kg.add_edges([tcr_pair_edges[0], tcr_epitope_edges[0]])

    airr_cells = in_memory_airr_kg.get_kg()

    assert len(airr_cells) == 1
    cell = airr_cells[0]

    # Check that internal properties are not present in chains
    alpha_chain = cell.chains[0]
    internal_properties = ["node_id", "node_label", "id", "preferred_id"]

    for prop in internal_properties:
        assert prop not in alpha_chain

    # Check that internal properties are not present in cell metadata
    for prop in internal_properties:
        assert prop not in cell


@pytest.mark.skipif(not HAS_SCIRPY, reason="scirpy dependency not available")
def test_airr_specific_properties_added(
    in_memory_airr_kg, tra_nodes, trb_nodes, epitope_nodes, tcr_pair_edges, tcr_epitope_edges
):
    """Test that AIRR-specific properties are properly added."""
    # Add nodes and edges
    in_memory_airr_kg.add_nodes([tra_nodes[0], trb_nodes[0], epitope_nodes[0]])
    in_memory_airr_kg.add_edges([tcr_pair_edges[0], tcr_epitope_edges[0]])

    airr_cells = in_memory_airr_kg.get_kg()

    assert len(airr_cells) == 1
    cell = airr_cells[0]

    # Check AIRR-specific properties are added
    assert "locus" in cell.chains[0]
    assert "locus" in cell.chains[1]
    assert cell.chains[0]["locus"] == "TRA"
    assert cell.chains[1]["locus"] == "TRB"

    assert "consensus_count" in cell.chains[0]
    assert "consensus_count" in cell.chains[1]
    assert cell.chains[0]["consensus_count"] == 0
    assert cell.chains[1]["consensus_count"] == 0

    assert "productive" in cell.chains[0]
    assert "productive" in cell.chains[1]
    assert cell.chains[0]["productive"] is True
    assert cell.chains[1]["productive"] is True

    assert "validated_epitope" in cell.chains[0]
    assert "validated_epitope" in cell.chains[1]
    assert cell.chains[0]["validated_epitope"] is True  # Alpha binds epitope
    assert not cell.chains[1]["validated_epitope"]  # Beta doesn't bind epitope

    # Check cell-level properties
    assert "data_source" in cell
    assert cell["data_source"] == "BioCypher"
    assert "is_paired" in cell
    assert cell["is_paired"] is True
