import os
import glob

from rdflib import RDF, Graph, Namespace
import pytest


@pytest.mark.parametrize("length", [4], scope="function")
def test_rdf_write_data(bw_rdf, length, _get_nodes, _get_edges):
    nodes = _get_nodes
    edges = _get_edges

    nodes = bw_rdf.write_nodes(nodes)
    edges = bw_rdf.write_edges(edges)

    # check if the writing of the nodes went okay.
    assert all([nodes, edges])

    tmp_path = bw_rdf.outdir

    rdf_files_path = os.path.join(tmp_path, "*.xml")
    rdf_files = glob.glob(rdf_files_path)

    graph = Graph()
    for file in rdf_files:
        with open(file) as f:
            temp_graph = Graph().parse(data=f.read(), format="xml")
            graph += temp_graph
            for node in temp_graph:
                print(node)

    biocypher_namespace = Namespace("https://biocypher.org/biocypher#")

    # All nodes should have an identifier
    assert len(set(graph.subjects(biocypher_namespace["id"]))) == 8

    # everything should have a type assigned
    assert len(set(graph.subjects(RDF.type))) == 20

    # check if all the nodes have assigned their properties
    assert len(set(graph.subject_objects())) == 92
