import os
import random
import string
import tempfile

import pytest

from biocypher._write import BatchWriter
from biocypher._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode
from biocypher._translate import BiolinkAdapter

__all__ = ['bw', 'get_random_string', 'test_BioCypherRelAsNode_implementation', 'test_accidental_exact_batch_size', 'test_create_import_call', 'test_inconsistent_properties', 'test_write_edge_data_and_headers', 'test_write_edge_data_from_gen', 'test_write_edge_data_from_large_gen', 'test_write_edge_data_from_list', 'test_write_edge_data_from_list_no_props', 'test_write_mixed_edges', 'test_write_node_data_and_headers', 'test_write_node_data_from_gen', 'test_write_node_data_from_gen_no_props', 'test_write_node_data_from_large_gen', 'test_write_node_data_from_list', 'test_writer_and_output_dir']


def get_random_string(length):

    # choose from all lowercase letter
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

path = os.path.join(
    tempfile.gettempdir(),
    f'biocypher-test-{get_random_string(5)}',
)
os.makedirs(path, exist_ok = True)

@pytest.fixture
def bw():

    schema = {
        'Protein': {
            'represented_as': 'node',
            'preferred_id': 'UniProtKB',
            'label_in_input': 'protein',
        },
        'microRNA': {
            'represented_as': 'node',
            'preferred_id': 'MIR',
            'label_in_input': 'miRNA',
        },
        'PostTranslationalInteraction': {
            'represented_as': 'edge',
            'source': 'Protein',
            'target': 'Protein',
            'preferred_id': 'PLID',
            'label_in_input': 'POST_TRANSLATIONAL',
        },
        'PostTranscriptionalInteraction': {
            'represented_as': 'edge',
            'source': 'microRNA',
            'target': 'Transcript',
            'preferred_id': 'PCID',
            'label_in_input': 'POST_TRANSCRIPTIONAL',
        },
        'PairwiseMolecularInteraction': {
            'represented_as': 'node',
            'source': 'Protein',
            'target': 'Protein',
            'preferred_id': 'RNID',
            'label_in_input': 'pm_interaction',
        },
    }
    bl_adapter = BiolinkAdapter(leaves=schema)
    bw = BatchWriter(
        schema = schema,
        bl_adapter = bl_adapter,
        path = path,
    )

    yield bw

    # teardown
    for f in os.listdir(path):
        os.remove(os.path.join(path, f))
    os.rmdir(path)


def test_writer_and_output_dir(bw):

    assert (
        os.path.isdir(path) and isinstance(bw, BatchWriter) and bw.delim == ';'
    )


def test_write_node_data_and_headers(bw):
    nodes = []
    # four proteins, four miRNAs
    for i in range(4):
        bnp = BioCypherNode(
            f'p{i+1}',
            'Protein',
            string_property='StringProperty1',
            taxon=9606,
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f'm{i+1}',
            'microRNA',
            string_property='StringProperty1',
            taxon=9606,
        )
        nodes.append(bnm)

    passed = bw.write_nodes(nodes)

    p_csv = os.path.join(path, 'Protein-header.csv')
    m_csv = os.path.join(path, 'microRNA-header.csv')

    with open(p_csv) as f:
        p = f.read()
    with open(m_csv) as f:
        m = f.read()

    assert (
        passed
        and p == ('UniProtKB:ID;string_property;taxon:int;:LABEL')
        and m == ('MIR:ID;string_property;taxon:int;:LABEL')
    )


