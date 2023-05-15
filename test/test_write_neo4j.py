import os

from genericpath import isfile
import pytest

from biocypher._write import _Neo4jBatchWriter
from biocypher._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode


def test_neo4j_writer_and_output_dir(bw):

    tmp_path = bw.outdir

    assert (
        os.path.isdir(tmp_path) and isinstance(bw, _Neo4jBatchWriter) and
        bw.delim == ';'
    )


def test_create_import_call(bw):
    mixed = []
    le = 4
    for i in range(le):
        n = BioCypherNode(
            f'i{i+1}',
            'post translational interaction',
        )
        e1 = BioCypherEdge(
            source_id=f'i{i+1}',
            target_id=f'p{i+1}',
            relationship_label='IS_SOURCE_OF',
        )
        e2 = BioCypherEdge(
            source_id=f'i{i}',
            target_id=f'p{i+2}',
            relationship_label='IS_TARGET_OF',
        )
        mixed.append(BioCypherRelAsNode(n, e1, e2))

        e3 = BioCypherEdge(
            source_id=f'p{i+1}',
            target_id=f'p{i+1}',
            relationship_label='PERTURBED_IN_DISEASE',
        )
        mixed.append(e3)

    def gen(lis):
        yield from lis

    passed = bw.write_edges(gen(mixed))

    call = bw.get_import_call()

    tmp_path = bw.outdir

    assert passed
    assert 'bin/neo4j-admin import --database=neo4j --delimiter=";" ' in call
    assert '--array-delimiter="|" --quote="\'" --force=true ' in call
    assert f'--nodes="{tmp_path}/PostTranslationalInteraction-header.csv,{tmp_path}/PostTranslationalInteraction-part.*" ' in call
    assert f'--relationships="{tmp_path}/IS_SOURCE_OF-header.csv,{tmp_path}/IS_SOURCE_OF-part.*" ' in call
    assert f'--relationships="{tmp_path}/IS_TARGET_OF-header.csv,{tmp_path}/IS_TARGET_OF-part.*" ' in call
    assert f'--relationships="{tmp_path}/PERTURBED_IN_DISEASE-header.csv,{tmp_path}/PERTURBED_IN_DISEASE-part.*" ' in call


@pytest.mark.parametrize('l', [4], scope='module')
def test_neo4j_write_node_data_headers_import_call(bw, _get_nodes):
    # four proteins, four miRNAs
    nodes = _get_nodes

    passed = bw.write_nodes(nodes[:4])
    passed = bw.write_nodes(nodes[4:])
    bw.write_import_call()

    assert passed

    tmp_path = bw.outdir

    p_csv = os.path.join(tmp_path, 'Protein-header.csv')
    m_csv = os.path.join(tmp_path, 'MicroRNA-header.csv')
    call = os.path.join(tmp_path, 'neo4j-admin-import-call.sh')

    with open(p_csv) as f:
        p = f.read()
    with open(m_csv) as f:
        m = f.read()
    with open(call) as f:
        c = f.read()

    assert p == ':ID;name;score:double;taxon:long;genes:string[];id;preferred_id;:LABEL'
    assert m == ':ID;name;taxon:long;id;preferred_id;:LABEL'
    assert 'bin/neo4j-admin import' in c
    assert '--database=neo4j' in c
    assert '--delimiter=";"' in c
    assert '--force=true' in c
    assert '--nodes="' in c
    assert 'Protein-header.csv' in c
    assert 'Protein-part.*"' in c
    assert 'MicroRNA-header.csv' in c
    assert 'MicroRNA-part.*"' in c

    # custom import call executable path
    bw.import_call_bin_prefix = 'custom/path/'

    os.remove(call)
    bw.write_import_call()

    with open(call) as f:
        c = f.read()

    assert 'custom/path/neo4j-admin import' in c

    # custom file prefix
    # TODO


def test_write_hybrid_ontology_nodes(bw):
    nodes = []
    for i in range(4):
        nodes.append(
            BioCypherNode(
                node_id=f'agpl:000{i}',
                node_label='altered gene product level',
                properties={}
            )
        )

    passed = bw.write_nodes(nodes)

    assert passed

    tmp_path = bw.outdir

    h_csv = os.path.join(tmp_path, 'AlteredGeneProductLevel-header.csv')
    p_csv = os.path.join(tmp_path, 'AlteredGeneProductLevel-part000.csv')

    with open(h_csv) as f:
        header = f.read()

    with open(p_csv) as f:
        part = f.read()

    assert header == ':ID;id;preferred_id;:LABEL'
    assert "agpl:0000;'agpl:0000';'id'" in part
    assert 'AlteredGeneProductLevel' in part
    assert 'BiologicalEntity' in part


