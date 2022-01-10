import pytest
import os
from biocypher.translate import BiolinkAdapter
from biocypher.write import BatchWriter
from biocypher.create import BioCypherNode, BioCypherEdge

import random
import string


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
        *os.path.split(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        )
    )
    path = ROOT + "/out/Test/"
    for f in os.listdir(path):
        os.remove(os.path.join(path, f))
    os.rmdir(path)


def test_writer_and_output_dir(bw):
    ROOT = os.path.join(
        *os.path.split(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        )
    )
    path = ROOT + "/out/Test/"
    assert (
        os.path.isdir(path) and isinstance(bw, BatchWriter) and bw.delim == ";"
    )


def test_write_node_data_and_headers(bw):
    nodes = []
    # four proteins, four miRNAs
    for i in range(4):
        bnp = BioCypherNode(
            f"p{i+1}",
            "Protein",
            string_property="StringProperty1",
            taxon=9606,
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f"m{i+1}",
            "microRNA",
            string_property="StringProperty1",
            taxon=9606,
        )
        nodes.append(bnm)

    passed = bw.write_nodes(nodes)

    ROOT = os.path.join(
        *os.path.split(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        )
    )
    path = ROOT + "/out/Test/"
    with open(path + "Protein-header.csv", "r") as f:
        p = f.read()
    with open(path + "microRNA-header.csv", "r") as f:
        m = f.read()

    assert (
        passed
        and p == ("UniProtKB:ID;string_property;taxon:int;:LABEL")
        and m == ("MIR:ID;string_property;taxon:int;:LABEL")
    )


def test_write_node_data_from_list(bw):
    nodes = []
    # four proteins, four miRNAs
    for i in range(4):
        bnp = BioCypherNode(
            f"p{i+1}",
            "Protein",
            string_property="StringProperty1",
            taxon=9606,
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f"m{i+1}",
            "microRNA",
            string_property="StringProperty1",
            taxon=9606,
        )
        nodes.append(bnm)

    passed = bw._write_node_data(nodes, batch_size=1e6)

    ROOT = os.path.join(
        *os.path.split(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        )
    )
    path = ROOT + "/out/Test/"
    with open(path + "Protein-part000.csv", "r") as f:
        pr = f.read()

    with open(path + "microRNA-part000.csv", "r") as f:
        mi = f.read()

    assert (
        passed
        and pr
        == "p1;'StringProperty1';9606;Protein|Polypeptide|BiologicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|ThingWithTaxon|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\np2;'StringProperty1';9606;Protein|Polypeptide|BiologicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|ThingWithTaxon|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\np3;'StringProperty1';9606;Protein|Polypeptide|BiologicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|ThingWithTaxon|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\np4;'StringProperty1';9606;Protein|Polypeptide|BiologicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|ThingWithTaxon|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\n"
        and mi
        == "m1;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|Transcript|NucleicAcidEntity|MolecularEntity|ChemicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|GenomicEntity|ThingWithTaxon|PhysicalEssence|PhysicalEssenceOrOccurrent|OntologyClass|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\nm2;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|Transcript|NucleicAcidEntity|MolecularEntity|ChemicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|GenomicEntity|ThingWithTaxon|PhysicalEssence|PhysicalEssenceOrOccurrent|OntologyClass|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\nm3;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|Transcript|NucleicAcidEntity|MolecularEntity|ChemicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|GenomicEntity|ThingWithTaxon|PhysicalEssence|PhysicalEssenceOrOccurrent|OntologyClass|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\nm4;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|Transcript|NucleicAcidEntity|MolecularEntity|ChemicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|GenomicEntity|ThingWithTaxon|PhysicalEssence|PhysicalEssenceOrOccurrent|OntologyClass|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\n"
    )


