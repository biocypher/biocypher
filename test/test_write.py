import os
import re
import random
import string
import tempfile

import pytest

from biocypher._write import BatchWriter
from biocypher._entity import (
    Edge,
    Node,
    RelAsNode,
)
from biocypher._meta import VersionNode
from biocypher._driver import Driver
from biocypher._biolink import BiolinkAdapter

__all__ = [
    "bw",
    "get_random_string",
    "test_RelAsNode_implementation",
    "test_accidental_exact_batch_size",
    "test_create_import_call",
    "test_inconsistent_properties",
    "test_write_edge_data_and_headers",
    "test_write_edge_data_from_gen",
    "test_write_edge_data_from_large_gen",
    "test_write_edge_data_from_list",
    "test_write_edge_data_from_list_no_props",
    "test_write_mixed_edges",
    "test_write_node_data_and_headers",
    "test_write_node_data_from_gen",
    "test_write_node_data_from_gen_no_props",
    "test_write_node_data_from_large_gen",
    "test_write_node_data_from_list",
    "test_writer_and_output_dir",
]


def get_random_string(length):

    # choose from all lowercase letter
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(length))


path = os.path.join(
    tempfile.gettempdir(),
    f"biocypher-test-{get_random_string(5)}",
)
os.makedirs(path, exist_ok=True)


def _get_nodes(l: int) -> list:

    nodes = []

    for i in range(int(l)):

        bnp = Node(
            id=f"p{i+1}",
            label="protein",
            id_type="uniprot",
            props={
                "score": 4 / (i + 1),
                "name": "StringProperty1",
                "taxon": 9606,
            },
        )
        nodes.append(bnp)
        bnm = Node(
            id=f"m{i+1}",
            label="microRNA",
            id_type="mirbase",
            props={"name": "StringProperty1", "taxon": 9606},
        )
        nodes.append(bnm)

    return nodes


def _get_edges(l):

    edges = []

    for i in range(int(l)):

        e1 = Edge(
            source=f"p{i}",
            target=f"p{i + 1}",
            label="PERTURBED_IN_DISEASE",
            props={
                "residue": "T253",
                "level": 4,
                "directional": True,
                "score": .78,
            },
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e1)
        e2 = Edge(
            source=f"m{i}",
            target=f"p{i + 1}",
            label="Is_Mutated_In",
            props={"site": "3-UTR", "confidence": 1},
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e2)

    return edges


def _get_rel_as_nodes(l):

    rels = []

    for i in range(int(l)):

        n = Node(
            id=f"i{i+1}",
            label="post translational interaction",
            props={"directed": True, "effect": -1},
        )
        e1 = Edge(
            source=f"i{i+1}",
            target=f"p{i+1}",
            label="IS_SOURCE_OF",
        )
        e2 = Edge(
            source=f"i{i}",
            target=f"p{i + 2}",
            label="IS_TARGET_OF",
        )
        rels.append(RelAsNode(n, e1, e2))

    return rels


def unformat(s: str) -> str:
    """
    Removes whitespace and line breaks from a string.
    """

    rewhite = re.compile('[\s\n\t\r]+')

    return rewhite.sub(' ', s)


@pytest.fixture
def version_node():
    return VersionNode(
        from_config=True,
        config_file="biocypher/_config/test_schema_config.yaml",
        offline=True,
    )


@pytest.fixture
def bw(version_node):

    bl_adapter = BiolinkAdapter(schema=version_node.schema)
    bw = BatchWriter(
        schema=version_node.schema,
        bl_adapter=bl_adapter,
        dirname=path,
        delimiter=";",
        array_delimiter="|",
        quote="'",
    )

    yield bw

    # teardown
    for f in os.listdir(path):
        os.remove(os.path.join(path, f))
    os.rmdir(path)


def test_writer_and_output_dir(bw):

    assert (
        os.path.isdir(path) and isinstance(bw, BatchWriter) and bw.delim == ";"
    )


