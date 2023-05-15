import os

import pytest


@pytest.mark.parametrize('l', [4], scope='function')
def test_arango_write_data_headers_import_call(
    bw_arango,
    _get_nodes,
    _get_edges,
):
    # four proteins, four miRNAs
    nodes = _get_nodes

    edges = _get_edges

    p1 = bw_arango.write_nodes(nodes[:4])
    p2 = bw_arango.write_nodes(nodes[4:])
    p3 = bw_arango.write_edges(edges[:4])
    p4 = bw_arango.write_edges(edges[4:])

    assert all([p1, p2, p3, p4])

    bw_arango.write_import_call()

    tmp_path = bw_arango.outdir

    ph_csv = os.path.join(tmp_path, 'Protein-header.csv')
    pp_1_csv = os.path.join(tmp_path, 'Protein-part000.csv')
    pp_2_csv = os.path.join(tmp_path, 'Protein-part001.csv')
    mh_csv = os.path.join(tmp_path, 'MicroRNA-header.csv')
    mp_1_csv = os.path.join(tmp_path, 'MicroRNA-part000.csv')
    mp_2_csv = os.path.join(tmp_path, 'MicroRNA-part001.csv')
    dh_csv = os.path.join(tmp_path, 'PERTURBED_IN_DISEASE-header.csv')
    dp_1_csv = os.path.join(tmp_path, 'PERTURBED_IN_DISEASE-part000.csv')
    dp_2_csv = os.path.join(tmp_path, 'PERTURBED_IN_DISEASE-part001.csv')
    muh_csv = os.path.join(tmp_path, 'Is_Mutated_In-header.csv')
    mup_1_csv = os.path.join(tmp_path, 'Is_Mutated_In-part000.csv')
    mup_2_csv = os.path.join(tmp_path, 'Is_Mutated_In-part001.csv')
    call_csv = os.path.join(tmp_path, 'arangodb-import-call.sh')

    with open(ph_csv) as f:
        ph = f.read()
    with open(pp_1_csv) as f:
        pp_1 = f.readlines()
    with open(pp_2_csv) as f:
        pp_2 = f.readlines()
    with open(mh_csv) as f:
        mh = f.read()
    with open(mp_1_csv) as f:
        mp_1 = f.readlines()
    with open(mp_2_csv) as f:
        mp_2 = f.readlines()
    with open(dh_csv) as f:
        dh = f.read()
    with open(dp_1_csv) as f:
        dp_1 = f.readlines()
    with open(dp_2_csv) as f:
        dp_2 = f.readlines()
    with open(muh_csv) as f:
        muh = f.read()
    with open(mup_1_csv) as f:
        mup_1 = f.readlines()
    with open(mup_2_csv) as f:
        mup_2 = f.readlines()
    with open(call_csv) as f:
        call = f.read()

    assert ph == '_key,name,score,taxon,genes,id,preferred_id'
    assert mh == '_key,name,taxon,id,preferred_id'
    assert '_from' in dh
    assert '_to' in dh
    assert '_from' in muh
    assert '_to' in muh
    assert len(pp_1) == len(pp_2) == len(mp_1) == len(mp_2) == len(dp_1) == len(
        dp_2
    ) == len(mup_1) == len(mup_2) == 2
    assert 'arangoimp --type csv' in call
    assert '--collection proteins' in call
    assert 'MicroRNA-part' in call

    # custom import call executable path
    bw_arango.import_call_bin_prefix = 'custom/path/to/'

    os.remove(call_csv)
    bw_arango.write_import_call()

    with open(call_csv) as f:
        call = f.read()

    assert 'custom/path/to/arangoimp --type csv' in call