def test_property_types(bw):
    nodes = []
    for i in range(4):
        bnp = BioCypherNode(
            node_id=f'p{i+1}',
            node_label='protein',
            properties={
                'score': 4 / (i + 1),
                'name': 'StringProperty1',
                'taxon': 9606,
                'genes': ['gene1', 'gene2'],
            },
        )
        nodes.append(bnp)

    passed = bw.write_nodes(nodes, batch_size=1e6)

    tmp_path = bw.outdir

    d_csv = os.path.join(tmp_path, 'Protein-part000.csv')
    h_csv = os.path.join(tmp_path, 'Protein-header.csv')

    with open(d_csv) as f:
        data = f.read()

    with open(h_csv) as f:
        header = f.read()

    assert passed
    assert header == ':ID;name;score:double;taxon:long;genes:string[];id;preferred_id;:LABEL'
    assert "p1;'StringProperty1';4.0;9606;'gene1|gene2';'p1';'id'" in data
    assert 'BiologicalEntity' in data


@pytest.mark.parametrize('l', [4], scope='module')
def test_write_node_data_from_list(bw, _get_nodes):
    nodes = _get_nodes

    passed = bw._write_node_data(nodes, batch_size=1e6)

    tmp_path = bw.outdir

    p_csv = os.path.join(tmp_path, 'Protein-part000.csv')
    m_csv = os.path.join(tmp_path, 'MicroRNA-part000.csv')

    with open(p_csv) as f:
        pr = f.read()

    with open(m_csv) as f:
        mi = f.read()

    assert passed
    assert "p1;'StringProperty1';4.0;9606;'gene1|gene2';'p1';'uniprot'" in pr
    assert 'BiologicalEntity' in pr
    assert "m1;'StringProperty1';9606;'m1';'mirbase'" in mi
    assert 'ChemicalEntity' in mi


@pytest.mark.parametrize('l', [4], scope='module')
def test_write_node_data_from_gen(bw, _get_nodes):
    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(node_gen(nodes), batch_size=1e6)

    tmp_path = bw.outdir

    p_csv = os.path.join(tmp_path, 'Protein-part000.csv')
    m_csv = os.path.join(tmp_path, 'MicroRNA-part000.csv')

    with open(p_csv) as f:
        pr = f.read()

    with open(m_csv) as f:
        mi = f.read()

    assert passed
    assert "p1;'StringProperty1';4.0;9606;'gene1|gene2';'p1';'uniprot'" in pr
    assert 'BiologicalEntity' in pr
    assert "m1;'StringProperty1';9606;'m1';'mirbase'" in mi
    assert 'ChemicalEntity' in mi


def test_write_node_data_from_gen_no_props(bw):
    nodes = []
    le = 4
    for i in range(le):
        bnp = BioCypherNode(
            node_id=f'p{i+1}',
            node_label='protein',
            properties={
                'score': 4 / (i + 1),
                'name': 'StringProperty1',
                'taxon': 9606,
                'genes': ['gene1', 'gene2'],
            },
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            node_id=f'm{i+1}',
            node_label='microRNA',
        )
        nodes.append(bnm)

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(node_gen(nodes), batch_size=1e6)

    tmp_path = bw.outdir

    p_csv = os.path.join(tmp_path, 'Protein-part000.csv')
    m_csv = os.path.join(tmp_path, 'microRNA-part000.csv')

    with open(p_csv) as f:
        pr = f.read()

    with open(m_csv) as f:
        mi = f.read()

    assert passed
    assert "p1;'StringProperty1';4.0;9606;'gene1|gene2';'p1';'id'" in pr
    assert 'BiologicalEntity' in pr
    assert "m1;'m1';'id'" in mi
    assert 'ChemicalEntity' in mi