def test_write_node_data_headers_import_call(bw):
    # four proteins, four miRNAs
    nodes = _get_nodes(8)

    passed_0 = bw.write(nodes[:4])
    passed_1 = bw.write(nodes[4:])
    bw.write_call()

    p_csv = os.path.join(path, "Protein-header.csv")
    m_csv = os.path.join(path, "Microrna-header.csv")
    call = os.path.join(path, "neo4j-admin-import-call.sh")

    with open(p_csv) as f:
        p = f.read()
    with open(m_csv) as f:
        m = f.read()
    with open(call) as f:
        c = f.read()

    assert passed_0
    assert passed_1
    assert unformat(p) == (
        ':ID;id:string;id_type:string;name:string;'
        'score:double;taxon:long;:LABEL'
    )
    assert unformat(m) == (
        ':ID;id:string;id_type:string;name:string;taxon:long;:LABEL'
    )
    assert unformat(c) == unformat(
        'neo4j-admin import --database=neo4j --delimiter=";" '
        '--array-delimiter="|" --quote="\'" '
        '--skip-bad-relationships=false --skip-duplicate-nodes=false '
        f'--nodes="{path}/Protein-header.csv,{path}/Protein-part.*" '
        f'--nodes="{path}/Microrna-header.csv,{path}/Microrna-part.*"'
    )


def test_property_types(bw):
    nodes = [
        Node(
            id=f"p{i+1}",
            label="protein",
            props={
                "score": 4 / (i + 1),
                "name": "StringProperty1",
                "taxon": 9606,
            },
        )
        for i in range(4)
    ]

    passed = bw.write(nodes, batch_size=1e6)

    d_csv = os.path.join(path, "Protein-part000.csv")
    h_csv = os.path.join(path, "Protein-header.csv")

    with open(d_csv) as f:
        data = f.read()

    with open(h_csv) as f:
        header = f.read()

    assert passed
    assert header == (
        ':ID;id:string;id_type:string;name:string;'
        'score:double;taxon:long;:LABEL'
    )
    assert data == (
        'p1;p1;id;StringProperty1;4.0;9606;Protein\n'
        'p2;p2;id;StringProperty1;2.0;9606;Protein\n'
        'p3;p3;id;StringProperty1;1.3333333333333333;9606;Protein\n'
        'p4;p4;id;StringProperty1;1.0;9606;Protein'
    )


def test_write_node_data_from_list(bw):
    nodes = _get_nodes(4)

    passed = bw._write_records(nodes, batch_size=1e6)

    p_csv = os.path.join(path, "Protein-part000.csv")
    m_csv = os.path.join(path, "Microrna-part000.csv")

    with open(p_csv) as f:
        pr = f.read()

    with open(m_csv) as f:
        mi = f.read()

    assert passed
    assert pr == (
        'p1;p1;uniprot;StringProperty1;4.0;9606;Protein\n'
        'p2;p2;uniprot;StringProperty1;2.0;9606;Protein\n'
        'p3;p3;uniprot;StringProperty1;1.3333333333333333;9606;Protein\n'
        'p4;p4;uniprot;StringProperty1;1.0;9606;Protein'
    )
    assert mi == (
        'm1;m1;mirbase;StringProperty1;9606;Microrna\n'
        'm2;m2;mirbase;StringProperty1;9606;Microrna\n'
        'm3;m3;mirbase;StringProperty1;9606;Microrna\n'
        'm4;m4;mirbase;StringProperty1;9606;Microrna'
    )