def test_write_node_data_from_list(bw):
    nodes = []
    # four proteins, four miRNAs
    for i in range(4):
        bnp = BioCypherNode(
            f'p{i+1}',
            'Protein',
            string_property='StringProperty1',
            taxon=9606,
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f'm{i+1}',
            'microRNA',
            string_property='StringProperty1',
            taxon=9606,
        )
        nodes.append(bnm)

    passed = bw._write_node_data(nodes, batch_size=1e6)

    p_csv = os.path.join(path, 'Protein-part000.csv')
    m_csv = os.path.join(path, 'microRNA-part000.csv')

    with open(p_csv) as f:
        pr = f.read()

    with open(m_csv) as f:
        mi = f.read()

    assert (
        passed
        and pr
        == "p1;'StringProperty1';9606;Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\np2;'StringProperty1';9606;Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\np3;'StringProperty1';9606;Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\np4;'StringProperty1';9606;Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\n"
        and mi
        == "m1;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\nm2;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\nm3;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\nm4;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\n"
    )


def test_write_node_data_from_gen(bw):
    nodes = []
    le = 4
    for i in range(le):
        bnp = BioCypherNode(
            f'p{i+1}',
            'Protein',
            string_property='StringProperty1',
            taxon=9606,
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f'm{i+1}',
            'microRNA',
            string_property='StringProperty1',
            taxon=9606,
        )
        nodes.append(bnm)

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(node_gen(nodes), batch_size=1e6)

    p_csv = os.path.join(path, 'Protein-part000.csv')
    m_csv = os.path.join(path, 'microRNA-part000.csv')

    with open(p_csv) as f:
        pr = f.read()

    with open(m_csv) as f:
        mi = f.read()

    assert (
        passed
        and pr
        == "p1;'StringProperty1';9606;Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\np2;'StringProperty1';9606;Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\np3;'StringProperty1';9606;Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\np4;'StringProperty1';9606;Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\n"
        and mi
        == "m1;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\nm2;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\nm3;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\nm4;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\n"
    )


def test_write_node_data_from_gen_no_props(bw):
    nodes = []
    le = 4
    for i in range(le):
        bnp = BioCypherNode(
            f'p{i+1}',
            'Protein',
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f'm{i+1}',
            'microRNA',
        )
        nodes.append(bnm)

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(node_gen(nodes), batch_size=1e6)

    p_csv = os.path.join(path, 'Protein-part000.csv')
    m_csv = os.path.join(path, 'microRNA-part000.csv')

    with open(p_csv) as f:
        pr = f.read()

    with open(m_csv) as f:
        mi = f.read()

    assert (
        passed
        and pr
        == 'p1;Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\np2;Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\np3;Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\np4;Protein|GeneProductMixin|ThingWithTaxon|Polypeptide|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|BiologicalEntity|NamedThing|Entity|GeneOrGeneProduct|MacromolecularMachineMixin\n'
        and mi
        == 'm1;MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\nm2;MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\nm3;MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\nm4;MicroRNA|NoncodingRNAProduct|RNAProduct|GeneProductMixin|Transcript|NucleicAcidEntity|GenomicEntity|PhysicalEssence|OntologyClass|MolecularEntity|ChemicalEntity|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide|NamedThing|Entity|PhysicalEssenceOrOccurrent|ThingWithTaxon|GeneOrGeneProduct|MacromolecularMachineMixin\n'
    )


def test_write_node_data_from_large_gen(bw):
    nodes = []
    le = int(1e4 + 4)
    for i in range(le):
        bnp = BioCypherNode(
            f'p{i+1}',
            'Protein',
            p1=get_random_string(4),
            p2=get_random_string(8),
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f'm{i+1}',
            'microRNA',
            p1=get_random_string(4),
            p2=get_random_string(8),
        )
        nodes.append(bnm)

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(
        node_gen(nodes), batch_size=int(1e4),
    )  # reduce test time

    p0_csv = os.path.join(path, 'Protein-part000.csv')
    m0_csv = os.path.join(path, 'microRNA-part000.csv')
    p1_csv = os.path.join(path, 'Protein-part001.csv')
    m1_csv = os.path.join(path, 'microRNA-part001.csv')

    pr_lines = sum(1 for _ in open(p0_csv))
    mi_lines = sum(1 for _ in open(m0_csv))
    pr_lines1 = sum(1 for _ in open(p1_csv))
    mi_lines1 = sum(1 for _ in open(m1_csv))

    assert (
        passed
        and pr_lines == 1e4
        and mi_lines == 1e4
        and pr_lines1 == 4
        and mi_lines1 == 4
    )