@pytest.mark.parametrize('l', [int(1e4 + 4)], scope='module')
def test_write_node_data_from_large_gen(bw, _get_nodes):
    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(
        node_gen(nodes),
        batch_size=int(1e4),
    )  # reduce test time

    tmp_path = bw.outdir

    p0_csv = os.path.join(tmp_path, 'Protein-part000.csv')
    m0_csv = os.path.join(tmp_path, 'MicroRNA-part000.csv')
    p1_csv = os.path.join(tmp_path, 'Protein-part001.csv')
    m1_csv = os.path.join(tmp_path, 'MicroRNA-part001.csv')

    pr_lines = sum(1 for _ in open(p0_csv))
    mi_lines = sum(1 for _ in open(m0_csv))
    pr_lines1 = sum(1 for _ in open(p1_csv))
    mi_lines1 = sum(1 for _ in open(m1_csv))

    assert (
        passed and pr_lines == 1e4 and mi_lines == 1e4 and pr_lines1 == 4 and
        mi_lines1 == 4
    )


@pytest.mark.parametrize('l', [1], scope='module')
def test_too_many_properties(bw, _get_nodes):
    nodes = _get_nodes

    bn1 = BioCypherNode(
        node_id='p0',
        node_label='protein',
        properties={
            'p1': 'StringProperty1',
            'p2': 'StringProperty2',
            'p3': 'StringProperty3',
            'p4': 'StringProperty4',
        },
    )
    nodes.append(bn1)

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(
        node_gen(nodes),
        batch_size=int(1e4),
    )  # reduce test time

    assert not passed


@pytest.mark.parametrize('l', [1], scope='module')
def test_not_enough_properties(bw, _get_nodes):
    nodes = _get_nodes

    bn1 = BioCypherNode(
        node_id='p0',
        node_label='protein',
        properties={'p1': 'StringProperty1'},
    )
    nodes.append(bn1)

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(
        node_gen(nodes),
        batch_size=int(1e4),
    )  # reduce test time

    tmp_path = bw.outdir

    p0_csv = os.path.join(tmp_path, 'Protein-part000.csv')

    assert not passed and not isfile(p0_csv)


def test_write_none_type_property_and_order_invariance(bw):
    # as introduced by translation using defined properties in
    # schema_config.yaml
    nodes = []

    bnp1 = BioCypherNode(
        node_id=f'p1',
        node_label='protein',
        properties={
            'taxon': 9606,
            'score': 1,
            'name': None,
            'genes': None,
        },
    )
    bnp2 = BioCypherNode(
        node_id=f'p2',
        node_label='protein',
        properties={
            'name': None,
            'genes': ['gene1', 'gene2'],
            'score': 2,
            'taxon': 9606,
        },
    )
    bnm = BioCypherNode(
        node_id=f'm1',
        node_label='microRNA',
        properties={
            'name': None,
            'taxon': 9606,
        },
    )
    nodes.append(bnp1)
    nodes.append(bnp2)
    nodes.append(bnm)

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(
        node_gen(nodes),
        batch_size=int(1e4),
    )  # reduce test time

    tmp_path = bw.outdir

    p0_csv = os.path.join(tmp_path, 'Protein-part000.csv')
    with open(p0_csv) as f:
        p = f.read()

    assert passed
    assert "p1;;1;9606;;'p1';'id'" in p
    assert 'BiologicalEntity' in p


@pytest.mark.parametrize('l', [int(1e4)], scope='module')
def test_accidental_exact_batch_size(bw, _get_nodes):
    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    passed = bw.write_nodes(
        node_gen(nodes),
        batch_size=int(1e4),
    )  # reduce test time

    tmp_path = bw.outdir

    p0_csv = os.path.join(tmp_path, 'Protein-part000.csv')
    m0_csv = os.path.join(tmp_path, 'MicroRNA-part000.csv')
    p1_csv = os.path.join(tmp_path, 'Protein-part001.csv')
    m1_csv = os.path.join(tmp_path, 'MicroRNA-part001.csv')

    pr_lines = sum(1 for _ in open(p0_csv))
    mi_lines = sum(1 for _ in open(m0_csv))

    ph_csv = os.path.join(tmp_path, 'Protein-header.csv')
    mh_csv = os.path.join(tmp_path, 'MicroRNA-header.csv')

    with open(ph_csv) as f:
        p = f.read()
    with open(mh_csv) as f:
        m = f.read()

    assert (
        passed and pr_lines == 1e4 and mi_lines == 1e4 and
        not isfile(p1_csv) and not isfile(m1_csv) and p ==
        ':ID;name;score:double;taxon:long;genes:string[];id;preferred_id;:LABEL'
        and m == ':ID;name;taxon:long;id;preferred_id;:LABEL'
    )