def test_write_node_data_from_gen(bw):
    nodes = []
    le = 4
    for i in range(le):
        bnp = BioCypherNode(
            f"p{i+1}",
            "Protein",
            string_property="StringProperty1",
            taxon=9606,
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f"m{i+1}",
            "microRNA",
            string_property="StringProperty1",
            taxon=9606,
        )
        nodes.append(bnm)

    def node_gen(nodes):
        for n in nodes:
            yield n

    passed = bw._write_node_data(node_gen(nodes), batch_size=1e6)

    ROOT = os.path.join(
        *os.path.split(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        )
    )
    path = ROOT + "/out/Test/"
    with open(path + "Protein-part000.csv", "r") as f:
        pr = f.read()

    with open(path + "microRNA-part000.csv", "r") as f:
        mi = f.read()

    assert (
        passed
        and pr
        == "p1;'StringProperty1';9606;Protein|Polypeptide|BiologicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|ThingWithTaxon|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\np2;'StringProperty1';9606;Protein|Polypeptide|BiologicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|ThingWithTaxon|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\np3;'StringProperty1';9606;Protein|Polypeptide|BiologicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|ThingWithTaxon|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\np4;'StringProperty1';9606;Protein|Polypeptide|BiologicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|ThingWithTaxon|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\n"
        and mi
        == "m1;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|Transcript|NucleicAcidEntity|MolecularEntity|ChemicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|GenomicEntity|ThingWithTaxon|PhysicalEssence|PhysicalEssenceOrOccurrent|OntologyClass|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\nm2;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|Transcript|NucleicAcidEntity|MolecularEntity|ChemicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|GenomicEntity|ThingWithTaxon|PhysicalEssence|PhysicalEssenceOrOccurrent|OntologyClass|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\nm3;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|Transcript|NucleicAcidEntity|MolecularEntity|ChemicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|GenomicEntity|ThingWithTaxon|PhysicalEssence|PhysicalEssenceOrOccurrent|OntologyClass|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\nm4;'StringProperty1';9606;MicroRNA|NoncodingRNAProduct|RNAProduct|Transcript|NucleicAcidEntity|MolecularEntity|ChemicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|GenomicEntity|ThingWithTaxon|PhysicalEssence|PhysicalEssenceOrOccurrent|OntologyClass|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\n"
    )


def test_write_node_data_from_gen_no_props(bw):
    nodes = []
    le = 4
    for i in range(le):
        bnp = BioCypherNode(
            f"p{i+1}",
            "Protein",
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f"m{i+1}",
            "microRNA",
        )
        nodes.append(bnm)

    def node_gen(nodes):
        for n in nodes:
            yield n

    passed = bw._write_node_data(node_gen(nodes), batch_size=1e6)

    ROOT = os.path.join(
        *os.path.split(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        )
    )
    path = ROOT + "/out/Test/"
    with open(path + "Protein-part000.csv", "r") as f:
        pr = f.read()

    with open(path + "microRNA-part000.csv", "r") as f:
        mi = f.read()

    assert (
        passed
        and pr
        == "p1;Protein|Polypeptide|BiologicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|ThingWithTaxon|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\np2;Protein|Polypeptide|BiologicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|ThingWithTaxon|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\np3;Protein|Polypeptide|BiologicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|ThingWithTaxon|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\np4;Protein|Polypeptide|BiologicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|ThingWithTaxon|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\n"
        and mi
        == "m1;MicroRNA|NoncodingRNAProduct|RNAProduct|Transcript|NucleicAcidEntity|MolecularEntity|ChemicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|GenomicEntity|ThingWithTaxon|PhysicalEssence|PhysicalEssenceOrOccurrent|OntologyClass|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\nm2;MicroRNA|NoncodingRNAProduct|RNAProduct|Transcript|NucleicAcidEntity|MolecularEntity|ChemicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|GenomicEntity|ThingWithTaxon|PhysicalEssence|PhysicalEssenceOrOccurrent|OntologyClass|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\nm3;MicroRNA|NoncodingRNAProduct|RNAProduct|Transcript|NucleicAcidEntity|MolecularEntity|ChemicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|GenomicEntity|ThingWithTaxon|PhysicalEssence|PhysicalEssenceOrOccurrent|OntologyClass|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\nm4;MicroRNA|NoncodingRNAProduct|RNAProduct|Transcript|NucleicAcidEntity|MolecularEntity|ChemicalEntity|NamedThing|Entity|GeneProductMixin|GeneOrGeneProduct|MacromolecularMachineMixin|GenomicEntity|ThingWithTaxon|PhysicalEssence|PhysicalEssenceOrOccurrent|OntologyClass|ChemicalOrDrugOrTreatment|ChemicalEntityOrGeneOrGeneProduct|ChemicalEntityOrProteinOrPolypeptide\n"
    )