def test_inconsistent_properties(bw):
    nodes = []
    le = 4
    for i in range(le):
        bnp = BioCypherNode(
            f'p{i+1}',
            'Protein',
            p1=get_random_string(4),
            p2=get_random_string(8),
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f'm{i+1}',
            'microRNA',
            p1=get_random_string(4),
            p2=get_random_string(8),
        )
        nodes.append(bnm)

    bn1 = BioCypherNode(
        'p0',
        'Protein',
        p1=get_random_string(4),
        p2=get_random_string(8),
        p3=get_random_string(16),
        p4=get_random_string(16),
    )
    nodes.append(bn1)

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(
        node_gen(nodes), batch_size=int(1e4),
    )  # reduce test time

    assert not passed

    del nodes[-1]
    bn2 = BioCypherNode(
        'p0',
        'Protein',
        p1=get_random_string(4),
    )
    nodes.append(bn2)

    passed = bw._write_node_data(
        node_gen(nodes), batch_size=int(1e4),
    )  # reduce test time

    assert not passed


def test_accidental_exact_batch_size(bw):
    nodes = []
    le = int(1e4)
    for i in range(le):
        bnp = BioCypherNode(
            f'p{i+1}',
            'Protein',
            p1=get_random_string(4),
            taxon=9606,
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f'm{i+1}',
            'microRNA',
            p1=get_random_string(4),
            taxon=9606,
        )
        nodes.append(bnm)

    def node_gen(nodes):
        yield from nodes

    passed = bw.write_nodes(
        node_gen(nodes), batch_size=int(1e4),
    )  # reduce test time

    p0_csv = os.path.join(path, 'Protein-part000.csv')
    m0_csv = os.path.join(path, 'microRNA-part000.csv')
    p1_csv = os.path.join(path, 'Protein-part001.csv')
    m1_csv = os.path.join(path, 'microRNA-part001.csv')

    pr_lines = sum(1 for _ in open(p0_csv))
    mi_lines = sum(1 for _ in open(m0_csv))
    pr_lines1 = sum(1 for _ in open(p1_csv))
    mi_lines1 = sum(1 for _ in open(m1_csv))

    ph_csv = os.path.join(path, 'Protein-header.csv')
    mh_csv = os.path.join(path, 'microRNA-header.csv')

    with open(ph_csv) as f:
        p = f.read()
    with open(mh_csv) as f:
        m = f.read()

    assert (
        passed
        and pr_lines == 1e4
        and mi_lines == 1e4
        and pr_lines1 == 0
        and mi_lines1 == 0
        and p == 'UniProtKB:ID;p1;taxon:int;:LABEL'
        and m == 'MIR:ID;p1;taxon:int;:LABEL'
    )


def test_write_edge_data_from_gen(bw):
    le = 4
    edges = []
    for i in range(le):
        e1 = BioCypherEdge(
            source_id=f'p{i}',
            target_id=f'p{i + 1}',
            relationship_label='INTERACTS_POST_TRANSLATIONAL',
            residue='T253',
            level=4,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e1)
        e2 = BioCypherEdge(
            source_id=f'm{i}',
            target_id=f'p{i + 1}',
            relationship_label='INHIBITS_POST_TRANSCRIPTIONAL',
            site='3-UTR',
            confidence=1,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e2)

    def edge_gen(edges):
        yield from edges

    passed = bw._write_edge_data(edge_gen(edges), batch_size=int(1e4))

    ptl_csv = os.path.join(path, 'INTERACTS_POST_TRANSLATIONAL-part000.csv')
    pts_csv = os.path.join(path, 'INHIBITS_POST_TRANSCRIPTIONAL-part000.csv')

    with open(ptl_csv) as f:
        l = f.read()
    with open(pts_csv) as f:
        c = f.read()

    assert (
        passed
        and l
        == "p0;'T253';4;p1;INTERACTS_POST_TRANSLATIONAL\np1;'T253';4;p2;INTERACTS_POST_TRANSLATIONAL\np2;'T253';4;p3;INTERACTS_POST_TRANSLATIONAL\np3;'T253';4;p4;INTERACTS_POST_TRANSLATIONAL\n"
        and c
        == "m0;'3-UTR';1;p1;INHIBITS_POST_TRANSCRIPTIONAL\nm1;'3-UTR';1;p2;INHIBITS_POST_TRANSCRIPTIONAL\nm2;'3-UTR';1;p3;INHIBITS_POST_TRANSCRIPTIONAL\nm3;'3-UTR';1;p4;INHIBITS_POST_TRANSCRIPTIONAL\n"
    )