def test_write_node_data_from_gen(bw):
    nodes = _get_nodes(4)

    node_gen = (n for n in nodes)

    passed = bw._write_records(node_gen, batch_size=1e6)

    p_csv = os.path.join(path, "Protein-part000.csv")
    m_csv = os.path.join(path, "Microrna-part000.csv")

    with open(p_csv) as f:
        pr = f.read()

    with open(m_csv) as f:
        mi = f.read()

    assert passed
    assert pr == (
        'p1;p1;uniprot;StringProperty1;4.0;9606;Protein\n'
        'p2;p2;uniprot;StringProperty1;2.0;9606;Protein\n'
        'p3;p3;uniprot;StringProperty1;1.3333333333333333;9606;Protein\n'
        'p4;p4;uniprot;StringProperty1;1.0;9606;Protein'
    )
    assert mi == (
        'm1;m1;mirbase;StringProperty1;9606;Microrna\n'
        'm2;m2;mirbase;StringProperty1;9606;Microrna\n'
        'm3;m3;mirbase;StringProperty1;9606;Microrna\n'
        'm4;m4;mirbase;StringProperty1;9606;Microrna'
    )


def test_write_node_data_from_gen_no_props(bw):

    nodes = [
        Node(
            id = f'{"m" if i % 2 else "p"}{i // 2 + 1}',
            label = 'microRNA' if i % 2 else 'protein',
            props = None if i % 2 else {
                'score': 4 / (i // 2 + 1),
                'name': 'StringProperty1',
                'taxon': 9606,
            },
        )
        for i in range(8)
    ]

    node_gen = (n for n in nodes)

    passed = bw._write_records(node_gen, batch_size=1e6)

    p_csv = os.path.join(path, 'Protein-part000.csv')
    m_csv = os.path.join(path, 'Microrna-part000.csv')

    with open(p_csv) as f:
        pr = f.read()

    with open(m_csv) as f:
        mi = f.read()

    assert passed
    assert pr == (
        'p1;p1;id;StringProperty1;4.0;9606;Protein\n'
        'p2;p2;id;StringProperty1;2.0;9606;Protein\n'
        'p3;p3;id;StringProperty1;1.3333333333333333;9606;Protein\n'
        'p4;p4;id;StringProperty1;1.0;9606;Protein'
    )
    assert mi == (
        'm1;m1;id;Microrna\n'
        'm2;m2;id;Microrna\n'
        'm3;m3;id;Microrna\n'
        'm4;m4;id;Microrna'
    )


def test_write_node_data_from_large_gen(bw):

    nodes = _get_nodes(1e4 + 4)

    node_gen = (n for n in nodes)

    passed = bw._write_records(node_gen, batch_size=1e4)

    p0_csv = os.path.join(path, 'Protein-part000.csv')
    m0_csv = os.path.join(path, 'Microrna-part000.csv')
    p1_csv = os.path.join(path, 'Protein-part001.csv')
    m1_csv = os.path.join(path, 'Microrna-part001.csv')

    pr_lines = sum(1 for _ in open(p0_csv))
    mi_lines = sum(1 for _ in open(m0_csv))
    pr_lines1 = sum(1 for _ in open(p1_csv))
    mi_lines1 = sum(1 for _ in open(m1_csv))

    assert passed
    assert pr_lines == 1e4
    assert mi_lines == 1e4
    assert pr_lines1 == 4
    assert mi_lines1 == 4


def test_too_many_properties(bw):

    nodes = _get_nodes(1)

    bn1 = Node(
        id = 'p0',
        label = 'protein',
        props = {
            'p1': get_random_string(4),
            'p2': get_random_string(8),
            'p3': get_random_string(16),
            'p4': get_random_string(16),
        },
    )
    nodes.append(bn1)

    node_gen = (n for n in nodes)

    passed = bw._write_records(node_gen, batch_size = 1e4)

    assert not passed


def test_not_enough_properties(bw):

    nodes = _get_nodes(1)

    bn1 = Node(
        id='p0',
        label='protein',
        props={'p1': get_random_string(4)},
    )
    nodes.append(bn1)
    node_gen = (n for n in nodes)

    passed = bw._write_records(node_gen, batch_size = 1e4)

    p0_csv = os.path.join(path, 'Protein-part000.csv')

    assert not passed
    assert not os.path.exists(p0_csv)


def test_write_none_type_property_and_order_invariance(bw):

    # as introduced by translation using defined properties in
    # schema_config.yaml
    nodes = [
        Node(
            id = 'p1',
            label = 'protein',
            props = {'taxon': 9606, 'score': 1, 'name': None},
        ),
        Node(
            id = 'p2',
            label='protein',
            props = {'name': None, 'score': 2, 'taxon': 9606},
        ),
        Node(
            id = 'm1',
            label = 'microRNA',
            props = {'name': None, 'taxon': 9606},
        ),
    ]

    node_gen = (n for n in nodes)

    passed = bw._write_records(node_gen, batch_size = 1e4)

    p0_csv = os.path.join(path, 'Protein-part000.csv')

    with open(p0_csv) as f:
        p = f.read()

    assert passed
    assert p == (
        'p1;p1;id;;1;9606;Protein\n'
        'p2;p2;id;;2;9606;Protein'
    )


def test_accidental_exact_batch_size(bw):

    nodes = _get_nodes(1e4)

    node_gen = (n for n in nodes)

    passed = bw.write(node_gen, batch_size = 1e4)

    p0_csv = os.path.join(path, 'Protein-part000.csv')
    m0_csv = os.path.join(path, 'Microrna-part000.csv')
    p1_csv = os.path.join(path, 'Protein-part001.csv')
    m1_csv = os.path.join(path, 'Microrna-part001.csv')

    pr_lines = sum(1 for _ in open(p0_csv))
    mi_lines = sum(1 for _ in open(m0_csv))

    ph_csv = os.path.join(path, 'Protein-header.csv')
    mh_csv = os.path.join(path, 'Microrna-header.csv')

    with open(ph_csv) as f:
        p_header = f.read()

    with open(mh_csv) as f:
        m_header = f.read()

    assert passed
    assert pr_lines == 1e4
    assert mi_lines == 1e4
    assert not os.path.exists(p1_csv)
    assert not os.path.exists(m1_csv)
    assert p_header == (
        ':ID;id:string;id_type:string;name:string;'
        'score:double;taxon:long;:LABEL'
    )
    assert m_header == (
        ':ID;id:string;id_type:string;'
        'name:string;taxon:long;:LABEL'
    )


def test_write_edge_data_from_gen(bw):

    edges = _get_edges(4)

    edge_gen = (e for e in edges)

    passed = bw._write_records(edge_gen, batch_size = 1e4)

    pid_csv = os.path.join(path, "PERTURBED_IN_DISEASE-part000.csv")
    imi_csv = os.path.join(path, "IS_MUTATED_IN-part000.csv")

    with open(pid_csv) as f:
        pid_contents = f.read()

    with open(imi_csv) as f:
        imi_contents = f.read()

    assert passed

    assert pid_contents == (
        'p0;True;4;T253;0.78;p1;PERTURBED_IN_DISEASE\n'
        'p1;True;4;T253;0.78;p2;PERTURBED_IN_DISEASE\n'
        'p2;True;4;T253;0.78;p3;PERTURBED_IN_DISEASE\n'
        'p3;True;4;T253;0.78;p4;PERTURBED_IN_DISEASE'
    )
    assert imi_contents == (
        'm0;1;3-UTR;p1;IS_MUTATED_IN\n'
        'm1;1;3-UTR;p2;IS_MUTATED_IN\n'
        'm2;1;3-UTR;p3;IS_MUTATED_IN\n'
        'm3;1;3-UTR;p4;IS_MUTATED_IN'
    )


def test_write_edge_data_from_large_gen(bw):

    edges = _get_edges(1e4 + 4)

    edge_gen = (e for e in edges)

    passed = bw._write_records(edge_gen, batch_size = 1e4)

    apl0_csv = os.path.join(path, 'PERTURBED_IN_DISEASE-part000.csv')
    ips0_csv = os.path.join(path, 'IS_MUTATED_IN-part000.csv')
    apl1_csv = os.path.join(path, 'PERTURBED_IN_DISEASE-part001.csv')
    ips1_csv = os.path.join(path, 'IS_MUTATED_IN-part001.csv')

    pid_lines0 = sum(1 for _ in open(apl0_csv))
    imi_lines0 = sum(1 for _ in open(ips0_csv))
    pid_lines1 = sum(1 for _ in open(apl1_csv))
    imi_lines1 = sum(1 for _ in open(ips1_csv))

    assert passed
    assert pid_lines0 == 1e4
    assert imi_lines0 == 1e4
    assert pid_lines1 == 4
    assert imi_lines1 == 4


def test_write_edge_data_from_list(bw):

    edges = _get_edges(4)

    passed = bw._write_records(edges, batch_size = 1e4)
    pid_csv = os.path.join(path, 'PERTURBED_IN_DISEASE-part000.csv')
    imi_csv = os.path.join(path, 'IS_MUTATED_IN-part000.csv')

    with open(pid_csv) as f:
        pid_contents = f.read()

    with open(imi_csv) as f:
        imi_contents = f.read()

    assert passed
    assert pid_contents == (
        'p0;True;4;T253;0.78;p1;PERTURBED_IN_DISEASE\n'
        'p1;True;4;T253;0.78;p2;PERTURBED_IN_DISEASE\n'
        'p2;True;4;T253;0.78;p3;PERTURBED_IN_DISEASE\n'
        'p3;True;4;T253;0.78;p4;PERTURBED_IN_DISEASE'
    )
    assert imi_contents == (
        'm0;1;3-UTR;p1;IS_MUTATED_IN\n'
        'm1;1;3-UTR;p2;IS_MUTATED_IN\n'
        'm2;1;3-UTR;p3;IS_MUTATED_IN\n'
        'm3;1;3-UTR;p4;IS_MUTATED_IN'
    )


def test_write_edge_data_from_list_no_props(bw):

    edges = [
        Edge(
            source = f'{"m" if i % 2 else "p"}{i // 2}',
            target = f'p{i // 2 + 1}',
            label = 'IS_MUTATED_IN' if i % 2 else 'PERTURBED_IN_DISEASE',
        )
        for i in range(8)
    ]

    passed = bw.write(edges, batch_size = 1e4)

    pid_csv = os.path.join(path, 'PERTURBED_IN_DISEASE-part000.csv')
    imi_csv = os.path.join(path, 'IS_MUTATED_IN-part000.csv')

    assert not passed
    assert not os.path.exists(pid_csv)
    assert not is.path.exists(imi.csv)


def test_write_edge_data_headers_import_call(bw):

    edges = _get_edges(8)
    nodes = _get_nodes(8)

    edge_gen0 = (e for e in edges[:4])
    edge_gen1 = (e for e in edges[4:])

    passed_e0 = bw.write(edge_gen0)
    passed_e1 = bw.write(edge_gen1)
    passed_n = bw.write(nodes)

    bw.write_call()

    pid_csv = os.path.join(path, 'PERTURBED_IN_DISEASE-header.csv')
    imi_csv = os.path.join(path, 'IS_MUTATED_IN-header.csv')
    call_sh = os.path.join(path, 'neo4j-admin-import-call.sh')

    with open(pid_csv) as f:
        pid_header = f.read()

    with open(imi_csv) as f:
        imi_header = f.read()

    with open(call_sh) as f:
        the_call = f.read()

    assert passed_e0
    assert passed_e1
    assert passed_n
    assert pid_header == (
        ':START_ID;directional:boolean;level:long;'
        'residue:string;score:double;:END_ID;:TYPE'
    )
    assert imi_header == ':START_ID;confidence:long;site:string;:END_ID;:TYPE'
    assert unformat(the_call) == (
        'neo4j-admin import --database=neo4j --delimiter=";" '
        '--array-delimiter="|" --quote="\'" --skip-bad-relationships=false '
        '--skip-duplicate-nodes=false '
        '--relationships="'
            f'{path}/PERTURBED_IN_DISEASE-header.csv,'
            f'{path}/PERTURBED_IN_DISEASE-part.*" '
        '--relationships="'
            f'{path}/IS_MUTATED_IN-header.csv,'
            f'{path}/IS_MUTATED_IN-part.*" '
        '--nodes="'
            f'{path}/Protein-header.csv,'
            f'{path}/Protein-part.*" '
        '--nodes="'
            f'{path}/Microrna-header.csv,'
            f'{path}/Microrna-part.*"'
    )


def test_write_duplicate_edges(bw):
    edges = _get_edges(4)
    edges.append(edges[0])

    passed = bw.write(edges)

    ptl_csv = os.path.join(path, "PERTURBED_IN_DISEASE-part000.csv")
    pts_csv = os.path.join(path, "Is_Mutated_In-part000.csv")

    l = sum(1 for _ in open(ptl_csv))
    c = sum(1 for _ in open(pts_csv))

    assert passed and l == 4 and c == 4


def test_relasnode_implementation(bw):
    trips = _get_rel_as_nodes(4)

    def gen(lis):
        yield from lis

    passed = bw.write(gen(trips))

    iso_csv = os.path.join(path, "IS_SOURCE_OF-part000.csv")
    ito_csv = os.path.join(path, "IS_TARGET_OF-part000.csv")
    pmi_csv = os.path.join(path, "PostTranslationalInteraction-part000.csv")

    with open(iso_csv) as f:
        s = f.read()
    with open(ito_csv) as f:
        t = f.read()
    with open(pmi_csv) as f:
        p = f.read()

    assert (
        passed
        and s
        == "i1;p1;IS_SOURCE_OF\ni2;p2;IS_SOURCE_OF\ni3;p3;IS_SOURCE_OF\ni4;p4;IS_SOURCE_OF\n"
        and t
        == "i0;p2;IS_TARGET_OF\ni1;p3;IS_TARGET_OF\ni2;p4;IS_TARGET_OF\ni3;p5;IS_TARGET_OF\n"
        and p
        == "i1;True;-1;'i1';'id';PostTranslationalInteraction|PairwiseMolecularInteraction|PairwiseGeneToGeneInteraction|GeneToGeneAssociation|Association|Entity\ni2;True;-1;'i2';'id';PostTranslationalInteraction|PairwiseMolecularInteraction|PairwiseGeneToGeneInteraction|GeneToGeneAssociation|Association|Entity\ni3;True;-1;'i3';'id';PostTranslationalInteraction|PairwiseMolecularInteraction|PairwiseGeneToGeneInteraction|GeneToGeneAssociation|Association|Entity\ni4;True;-1;'i4';'id';PostTranslationalInteraction|PairwiseMolecularInteraction|PairwiseGeneToGeneInteraction|GeneToGeneAssociation|Association|Entity\n"
    )


def test_relasnode_overwrite_behaviour(bw):
    # if rel as node is called from successive write calls, SOURCE_OF,
    # TARGET_OF, and PART_OF should be continued, not overwritten
    trips = _get_rel_as_nodes(8)

    def gen1(lis):
        yield from lis[:5]

    def gen2(lis):
        yield from lis[5:]

    passed1 = bw.write(gen1(trips))
    passed2 = bw.write(gen2(trips))

    iso_csv = os.path.join(path, "IS_SOURCE_OF-part001.csv")

    assert passed1 and passed2 and os.path.exists(iso_csv)


def test_write_mixed_edges(bw):
    mixed = []
    le = 4
    for i in range(le):
        e3 = Edge(
            source=f"p{i+1}",
            target=f"p{i+1}",
            label="PERTURBED_IN_DISEASE",
        )
        mixed.append(e3)

        n = Node(
            f"i{i+1}",
            "post translational interaction",
        )
        e1 = Edge(
            source=f"i{i+1}",
            target=f"p{i+1}",
            label="IS_SOURCE_OF",
        )
        e2 = Edge(
            source=f"i{i}",
            target=f"p{i+2}",
            label="IS_TARGET_OF",
        )
        mixed.append(RelAsNode(n, e1, e2))

    def gen(lis):
        yield from lis

    passed = bw.write(gen(mixed))

    pmi_csv = os.path.join(path, "PostTranslationalInteraction-header.csv")
    iso_csv = os.path.join(path, "IS_SOURCE_OF-header.csv")
    ito_csv = os.path.join(path, "IS_TARGET_OF-header.csv")
    ipt_csv = os.path.join(path, "PERTURBED_IN_DISEASE-header.csv")

    assert (
        passed
        and os.path.exists(pmi_csv)
        and os.path.exists(iso_csv)
        and os.path.exists(ito_csv)
        and os.path.exists(ipt_csv)
    )


def test_create_import_call(bw):
    mixed = []
    le = 4
    for i in range(le):
        n = Node(
            f"i{i+1}",
            "post translational interaction",
        )
        e1 = Edge(
            source=f"i{i+1}",
            target=f"p{i+1}",
            label="IS_SOURCE_OF",
        )
        e2 = Edge(
            source=f"i{i}",
            target=f"p{i+2}",
            label="IS_TARGET_OF",
        )
        mixed.append(RelAsNode(n, e1, e2))

        e3 = Edge(
            source=f"p{i+1}",
            target=f"p{i+1}",
            label="PERTURBED_IN_DISEASE",
        )
        mixed.append(e3)

    def gen(lis):
        yield from lis

    passed = bw.write(gen(mixed))

    call = bw.compile_call()

    assert (
        passed
        and call == 'bin/neo4j-admin import --database=neo4j --delimiter=";" '
        '--array-delimiter="|" --quote="\'" '
        f'--nodes="{path}/PostTranslationalInteraction-header.csv,{path}/PostTranslationalInteraction-part.*" '
        f'--relationships="{path}/IS_SOURCE_OF-header.csv,{path}/IS_SOURCE_OF-part.*" '
        f'--relationships="{path}/IS_TARGET_OF-header.csv,{path}/IS_TARGET_OF-part.*" '
        f'--relationships="{path}/PERTURBED_IN_DISEASE-header.csv,{path}/PERTURBED_IN_DISEASE-part.*" '
    )


def test_write_offline():
    d = Driver(
        offline=True,
        user_schema_config_path="biocypher/_config/test_schema_config.yaml",
        delimiter=",",
        array_delimiter="|",
    )

    nodes = _get_nodes(4)

    passed = d.write_csv(items=nodes, dirname=path)

    p_csv = os.path.join(path, "Protein-part000.csv")
    m_csv = os.path.join(path, "MicroRNA-part000.csv")

    with open(p_csv) as f:
        pr = f.read()

    with open(m_csv) as f:
        mi = f.read()

    assert (
        passed
        and pr
        == 'p1,"StringProperty1",4.0,9606,"p1","uniprot",Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\np2,"StringProperty1",2.0,9606,"p2","uniprot",Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\np3,"StringProperty1",1.3333333333333333,9606,"p3","uniprot",Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\np4,"StringProperty1",1.0,9606,"p4","uniprot",Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\n'
        and mi
        == 'm1,"StringProperty1",9606,"m1","mirbase",MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\nm2,"StringProperty1",9606,"m2","mirbase",MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\nm3,"StringProperty1",9606,"m3","mirbase",MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\nm4,"StringProperty1",9606,"m4","mirbase",MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\n'
    )


def test_duplicate_id(bw):
    nodes = []
    csv = os.path.join(path, "Protein-part000.csv")
    # remove csv file in path
    if os.path.exists(csv):
        os.remove(csv)
    # four proteins, four miRNAs
    for _ in range(2):
        bnp = Node(
            id=f"p1",
            label="protein",
            props={
                "name": "StringProperty1",
                "score": 4.32,
                "taxon": 9606,
            },
        )
        nodes.append(bnp)

    passed = bw.write(nodes)

    with open(csv, 'r') as fp:

        numof_lines = sum(1 for _ in fp)

    assert passed
    assert numof_lines == 1
