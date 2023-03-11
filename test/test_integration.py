import os

import pytest


@pytest.mark.parametrize('l', [4])
def test_write_node_data_from_gen(core, path, _get_nodes):
    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    passed = core.write_nodes(node_gen(nodes))

    p_csv = os.path.join(path, 'Protein-part000.csv')
    m_csv = os.path.join(path, 'MicroRNA-part000.csv')

    with open(p_csv) as f:
        pr = f.read()

    with open(m_csv) as f:
        mi = f.read()

    assert passed
    assert "p1;'StringProperty1';4.0;9606;'gene1|gene2';'p1';'uniprot'" in pr
    assert 'BiologicalEntity' in pr
    assert "m1;'StringProperty1';9606;'m1';'mirbase'" in mi
    assert 'ChemicalEntity' in mi