def test_write_edge_data_from_large_gen(bw):
    le = int(1e4 + 4)
    edges = []
    for i in range(le):
        e1 = BioCypherEdge(
            source_id=f'p{i}',
            target_id=f'p{i + 1}',
            relationship_label='INTERACTS_POST_TRANSLATIONAL',
            residue='T253',
            level=4,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e1)
        e2 = BioCypherEdge(
            source_id=f'm{i}',
            target_id=f'p{i + 1}',
            relationship_label='INHIBITS_POST_TRANSCRIPTIONAL',
            site='3-UTR',
            confidence=1,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e2)

    def edge_gen(edges):
        yield from edges

    passed = bw._write_edge_data(edge_gen(edges), batch_size=int(1e4))

    apl0_csv = os.path.join(path, 'INTERACTS_POST_TRANSLATIONAL-part000.csv')
    ips0_csv = os.path.join(path, 'INHIBITS_POST_TRANSCRIPTIONAL-part000.csv')
    apl1_csv = os.path.join(path, 'INTERACTS_POST_TRANSLATIONAL-part001.csv')
    ips1_csv = os.path.join(path, 'INHIBITS_POST_TRANSCRIPTIONAL-part001.csv')

    l_lines0 = sum(1 for _ in open(apl0_csv))
    c_lines0 = sum(1 for _ in open(ips0_csv))
    l_lines1 = sum(1 for _ in open(apl1_csv))
    c_lines1 = sum(1 for _ in open(ips1_csv))

    assert (
        passed
        and l_lines0 == 1e4
        and c_lines0 == 1e4
        and l_lines1 == 4
        and c_lines1 == 4
    )


def test_write_edge_data_from_list(bw):
    le = 4
    edges = []
    for i in range(le):
        e1 = BioCypherEdge(
            source_id=f'p{i}',
            target_id=f'p{i + 1}',
            relationship_label='INTERACTS_POST_TRANSLATIONAL',
            residue='T253',
            level=4,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e1)
        e2 = BioCypherEdge(
            source_id=f'm{i}',
            target_id=f'p{i + 1}',
            relationship_label='INHIBITS_POST_TRANSCRIPTIONAL',
            site='3-UTR',
            confidence=1,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e2)

    passed = bw._write_edge_data(edges, batch_size=int(1e4))

    apl_csv = os.path.join(path, 'INTERACTS_POST_TRANSLATIONAL-part000.csv')
    ips_csv = os.path.join(path, 'INHIBITS_POST_TRANSCRIPTIONAL-part000.csv')

    with open(apl_csv) as f:
        l = f.read()
    with open(ips_csv) as f:
        c = f.read()

    assert (
        passed
        and l
        == "p0;'T253';4;p1;INTERACTS_POST_TRANSLATIONAL\np1;'T253';4;p2;INTERACTS_POST_TRANSLATIONAL\np2;'T253';4;p3;INTERACTS_POST_TRANSLATIONAL\np3;'T253';4;p4;INTERACTS_POST_TRANSLATIONAL\n"
        and c
        == "m0;'3-UTR';1;p1;INHIBITS_POST_TRANSCRIPTIONAL\nm1;'3-UTR';1;p2;INHIBITS_POST_TRANSCRIPTIONAL\nm2;'3-UTR';1;p3;INHIBITS_POST_TRANSCRIPTIONAL\nm3;'3-UTR';1;p4;INHIBITS_POST_TRANSCRIPTIONAL\n"
    )