@pytest.mark.parametrize('l', [4], scope='module')
def test_write_edge_data_from_gen(bw, _get_edges):
    edges = _get_edges

    def edge_gen(edges):
        yield from edges

    passed = bw._write_edge_data(edge_gen(edges), batch_size=int(1e4))

    tmp_path = bw.outdir

    pid_csv = os.path.join(tmp_path, 'PERTURBED_IN_DISEASE-part000.csv')
    imi_csv = os.path.join(tmp_path, 'Is_Mutated_In-part000.csv')

    with open(pid_csv) as f:
        l = f.read()
    with open(imi_csv) as f:
        c = f.read()

    assert passed
    assert "p0;'T253';4;p1;PERTURBED_IN_DISEASE" in l
    assert "p1;'T253';4;p2;PERTURBED_IN_DISEASE" in l
    assert '\n' in l
    assert "m0;'3-UTR';1;p1;Is_Mutated_In" in c
    assert "m1;'3-UTR';1;p2;Is_Mutated_In" in c
    assert '\n' in c


@pytest.mark.parametrize('l', [int(1e4 + 4)], scope='module')
def test_write_edge_data_from_large_gen(bw, _get_edges):

    edges = _get_edges

    def edge_gen(edges):
        yield from edges

    passed = bw._write_edge_data(edge_gen(edges), batch_size=int(1e4))

    tmp_path = bw.outdir

    apl0_csv = os.path.join(tmp_path, 'PERTURBED_IN_DISEASE-part000.csv')
    ips0_csv = os.path.join(tmp_path, 'Is_Mutated_In-part000.csv')
    apl1_csv = os.path.join(tmp_path, 'PERTURBED_IN_DISEASE-part001.csv')
    ips1_csv = os.path.join(tmp_path, 'Is_Mutated_In-part001.csv')

    l_lines0 = sum(1 for _ in open(apl0_csv))
    c_lines0 = sum(1 for _ in open(ips0_csv))
    l_lines1 = sum(1 for _ in open(apl1_csv))
    c_lines1 = sum(1 for _ in open(ips1_csv))

    assert (
        passed and l_lines0 == 1e4 and c_lines0 == 1e4 and l_lines1 == 4 and
        c_lines1 == 4
    )


@pytest.mark.parametrize('l', [4], scope='module')
def test_write_edge_data_from_list(bw, _get_edges):
    edges = _get_edges

    passed = bw._write_edge_data(edges, batch_size=int(1e4))

    tmp_path = bw.outdir

    apl_csv = os.path.join(tmp_path, 'PERTURBED_IN_DISEASE-part000.csv')
    ips_csv = os.path.join(tmp_path, 'Is_Mutated_In-part000.csv')

    with open(apl_csv) as f:
        l = f.read()
    with open(ips_csv) as f:
        c = f.read()

    assert passed
    assert "p0;'T253';4;p1;PERTURBED_IN_DISEASE" in l
    assert "p1;'T253';4;p2;PERTURBED_IN_DISEASE" in l
    assert '\n' in l
    assert "m0;'3-UTR';1;p1;Is_Mutated_In" in c
    assert "m1;'3-UTR';1;p2;Is_Mutated_In" in c
    assert '\n' in c


def test_write_edge_data_from_list_no_props(bw):
    le = 4
    edges = []
    for i in range(le):
        e1 = BioCypherEdge(
            source_id=f'p{i}',
            target_id=f'p{i + 1}',
            relationship_label='PERTURBED_IN_DISEASE',
        )
        edges.append(e1)
        e2 = BioCypherEdge(
            source_id=f'm{i}',
            target_id=f'p{i + 1}',
            relationship_label='Is_Mutated_In',
        )
        edges.append(e2)

    passed = bw._write_edge_data(edges, batch_size=int(1e4))

    tmp_path = bw.outdir

    ptl_csv = os.path.join(tmp_path, 'PERTURBED_IN_DISEASE-part000.csv')
    pts_csv = os.path.join(tmp_path, 'Is_Mutated_In-part000.csv')

    with open(ptl_csv) as f:
        l = f.read()
    with open(pts_csv) as f:
        c = f.read()

    assert passed
    assert 'p0;p1;PERTURBED_IN_DISEASE' in l
    assert 'p1;p2;PERTURBED_IN_DISEASE' in l
    assert '\n' in l
    assert 'm0;p1;Is_Mutated_In' in c
    assert 'm1;p2;Is_Mutated_In' in c
    assert '\n' in c


