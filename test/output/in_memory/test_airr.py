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


def test_to_airr_cells_basic(in_memory_airr_kg, tra_nodes, trb_nodes, tcr_pair_edges):
    in_memory_airr_kg.add_nodes([tra_nodes[2], trb_nodes[2]])
    in_memory_airr_kg.add_edges([tcr_pair_edges[2]])
    airr_cells = in_memory_airr_kg.to_airr_cells(in_memory_airr_kg.adjacency_list)

    assert isinstance(airr_cells, list)
    assert len(airr_cells) == 1

    cell = airr_cells[0]
    assert cell.cell_id == "pair3"
    assert "TRA" in cell.chains[0]["locus"]
    assert "TRB" in cell.chains[1]["locus"]
    assert cell.chains[0]["junction_aa"] == "CAVDNNNDMRF"
    assert cell.chains[1]["junction_aa"] == "CASSPRGDSGNTIYF"
    assert cell["is_paired"] is True


def test_to_airr_cells_with_epitope(
    in_memory_airr_kg,
    tra_nodes,
    trb_nodes,
    epitope_nodes,
    tcr_pair_edges,
    tcr_epitope_edges,
):
    in_memory_airr_kg.add_nodes([tra_nodes[2], trb_nodes[2], epitope_nodes[2]])
    in_memory_airr_kg.add_edges([tcr_pair_edges[2], tcr_epitope_edges[2]])
    airr_cells = in_memory_airr_kg.to_airr_cells(in_memory_airr_kg.adjacency_list)

    assert len(airr_cells) == 1
    cell = airr_cells[0]
    assert cell["antigen_name"] == "M"
    assert cell["antigen_organism"] == "InfluenzaA"
    assert cell["MHC_class"] == "MHCI"


def test_multiple_tcr_pairs(in_memory_airr_kg, tra_nodes, trb_nodes, tcr_pair_edges):
    in_memory_airr_kg.add_nodes(tra_nodes[:2] + trb_nodes[:2])
    in_memory_airr_kg.add_edges(tcr_pair_edges[:2])
    airr_cells = in_memory_airr_kg.to_airr_cells(in_memory_airr_kg.adjacency_list)

    assert len(airr_cells) == 2
    cell_ids = [cell.cell_id for cell in airr_cells]
    assert "pair1" in cell_ids
    assert "pair2" in cell_ids

    alpha_junctions = [cell.chains[0]["junction_aa"] for cell in airr_cells]
    assert "CAVRWGGKLSF" in alpha_junctions
    assert "CAGLLPGGGADGLTF" in alpha_junctions

    # TODO: Add test for multiple epitopes per TCR pair