def test_write_edge_data_from_list_no_props(bw):
    le = 4
    edges = []
    for i in range(le):
        e1 = BioCypherEdge(
            source_id=f'p{i}',
            target_id=f'p{i + 1}',
            relationship_label='INTERACTS_POST_TRANSLATIONAL',
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e1)
        e2 = BioCypherEdge(
            source_id=f'm{i}',
            target_id=f'p{i + 1}',
            relationship_label='INHIBITS_POST_TRANSCRIPTIONAL',
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e2)

    passed = bw._write_edge_data(edges, batch_size=int(1e4))

    ptl_csv = os.path.join(path, 'INTERACTS_POST_TRANSLATIONAL-part000.csv')
    pts_csv = os.path.join(path, 'INHIBITS_POST_TRANSCRIPTIONAL-part000.csv')

    with open(ptl_csv) as f:
        l = f.read()
    with open(pts_csv) as f:
        c = f.read()

    assert (
        passed
        and l
        == 'p0;p1;INTERACTS_POST_TRANSLATIONAL\np1;p2;INTERACTS_POST_TRANSLATIONAL\np2;p3;INTERACTS_POST_TRANSLATIONAL\np3;p4;INTERACTS_POST_TRANSLATIONAL\n'
        and c
        == 'm0;p1;INHIBITS_POST_TRANSCRIPTIONAL\nm1;p2;INHIBITS_POST_TRANSCRIPTIONAL\nm2;p3;INHIBITS_POST_TRANSCRIPTIONAL\nm3;p4;INHIBITS_POST_TRANSCRIPTIONAL\n'
    )


def test_write_edge_data_and_headers(bw):
    le = 4
    edges = []
    for i in range(le):
        e1 = BioCypherEdge(
            source_id=f'p{i}',
            target_id=f'p{i + 1}',
            relationship_label='INTERACTS_POST_TRANSLATIONAL',
            residue='T253',
            level=4,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e1)
        e2 = BioCypherEdge(
            source_id=f'm{i}',
            target_id=f'p{i + 1}',
            relationship_label='INHIBITS_POST_TRANSCRIPTIONAL',
            site='3-UTR',
            confidence=1,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e2)

    def edge_gen(edges):
        yield from edges

    passed = bw.write_edges(edge_gen(edges), batch_size=int(1e4))

    ptl_csv = os.path.join(path, 'INTERACTS_POST_TRANSLATIONAL-header.csv')
    pts_csv = os.path.join(path, 'INHIBITS_POST_TRANSCRIPTIONAL-header.csv')

    with open(ptl_csv) as f:
        l = f.read()
    with open(pts_csv) as f:
        c = f.read()

    assert (
        passed
        and l == ':START_ID;residue;level:int;:END_ID;:TYPE'
        and c == ':START_ID;site;confidence:int;:END_ID;:TYPE'
    )


