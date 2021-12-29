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
            "preferred_id": "tbd",
            "label_in_input": "POST_TRANSLATIONAL",
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

    assert p == "UniProtKB:ID;p1;p2;:Protein" and m == "MIR:ID;p1;p2;:microRNA"