@pytest.mark.parametrize('l', [8], scope='module')
def test_write_edge_data_headers_import_call(bw, _get_nodes, _get_edges):
    edges = _get_edges

    nodes = _get_nodes

    def edge_gen1(edges):
        yield from edges[:4]

    def edge_gen2(edges):
        yield from edges[4:]

    passed = bw.write_edges(edge_gen1(edges))
    assert passed

    passed = bw.write_edges(edge_gen2(edges))
    assert passed

    passed = bw.write_nodes(nodes)
    assert passed

    bw.write_import_call()

    tmp_path = bw.outdir

    ptl_csv = os.path.join(tmp_path, 'PERTURBED_IN_DISEASE-header.csv')
    pts_csv = os.path.join(tmp_path, 'Is_Mutated_In-header.csv')
    call_csv = os.path.join(tmp_path, 'neo4j-admin-import-call.sh')

    with open(ptl_csv) as f:
        l = f.read()
    with open(pts_csv) as f:
        c = f.read()
    with open(call_csv) as f:
        call = f.read()

    assert l == ':START_ID;residue;level:long;:END_ID;:TYPE'
    assert c == ':START_ID;site;confidence:long;:END_ID;:TYPE'

    assert 'bin/neo4j-admin import' in call
    assert '--database=neo4j' in call
    assert '--delimiter=";"' in call
    assert '--force=true' in call
    assert '--nodes="' in call
    assert 'PERTURBED_IN_DISEASE' in call
    assert 'Is_Mutated_In' in call


@pytest.mark.parametrize('l', [4], scope='module')
def test_write_duplicate_edges(bw, _get_edges):
    edges = _get_edges
    edges.append(edges[0])

    passed = bw.write_edges(edges)

    tmp_path = bw.outdir

    ptl_csv = os.path.join(tmp_path, 'PERTURBED_IN_DISEASE-part000.csv')
    pts_csv = os.path.join(tmp_path, 'Is_Mutated_In-part000.csv')

    l = sum(1 for _ in open(ptl_csv))
    c = sum(1 for _ in open(pts_csv))

    assert passed and l == 4 and c == 4


def test_BioCypherRelAsNode_implementation(bw):
    trips = _get_rel_as_nodes(4)

    def gen(lis):
        yield from lis

    passed = bw.write_edges(gen(trips))

    tmp_path = bw.outdir

    iso_csv = os.path.join(tmp_path, 'IS_SOURCE_OF-part000.csv')
    ito_csv = os.path.join(tmp_path, 'IS_TARGET_OF-part000.csv')
    pmi_csv = os.path.join(tmp_path, 'PostTranslationalInteraction-part000.csv')

    with open(iso_csv) as f:
        s = f.read()
    with open(ito_csv) as f:
        t = f.read()
    with open(pmi_csv) as f:
        p = f.read()

    assert passed
    assert 'i1;p1;IS_SOURCE_OF' in s
    assert '\n' in s
    assert 'i0;p2;IS_TARGET_OF' in t
    assert '\n' in t
    assert "i1;True;-1;'i1';'id'" in p
    assert 'Association' in p
    assert '\n' in p


def _get_rel_as_nodes(l):
    rels = []
    for i in range(l):
        n = BioCypherNode(
            node_id=f'i{i+1}',
            node_label='post translational interaction',
            properties={
                'directed': True,
                'effect': -1,
            },
        )
        e1 = BioCypherEdge(
            source_id=f'i{i+1}',
            target_id=f'p{i+1}',
            relationship_label='IS_SOURCE_OF',
        )
        e2 = BioCypherEdge(
            source_id=f'i{i}',
            target_id=f'p{i + 2}',
            relationship_label='IS_TARGET_OF',
        )
        rels.append(BioCypherRelAsNode(n, e1, e2))
    return rels


def test_RelAsNode_overwrite_behaviour(bw):
    # if rel as node is called from successive write calls, SOURCE_OF,
    # TARGET_OF, and PART_OF should be continued, not overwritten
    trips = _get_rel_as_nodes(8)

    def gen1(lis):
        yield from lis[:5]

    def gen2(lis):
        yield from lis[5:]

    passed1 = bw.write_edges(gen1(trips))
    passed2 = bw.write_edges(gen2(trips))

    tmp_path = bw.outdir

    iso_csv = os.path.join(tmp_path, 'IS_SOURCE_OF-part001.csv')

    assert passed1 and passed2 and isfile(iso_csv)


