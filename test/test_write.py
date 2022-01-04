import pytest
import os
from biocypher.translate import BiolinkAdapter
from biocypher.write import BatchWriter
from biocypher.create import BioCypherNode, BioCypherEdge

import random
import string
import itertools


def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(length))


@pytest.fixture
def bw():
    schema = {
        "Protein": {
            "represented_as": "node",
            "preferred_id": "UniProtKB",
            "label_in_input": "protein",
        },
        "microRNA": {
            "represented_as": "node",
            "preferred_id": "MIR",
            "label_in_input": "miRNA",
        },
        "PostTranslationalInteraction": {
            "represented_as": "edge",
            "preferred_id": "PLID",
            "label_in_input": "POST_TRANSLATIONAL",
        },
        "PostTranscriptionalInteraction": {
            "represented_as": "edge",
            "preferred_id": "PCID",
            "label_in_input": "POST_TRANSCRIPTIONAL",
        },
    }
    bl_adapter = BiolinkAdapter(leaves=schema)
    bw = BatchWriter(schema, bl_adapter, dirname="Test")

    yield bw

    # teardown
    ROOT = os.path.join(
        *os.path.split(os.path.abspath(os.path.dirname(__file__)))
    )
    path = ROOT + "/../out/Test/"
    for f in os.listdir(path):
        os.remove(os.path.join(path, f))
    os.rmdir(path)


def test_writer_and_output_dir(bw):
    ROOT = os.path.join(
        *os.path.split(os.path.abspath(os.path.dirname(__file__)))
    )
    path = ROOT + "/../out/Test/"
    assert (
        os.path.isdir(path) and isinstance(bw, BatchWriter) and bw.delim == ";"
    )


def test_write_node_headers(bw):
    bw.write_node_headers()
    ROOT = os.path.join(
        *os.path.split(os.path.abspath(os.path.dirname(__file__)))
    )
    path = ROOT + "/../out/Test/"
    with open(path + "Protein-header.csv", "r") as f:
        p = f.read()
    with open(path + "microRNA-header.csv", "r") as f:
        m = f.read()

    assert p == (
        "UniProtKB:ID;p1;p2;:Protein|:Polypeptide|:BiologicalEntity"
        "|:NamedThing|:Entity|:GeneProductMixin|:GeneOrGeneProduct"
        "|:MacromolecularMachineMixin|:ThingWithTaxon"
        "|:ChemicalEntityOrGeneOrGeneProduct"
        "|:ChemicalEntityOrProteinOrPolypeptide"
    ) and m == (
        "MIR:ID;p1;p2;:MicroRNA|:NoncodingRNAProduct|:RNAProduct"
        "|:Transcript|:NucleicAcidEntity|:MolecularEntity"
        "|:ChemicalEntity|:NamedThing|:Entity|:GeneProductMixin"
        "|:GeneOrGeneProduct|:MacromolecularMachineMixin"
        "|:GenomicEntity|:ThingWithTaxon|:PhysicalEssence"
        "|:PhysicalEssenceOrOccurrent|:OntologyClass"
        "|:ChemicalOrDrugOrTreatment|:ChemicalEntityOrGeneOrGeneProduct"
        "|:ChemicalEntityOrProteinOrPolypeptide"
    )


def test_write_edge_headers(bw):
    bw.write_edge_headers()
    ROOT = os.path.join(
        *os.path.split(os.path.abspath(os.path.dirname(__file__)))
    )
    path = ROOT + "/../out/Test/"
    with open(path + "PostTranslationalInteraction-header.csv", "r") as f:
        l = f.read()
    with open(path + "PostTranscriptionalInteraction-header.csv", "r") as f:
        c = f.read()

    assert (
        l == ":START_ID;PLID;p1;p2;:END_ID;PostTranslationalInteraction"
        and c == ":START_ID;PCID;p1;p2;:END_ID;PostTranscriptionalInteraction"
    )


def test_write_node_body_from_list(bw):
    nodes = []
    # four proteins, four miRNAs
    for i in range(4):
        bnp = BioCypherNode(
            f"p{i+1}",
            "Protein",
            optional_labels=["SubLabel1", "SubLabel2"],
            p1="Property1",
            p2="Property2",
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f"m{i+1}",
            "microRNA",
            optional_labels=["SubLabel1", "SubLabel2"],
            p1="Property1",
            p2="Property2",
        )
        nodes.append(bnm)

    bw.write_node_body(nodes)

    ROOT = os.path.join(
        *os.path.split(os.path.abspath(os.path.dirname(__file__)))
    )
    path = ROOT + "/../out/Test/"
    with open(path + "Protein-part000.csv", "r") as f:
        pr = f.read()

    with open(path + "microRNA-part000.csv", "r") as f:
        mi = f.read()

    assert (
        pr == "p1;Property1;Property2;Protein|SubLabel1|SubLabel2\n"
        "p2;Property1;Property2;Protein|SubLabel1|SubLabel2\n"
        "p3;Property1;Property2;Protein|SubLabel1|SubLabel2\n"
        "p4;Property1;Property2;Protein|SubLabel1|SubLabel2\n"
        and mi == "m1;Property1;Property2;microRNA|SubLabel1|SubLabel2\n"
        "m2;Property1;Property2;microRNA|SubLabel1|SubLabel2\n"
        "m3;Property1;Property2;microRNA|SubLabel1|SubLabel2\n"
        "m4;Property1;Property2;microRNA|SubLabel1|SubLabel2\n"
    )


