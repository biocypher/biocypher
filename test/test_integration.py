import os

import pytest
import networkx as nx

from biocypher._ontology import Ontology


@pytest.mark.parametrize("l", [4], scope="function")
def test_write_node_data_from_gen(core, _get_nodes):
    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    passed = core.write_nodes(node_gen(nodes))
    assert passed

    path = core._output_directory

    p_csv = os.path.join(path, "Protein-part000.csv")
    m_csv = os.path.join(path, "MicroRNA-part000.csv")

    with open(p_csv) as f:
        pr = f.read()

    with open(m_csv) as f:
        mi = f.read()

    assert passed
    assert "p1;'StringProperty1';4.0;9606;'gene1|gene2';'p1';'uniprot'" in pr
    assert "BiologicalEntity" in pr
    assert "m1;'StringProperty1';9606;'m1';'mirbase'" in mi
    assert "ChemicalEntity" in mi


def test_show_ontology_structure_kwargs(core):
    treevis = core.show_ontology_structure(full=True)

    assert treevis is not None


def test_ontology_without_schema_config(core_no_schema):
    assert core_no_schema

    core_no_schema._head_ontology = {
        "url": "http://semanticweb.cs.vu.nl/2009/11/sem/",
        "root_node": "Core",
        "format": "rdf",
    }
    core_no_schema._ontology_mapping = None

    core_no_schema._get_ontology()

    assert isinstance(core_no_schema._ontology, Ontology)
    assert isinstance(core_no_schema._ontology._nx_graph, nx.DiGraph)


@pytest.mark.parametrize("l", [4], scope="function")
def test_write_schema_info_as_node(core, _get_nodes):
    core.add(_get_nodes)

    schema = core.write_schema_info(as_node=True)

    path = os.path.join(core._output_directory, "schema_info.yaml")
    assert os.path.exists(path)

    with open(path, "r") as f:
        schema_loaded = yaml.safe_load(f)

    assert schema_loaded == schema
