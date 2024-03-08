import os
import subprocess

import pytest


@pytest.mark.parametrize("length", [4], scope="module")
def test__construct_import_call(bw_tab_sqlite, _get_nodes):
    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    passed = bw_tab_sqlite.write_nodes(node_gen(nodes), batch_size=1e6)

    tmp_path = bw_tab_sqlite.outdir

    protein_csv = os.path.join(tmp_path, "Protein-part000.csv")
    micro_rna_csv = os.path.join(tmp_path, "MicroRNA-part000.csv")

    with open(protein_csv) as f:
        protein = f.read()

    with open(micro_rna_csv) as f:
        micro_rna = f.read()

    assert passed
    assert 'p1\t"StringProperty1"\t4.0\t9606\t' in protein
    assert '\t"uniprot"\t' in protein
    assert "BiologicalEntity" in protein
    assert "Polypeptide" in protein
    assert "Protein" in protein
    assert 'm1\t"StringProperty1"\t9606\t"m1"\t"mirbase"' in micro_rna
    assert "ChemicalEntity" in micro_rna

    import_call = bw_tab_sqlite._construct_import_call()
    assert "sqlite3 test_sqlite.db <" in import_call
    assert "protein-create_table.sql" in import_call
    assert "microrna-create_table.sql" in import_call
    assert "sqlite3 -separator $'\\t' test_sqlite.db \".import" in import_call
    assert "Protein-part000.csv protein" in import_call
    assert "MicroRNA-part000.csv microrna" in import_call

    subprocess.check_output(import_call, shell=True)