def test_write_node_body_from_large_list(bw):
    nodes = []
    # 5e5 proteins and miRNAs
    le = int(5e5)
    print("Creating list")
    for i in range(le):
        bnp = BioCypherNode(
            f"p{i+1}",
            "Protein",
            optional_labels=["SubLabel1", "SubLabel2"],
            p1=get_random_string(4),
            p2=get_random_string(8),
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f"m{i+1}",
            "microRNA",
            optional_labels=["SubLabel1", "SubLabel2"],
            p1=get_random_string(4),
            p2=get_random_string(8),
        )
        nodes.append(bnm)

    bw.write_node_body(nodes)

    ROOT = os.path.join(
        *os.path.split(os.path.abspath(os.path.dirname(__file__)))
    )
    path = ROOT + "/../out/Test/"
    pr_lines = sum(1 for _ in open(path + "Protein-part000.csv"))

    mi_lines = sum(1 for _ in open(path + "microRNA-part000.csv"))

    assert pr_lines == le and mi_lines == le


def test_write_node_body_from_gen(bw):
    nodes = []
    le = 4
    print("Creating list")
    for i in range(le):
        bnp = BioCypherNode(
            f"p{i+1}",
            "Protein",
            optional_labels=["SubLabel1", "SubLabel2"],
            p1="Property1",
            p2="Property2",
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f"m{i+1}",
            "microRNA",
            optional_labels=["SubLabel1", "SubLabel2"],
            p1="Property1",
            p2="Property2",
        )
        nodes.append(bnm)

    def node_gen(nodes):
        for n in nodes:
            yield n

    bw.write_node_body(node_gen(nodes))

    ROOT = os.path.join(
        *os.path.split(os.path.abspath(os.path.dirname(__file__)))
    )
    path = ROOT + "/../out/Test/"
    with open(path + "Protein-part000.csv", "r") as f:
        pr = f.read()

    with open(path + "microRNA-part000.csv", "r") as f:
        mi = f.read()

    assert (
        pr == "p1;Property1;Property2;Protein|SubLabel1|SubLabel2\n"
        "p2;Property1;Property2;Protein|SubLabel1|SubLabel2\n"
        "p3;Property1;Property2;Protein|SubLabel1|SubLabel2\n"
        "p4;Property1;Property2;Protein|SubLabel1|SubLabel2\n"
        and mi == "m1;Property1;Property2;microRNA|SubLabel1|SubLabel2\n"
        "m2;Property1;Property2;microRNA|SubLabel1|SubLabel2\n"
        "m3;Property1;Property2;microRNA|SubLabel1|SubLabel2\n"
        "m4;Property1;Property2;microRNA|SubLabel1|SubLabel2\n"
    )


def test_write_node_body_from_large_gen(bw):
    nodes = []
    le = int(1e6 + 4)
    print("Creating list")
    for i in range(le):
        bnp = BioCypherNode(
            f"p{i+1}",
            "Protein",
            optional_labels=["SubLabel1", "SubLabel2"],
            p1=get_random_string(4),
            p2=get_random_string(8),
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f"m{i+1}",
            "microRNA",
            optional_labels=["SubLabel1", "SubLabel2"],
            p1=get_random_string(4),
            p2=get_random_string(8),
        )
        nodes.append(bnm)

    def node_gen(nodes):
        for n in nodes:
            yield n

    bw.write_node_body(node_gen(nodes))

    ROOT = os.path.join(
        *os.path.split(os.path.abspath(os.path.dirname(__file__)))
    )
    path = ROOT + "/../out/Test/"

    pr_lines = sum(1 for _ in open(path + "Protein-part000.csv"))
    mi_lines = sum(1 for _ in open(path + "microRNA-part000.csv"))
    pr_lines1 = sum(1 for _ in open(path + "Protein-part001.csv"))
    mi_lines1 = sum(1 for _ in open(path + "microRNA-part001.csv"))

    assert (
        pr_lines == 1e6
        and mi_lines == 1e6
        and pr_lines1 == 4
        and mi_lines1 == 4
    )
