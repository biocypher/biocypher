import os

import pytest


@pytest.mark.parametrize("l", [4], scope="function")
def test_write_node_data_from_gen(core, _get_nodes):
    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    passed = core.write_nodes(node_gen(nodes))
    assert passed

    path = core._output_directory

    protein_csv = os.path.join(path, "Protein-part000.csv")
    micro_rna_csv = os.path.join(path, "MicroRNA-part000.csv")

    with open(protein_csv) as f:
        protein_data = f.read()

    with open(micro_rna_csv) as f:
        micro_rna_data = f.read()

    assert passed
    assert (
        "p1;'StringProperty1';4.0;9606;'gene1|gene2';'p1';'uniprot'"
        in protein_data
    )
    assert "BiologicalEntity" in protein_data
    assert "m1;'StringProperty1';9606;'m1';'mirbase'" in micro_rna_data
    assert "ChemicalEntity" in micro_rna_data


def test_show_ontology_structure_kwargs(core):
    treevis = core.show_ontology_structure(full=True)

    assert treevis is not None
