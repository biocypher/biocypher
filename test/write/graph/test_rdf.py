import os
import pytest
from rdflib import Graph
from biocypher.write import _batch_writer
from biocypher.write.graph._rdf import _RDFwriter
from biocypher._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode
import glob

def nodes_and_edges():
    nodes_type_1 = []
    nodes_type_2 = []
    edges = []
    number_of_items = 4
    for i in range(number_of_items):
        node1 = BioCypherNode(
            f"EFO:{i+1}",
            node_label="disease",
            properties= {"name": f"disease{i+1}"}
        )
        node2 = BioCypherNode(
            f"ensembl:ENS{i+1}",
            node_label="gene",
        )
        edge_1 = BioCypherEdge(
            source_id=f"EFO:{i+1}",
            target_id=f"ensembl:ENS{i+1}",
            relationship_label="gene_disease_relationship",
            properties = {"score": "0.3"}
        )
        nodes_type_1.append(node1)
        nodes_type_2.append(node2)
        edges.append(edge_1)

    return [[nodes_type_1, nodes_type_2], edges]

@pytest.fixture
def _get_nodes():
    # return a list of nodes
    return nodes_and_edges()[0]

@pytest.fixture
def _get_edges():
    # return a list of edges
    return nodes_and_edges()[1]


@pytest.mark.parametrize("length", [4], scope="function")
def test_rdf_write_data(bw_rdf, length, _get_nodes, _get_edges):
    # writer = _get_writer
    # writer.rdf_format = "xml"
    nodes = _get_nodes
    edges = _get_edges

    node_type_1 = bw_rdf.write_nodes(nodes[0])
    node_type_2 = bw_rdf.write_nodes(nodes[1])
    edge_1 = bw_rdf.write_edges(edges)

    # check if the writing of the nodes went okay.
    assert all([node_type_1, node_type_2, edge_1])

    tmp_path = bw_rdf.outdir

    rdf_files_path = os.path.join(tmp_path, "*.xml")
    rdf_files = glob.glob(rdf_files_path)

    g = Graph()
    for file in rdf_files:
        with open(file) as f:
            g_temp = Graph().parse(data=f.read(), format="xml")
            g += g_temp

    # check if the number of nodes and relations are correct
    assert len(set(g.subjects())) == 15  # generated 4 nodes per type (8 in total) and 4 'edges'. together with the class definition (+3) makes 15 in total
    assert len(set(g.subject_objects())) == 47 # all the triples; between nodes, but also the converted properties of nodes and the 'edges'.