import pytest


@pytest.mark.parametrize('l', [4], scope='module')
def test_arango_write_node_data_headers_import_call(
    bw_arango, path, _get_nodes
):
    # four proteins, four miRNAs
    nodes = _get_nodes

    passed = bw_arango.write_nodes(nodes[:4])
    passed = bw_arango.write_nodes(nodes[4:])
    bw_arango.write_import_call()

    assert passed

    p_csv = os.path.join(path, 'Protein-header.csv')
    m_csv = os.path.join(path, 'MicroRNA-header.csv')
    call = os.path.join(path, 'arangodb-import-call.sh')

    with open(p_csv) as f:
        p = f.read()
    with open(m_csv) as f:
        m = f.read()
    with open(call) as f:
        c = f.read()

    assert p == '_key,name,score,taxon,genes,id,preferred_id'
    assert m == '_key,name,taxon,id,preferred_id'
    assert 'arangoimp --type csv' in c
    assert '--collection proteins' in c
    assert 'MicroRNA-part.' in c

    # custom import call executable path
    bw_arango.import_call_bin_prefix = 'custom/path/to/'

    os.remove(call)
    bw_arango.write_import_call()

    with open(call) as f:
        c = f.read()

    assert 'custom/path/to/arangoimp --type csv' in c

    # custom file prefix
    # TODO
