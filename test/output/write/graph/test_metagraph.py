import glob
import os

import pytest

from rdflib import (
    OWL,
    RDFS,
    URIRef,
)

from rdflib import CSVW, RDF, Graph, Literal


@pytest.mark.parametrize("length", [4], scope="function")
def test_metagraph_write_data(bw_metagraph, length, _get_nodes, _get_edges):
    # See test/fixtures/metagraph.py

    # logging.basicConfig()
    # logger = logging.getLogger("biocypher")

    nodes = _get_nodes
    edges = _get_edges

    # fix_ontology(bw_owl)

    nodes = bw_metagraph.write_nodes(nodes)
    edges = bw_metagraph.write_edges(edges)

    # check if the writing of the nodes went okay.
    assert all([nodes, edges])

    bw_metagraph._construct_import_call()