def test_write_mixed_edges(bw):
    mixed = []
    le = 4
    for i in range(le):
        e3 = BioCypherEdge(
            source_id=f'p{i+1}',
            target_id=f'p{i+1}',
            relationship_label='PERTURBED_IN_DISEASE',
        )
        mixed.append(e3)

        n = BioCypherNode(
            f'i{i+1}',
            'post translational interaction',
        )
        e1 = BioCypherEdge(
            source_id=f'i{i+1}',
            target_id=f'p{i+1}',
            relationship_label='IS_SOURCE_OF',
        )
        e2 = BioCypherEdge(
            source_id=f'i{i}',
            target_id=f'p{i+2}',
            relationship_label='IS_TARGET_OF',
        )
        mixed.append(BioCypherRelAsNode(n, e1, e2))

    def gen(lis):
        yield from lis

    passed = bw.write_edges(gen(mixed))

    tmp_path = bw.outdir

    pmi_csv = os.path.join(tmp_path, 'PostTranslationalInteraction-header.csv')
    iso_csv = os.path.join(tmp_path, 'IS_SOURCE_OF-header.csv')
    ito_csv = os.path.join(tmp_path, 'IS_TARGET_OF-header.csv')
    ipt_csv = os.path.join(tmp_path, 'PERTURBED_IN_DISEASE-header.csv')

    assert (
        passed and os.path.isfile(pmi_csv) and os.path.isfile(iso_csv) and
        os.path.isfile(ito_csv) and os.path.isfile(ipt_csv)
    )


def test_duplicate_id(bw):

    nodes = []

    tmp_path = bw.outdir

    csv = os.path.join(tmp_path, 'Protein-part000.csv')

    # remove csv file in path
    if os.path.exists(csv):
        os.remove(csv)

    # four proteins, four miRNAs
    for _ in range(2):
        bnp = BioCypherNode(
            node_id=f'p1',
            node_label='protein',
            properties={
                'name': 'StringProperty1',
                'score': 4.32,
                'taxon': 9606,
                'genes': ['gene1', 'gene2'],
            },
        )
        nodes.append(bnp)

    passed = bw.write_nodes(nodes)

    l_lines0 = sum(1 for _ in open(csv))

    assert passed and l_lines0 == 1


def test_write_synonym(bw):

    nodes = []

    tmp_path = bw.outdir

    csv = os.path.join(tmp_path, 'Complex-part000.csv')

    # remove csv file in path
    if os.path.exists(csv):
        os.remove(csv)
    # four proteins, four miRNAs
    for _ in range(4):
        bnp = BioCypherNode(
            node_id=f'p{_+1}',
            node_label='complex',
            properties={
                'name': 'StringProperty1',
                'score': 4.32,
                'taxon': 9606,
            },
        )
        nodes.append(bnp)

    passed = bw.write_nodes(nodes)

    with open(csv) as f:
        comp = f.read()

    assert passed and os.path.exists(csv)
    assert "p1;'StringProperty1';4.32;9606;'p1';'id'" in comp
    assert 'Complex' in comp

def test_write_strict(bw_strict):

    n1 = BioCypherNode(
        node_id='p1',
        node_label='protein',
        properties={
            'name': 'StringProperty1',
            'score': 4.32,
            'taxon': 9606,
            'genes': ['gene1', 'gene2'],
            'source': 'source1',
            'version': 'version1',
            'licence': 'licence1',
        },
    )

    passed = bw_strict.write_nodes([n1])

    assert passed

    tmp_path = bw_strict.outdir

    csv = os.path.join(tmp_path, 'Protein-part000.csv')

    with open(csv) as f:
        prot = f.read()

    assert "p1;'StringProperty1';4.32;9606;'gene1|gene2';'p1';'id';'source1';'version1';'licence1'" in prot
    assert 'BiologicalEntity' in prot


@pytest.mark.parametrize('l', [4], scope='module')
def test_tab_delimiter(bw_tab, _get_nodes):

    passed = bw_tab.write_nodes(_get_nodes)

    assert passed

    tmp_path = bw_tab.outdir

    header = os.path.join(tmp_path, 'Protein-header.csv')

    with open(header) as f:
        prot = f.read()

    assert '\t' in prot

    call = bw_tab._construct_import_call()

    assert '--delimiter="\\t"' in call