def test_write_node_data_from_large_gen(bw):
    nodes = []
    le = int(1e4 + 4)
    for i in range(le):
        bnp = BioCypherNode(
            f"p{i+1}",
            "Protein",
            p1=get_random_string(4),
            p2=get_random_string(8),
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f"m{i+1}",
            "microRNA",
            p1=get_random_string(4),
            p2=get_random_string(8),
        )
        nodes.append(bnm)

    def node_gen(nodes):
        for n in nodes:
            yield n

    passed = bw._write_node_data(
        node_gen(nodes), batch_size=int(1e4)
    )  # reduce test time

    ROOT = os.path.join(
        *os.path.split(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        )
    )
    path = ROOT + "/out/Test/"

    pr_lines = sum(1 for _ in open(path + "Protein-part000.csv"))
    mi_lines = sum(1 for _ in open(path + "microRNA-part000.csv"))
    pr_lines1 = sum(1 for _ in open(path + "Protein-part001.csv"))
    mi_lines1 = sum(1 for _ in open(path + "microRNA-part001.csv"))

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
            f"p{i+1}",
            "Protein",
            p1=get_random_string(4),
            p2=get_random_string(8),
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f"m{i+1}",
            "microRNA",
            p1=get_random_string(4),
            p2=get_random_string(8),
        )
        nodes.append(bnm)

    bn1 = BioCypherNode(
        "p0",
        "Protein",
        p1=get_random_string(4),
        p2=get_random_string(8),
        p3=get_random_string(16),
        p4=get_random_string(16),
    )
    nodes.append(bn1)

    def node_gen(nodes):
        for n in nodes:
            yield n

    passed = bw._write_node_data(
        node_gen(nodes), batch_size=int(1e4)
    )  # reduce test time

    assert not passed

    del nodes[-1]
    bn2 = BioCypherNode(
        "p0",
        "Protein",
        p1=get_random_string(4),
    )
    nodes.append(bn2)

    passed = bw._write_node_data(
        node_gen(nodes), batch_size=int(1e4)
    )  # reduce test time

    assert not passed


def test_accidental_exact_batch_size(bw):
    nodes = []
    le = int(1e4)
    for i in range(le):
        bnp = BioCypherNode(
            f"p{i+1}",
            "Protein",
            p1=get_random_string(4),
            taxon=9606,
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            f"m{i+1}",
            "microRNA",
            p1=get_random_string(4),
            taxon=9606,
        )
        nodes.append(bnm)

    def node_gen(nodes):
        for n in nodes:
            yield n

    passed = bw.write_nodes(
        node_gen(nodes), batch_size=int(1e4)
    )  # reduce test time

    ROOT = os.path.join(
        *os.path.split(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        )
    )
    path = ROOT + "/out/Test/"

    pr_lines = sum(1 for _ in open(path + "Protein-part000.csv"))
    mi_lines = sum(1 for _ in open(path + "microRNA-part000.csv"))
    pr_lines1 = sum(1 for _ in open(path + "Protein-part001.csv"))
    mi_lines1 = sum(1 for _ in open(path + "microRNA-part001.csv"))

    with open(path + "Protein-header.csv", "r") as f:
        p = f.read()
    with open(path + "microRNA-header.csv", "r") as f:
        m = f.read()

    assert (
        passed
        and pr_lines == 1e4
        and mi_lines == 1e4
        and pr_lines1 == 0
        and mi_lines1 == 0
        and p == "UniProtKB:ID;p1;taxon:int;:LABEL"
        and m == "MIR:ID;p1;taxon:int;:LABEL"
    )


def test_write_edge_data_from_gen(bw):
    le = 4
    edges = []
    for i in range(le):
        e1 = BioCypherEdge(
            source_id=f"p{i}",
            target_id=f"p{i + 1}",
            relationship_label="INTERACTS_POST_TRANSLATIONAL",
            residue="T253",
            level=4,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e1)
        e2 = BioCypherEdge(
            source_id=f"m{i}",
            target_id=f"p{i + 1}",
            relationship_label="INHIBITS_POST_TRANSCRIPTIONAL",
            site="3-UTR",
            confidence=1,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e2)

    def edge_gen(edges):
        yield from edges

    passed = bw._write_edge_data(edge_gen(edges), batch_size=int(1e4))

    ROOT = os.path.join(
        *os.path.split(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        )
    )
    path = ROOT + "/out/Test/"

    with open(path + "INTERACTS_POST_TRANSLATIONAL-part000.csv", "r") as f:
        l = f.read()
    with open(path + "INHIBITS_POST_TRANSCRIPTIONAL-part000.csv", "r") as f:
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
            source_id=f"p{i}",
            target_id=f"p{i + 1}",
            relationship_label="INTERACTS_POST_TRANSLATIONAL",
            residue="T253",
            level=4,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e1)
        e2 = BioCypherEdge(
            source_id=f"m{i}",
            target_id=f"p{i + 1}",
            relationship_label="INHIBITS_POST_TRANSCRIPTIONAL",
            site="3-UTR",
            confidence=1,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e2)

    def edge_gen(edges):
        yield from edges

    passed = bw._write_edge_data(edge_gen(edges), batch_size=int(1e4))

    ROOT = os.path.join(
        *os.path.split(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        )
    )
    path = ROOT + "/out/Test/"

    l_lines = sum(
        1 for _ in open(path + "INTERACTS_POST_TRANSLATIONAL-part000.csv")
    )
    c_lines = sum(
        1 for _ in open(path + "INHIBITS_POST_TRANSCRIPTIONAL-part000.csv")
    )
    l_lines1 = sum(
        1 for _ in open(path + "INTERACTS_POST_TRANSLATIONAL-part001.csv")
    )
    c_lines1 = sum(
        1 for _ in open(path + "INHIBITS_POST_TRANSCRIPTIONAL-part001.csv")
    )

    assert (
        passed
        and l_lines == 1e4
        and c_lines == 1e4
        and l_lines1 == 4
        and c_lines1 == 4
    )