def test_BioCypherRelAsNode_implementation(bw):
    trips = []
    le = 4
    for i in range(le):
        n = BioCypherNode(
            f'i{i+1}',
            'PairwiseMolecularInteraction',
            directed=True,
            effect=-1,
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
        trips.append(BioCypherRelAsNode(n, e1, e2))

    def gen(lis):
        yield from lis

    passed = bw.write_edges(gen(trips))

    iso_csv = os.path.join(path, 'IS_SOURCE_OF-part000.csv')
    ito_csv = os.path.join(path, 'IS_TARGET_OF-part000.csv')
    pmi_csv = os.path.join(path, 'PairwiseMolecularInteraction-part000.csv')

    with open(iso_csv) as f:
        s = f.read()
    with open(ito_csv) as f:
        t = f.read()
    with open(pmi_csv) as f:
        p = f.read()

    assert (
        passed
        # above we've just read these files, they must be files, isn't it?
        and os.path.isfile(iso_csv)
        and os.path.isfile(ito_csv)
        and os.path.isfile(pmi_csv)
        and s
        == 'i1;p1;IS_SOURCE_OF\ni2;p2;IS_SOURCE_OF\ni3;p3;IS_SOURCE_OF\ni4;p4;IS_SOURCE_OF\n'
        and t
        == 'i0;p2;IS_TARGET_OF\ni1;p3;IS_TARGET_OF\ni2;p4;IS_TARGET_OF\ni3;p5;IS_TARGET_OF\n'
        and p
        == "i1;'True';-1;PairwiseMolecularInteraction|PairwiseGeneToGeneInteraction|GeneToGeneAssociation|Association|Entity\ni2;'True';-1;PairwiseMolecularInteraction|PairwiseGeneToGeneInteraction|GeneToGeneAssociation|Association|Entity\ni3;'True';-1;PairwiseMolecularInteraction|PairwiseGeneToGeneInteraction|GeneToGeneAssociation|Association|Entity\ni4;'True';-1;PairwiseMolecularInteraction|PairwiseGeneToGeneInteraction|GeneToGeneAssociation|Association|Entity\n"
    )


def test_write_mixed_edges(bw):
    mixed = []
    le = 4
    for i in range(le):
        n = BioCypherNode(
            f'i{i+1}',
            'PairwiseMolecularInteraction',
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
            relationship_label='INTERACTS_POST_TRANSLATIONAL',
        )
        mixed.append(e3)

    def gen(lis):
        yield from lis

    passed = bw.write_edges(gen(mixed))

    pmi_csv = os.path.join(path, 'PairwiseMolecularInteraction-header.csv')
    iso_csv = os.path.join(path, 'IS_SOURCE_OF-header.csv')
    ito_csv = os.path.join(path, 'IS_TARGET_OF-header.csv')
    ipt_csv = os.path.join(path, 'INTERACTS_POST_TRANSLATIONAL-header.csv')

    assert (
        passed
        and os.path.isfile(pmi_csv)
        and os.path.isfile(iso_csv)
        and os.path.isfile(ito_csv)
        and os.path.isfile(ipt_csv)
    )


def test_create_import_call(bw):
    mixed = []
    le = 4
    for i in range(le):
        n = BioCypherNode(
            f'i{i+1}',
            'PairwiseMolecularInteraction',
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
            relationship_label='INTERACTS_POST_TRANSLATIONAL',
        )
        mixed.append(e3)

    def gen(lis):
        yield from lis

    passed = bw.write_edges(gen(mixed))

    call = bw.get_import_call()

    assert (
        passed
        and call == 'bin/neo4j-admin import --database=neo4j --delimiter=";" '
        '--array-delimiter="|" --quote="\'" '
        f'--nodes="{path}/PairwiseMolecularInteraction-header.csv,{path}/PairwiseMolecularInteraction-part.*" '
        f'--relationships="{path}/IS_SOURCE_OF-header.csv,{path}/IS_SOURCE_OF-part.*" '
        f'--relationships="{path}/IS_TARGET_OF-header.csv,{path}/IS_TARGET_OF-part.*" '
        f'--relationships="{path}/INTERACTS_POST_TRANSLATIONAL-header.csv,{path}/INTERACTS_POST_TRANSLATIONAL-part.*" '
    )


# TODO extend tests to "raw" input (not biocypher nodes)
# where? translate? is not "unit" test

# TODO possible overwrite? eg IS_SOURCE_OF or IS_TARGET_OF gets called
# more than one time? what if write function called multiple times with
# different properties on the same node or edge types?
