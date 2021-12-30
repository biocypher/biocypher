import pytest
import os
from biocypher.translate import BiolinkAdapter
from biocypher.write import BatchWriter


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
        "|:MacromolecularMachineMixin|:ThingWithTaxon|:ThingWithTaxon"
        "|:ChemicalEntityOrGeneOrGeneProduct"
        "|:ChemicalEntityOrProteinOrPolypeptide"
    ) and m == (
        "MIR:ID;p1;p2;:MicroRNA|:NoncodingRNAProduct|:RNAProduct"
        "|:Transcript|:NucleicAcidEntity|:MolecularEntity"
        "|:ChemicalEntity|:NamedThing|:Entity|:GeneProductMixin"
        "|:GeneOrGeneProduct|:MacromolecularMachineMixin"
        "|:GenomicEntity|:ThingWithTaxon|:PhysicalEssence"
        "|:PhysicalEssenceOrOccurrent|:OntologyClass"
        "|:PhysicalEssence|:PhysicalEssenceOrOccurrent"
        "|:ChemicalOrDrugOrTreatment"
        "|:ChemicalEntityOrGeneOrGeneProduct"
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
