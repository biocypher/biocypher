import pytest
import os
from biocypher.write import BatchWriter


@pytest.fixture
def bw():
    bw = BatchWriter(dirname="Test")

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


def test_write_headers(bw):
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

    bw.write_node_headers(schema)
    ROOT = os.path.join(
        *os.path.split(os.path.abspath(os.path.dirname(__file__)))
    )
    path = ROOT + "/../out/Test/"
    with open(path + "Protein-header.csv", "r") as f:
        p = f.read()
    with open(path + "microRNA-header.csv", "r") as f:
        m = f.read()

    bw.write_edge_headers(schema)
    ROOT = os.path.join(
        *os.path.split(os.path.abspath(os.path.dirname(__file__)))
    )
    path = ROOT + "/../out/Test/"
    with open(path + "PostTranslationalInteraction-header.csv", "r") as f:
        l = f.read()
    with open(path + "PostTranscriptionalInteraction-header.csv", "r") as f:
        c = f.read()

    assert (
        p == "UniProtKB:ID;p1;p2;:Protein"
        and m == "MIR:ID;p1;p2;:microRNA"
        and l == "PLID:ID;p1;p2;:PostTranslationalInteraction"
        and c == "PCID:ID;p1;p2;:PostTranscriptionalInteraction"
    )