def test_write_edge_data_from_list(bw):
    le = 4
    edges = []
    for i in range(le):
        e1 = BioCypherEdge(
            source_id=f"p{i}",
            target_id=f"p{i + 1}",
            relationship_label="INTERACTS_POST_TRANSLATIONAL",
            residue="T253",
            level=4,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e1)
        e2 = BioCypherEdge(
            source_id=f"m{i}",
            target_id=f"p{i + 1}",
            relationship_label="INHIBITS_POST_TRANSCRIPTIONAL",
            site="3-UTR",
            confidence=1,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e2)

    passed = bw._write_edge_data(edges, batch_size=int(1e4))

    ROOT = os.path.join(
        *os.path.split(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        )
    )
    path = ROOT + "/out/Test/"

    with open(path + "INTERACTS_POST_TRANSLATIONAL-part000.csv", "r") as f:
        l = f.read()
    with open(path + "INHIBITS_POST_TRANSCRIPTIONAL-part000.csv", "r") as f:
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
            source_id=f"p{i}",
            target_id=f"p{i + 1}",
            relationship_label="INTERACTS_POST_TRANSLATIONAL",
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e1)
        e2 = BioCypherEdge(
            source_id=f"m{i}",
            target_id=f"p{i + 1}",
            relationship_label="INHIBITS_POST_TRANSCRIPTIONAL",
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e2)

    passed = bw._write_edge_data(edges, batch_size=int(1e4))

    ROOT = os.path.join(
        *os.path.split(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        )
    )
    path = ROOT + "/out/Test/"

    with open(path + "INTERACTS_POST_TRANSLATIONAL-part000.csv", "r") as f:
        l = f.read()
    with open(path + "INHIBITS_POST_TRANSCRIPTIONAL-part000.csv", "r") as f:
        c = f.read()

    assert (
        passed
        and l
        == "p0;p1;INTERACTS_POST_TRANSLATIONAL\np1;p2;INTERACTS_POST_TRANSLATIONAL\np2;p3;INTERACTS_POST_TRANSLATIONAL\np3;p4;INTERACTS_POST_TRANSLATIONAL\n"
        and c
        == "m0;p1;INHIBITS_POST_TRANSCRIPTIONAL\nm1;p2;INHIBITS_POST_TRANSCRIPTIONAL\nm2;p3;INHIBITS_POST_TRANSCRIPTIONAL\nm3;p4;INHIBITS_POST_TRANSCRIPTIONAL\n"
    )


def test_write_edge_data_and_headers(bw):
    le = 4
    edges = []
    for i in range(le):
        e1 = BioCypherEdge(
            source_id=f"p{i}",
            target_id=f"p{i + 1}",
            relationship_label="INTERACTS_POST_TRANSLATIONAL",
            residue="T253",
            level=4,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e1)
        e2 = BioCypherEdge(
            source_id=f"m{i}",
            target_id=f"p{i + 1}",
            relationship_label="INHIBITS_POST_TRANSCRIPTIONAL",
            site="3-UTR",
            confidence=1,
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e2)

    def edge_gen(edges):
        yield from edges

    passed = bw._write_edge_data(edge_gen(edges), batch_size=int(1e4))

    bw._write_edge_headers()
    ROOT = os.path.join(
        *os.path.split(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        )
    )
    path = ROOT + "/out/Test/"
    with open(path + "INTERACTS_POST_TRANSLATIONAL-header.csv", "r") as f:
        l = f.read()
    with open(path + "INHIBITS_POST_TRANSCRIPTIONAL-header.csv", "r") as f:
        c = f.read()

    assert (
        passed
        and l == ":START_ID;residue;level:int;:END_ID;:TYPE"
        and c == ":START_ID;site;confidence:int;:END_ID;:TYPE"
    )


# TODO extend tests to "raw" input (not biocypher nodes)
# where? translate? is not "unit" test
