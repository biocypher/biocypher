import os

import pytest
import networkx as nx

from biocypher._ontology import Ontology, OntologyAdapter, warn_if_slow


def test_biolink_adapter(biolink_adapter):
    assert biolink_adapter.get_root_label() == "entity"
    assert biolink_adapter.get_nx_graph().number_of_nodes() > 100

    assert "biological entity" in biolink_adapter.get_ancestors("gene")
    assert "macromolecular machine mixin" in biolink_adapter.get_ancestors(
        "macromolecular complex"
    )


def test_so_adapter(so_adapter):
    assert so_adapter.get_root_label() == "sequence_variant"

    # here without underscores
    assert "sequence variant" in so_adapter.get_ancestors("lethal variant")


def test_go_adapter(go_adapter):
    assert go_adapter.get_root_label() == "molecular_function"

    assert "molecular function" in go_adapter.get_ancestors(
        "rna helicase activity"
    )


def test_mondo_adapter(mondo_adapter):
    assert mondo_adapter.get_root_label() == "disease"

    assert "human disease" in mondo_adapter.get_ancestors("cystic fibrosis")


def test_ontology_adapter_root_node_missing():
    with pytest.raises(ValueError):
        OntologyAdapter("test/so.owl", "not_in_tree")


def test_ontology_functions(hybrid_ontology):
    assert isinstance(hybrid_ontology, Ontology)

    first_tail_ontology = hybrid_ontology._tail_ontologies.get(
        "so"
    ).get_nx_graph()
    assert len(first_tail_ontology) == 6
    assert nx.is_directed_acyclic_graph(first_tail_ontology)

    # subgraph combination
    combined_length = len(hybrid_ontology._head_ontology.get_nx_graph())
    for adapter in hybrid_ontology._tail_ontologies.values():
        combined_length += len(adapter.get_nx_graph())
    # need to add 1 for the 'merge_nodes' = False case
    combined_length += 1
    hybrid_length = len(hybrid_ontology._nx_graph)

    # subtract number of tail ontologies
    num_tail = len(hybrid_ontology._tail_ontologies)
    # subtract user extensions
    num_ext = len(hybrid_ontology._extended_nodes)

    assert hybrid_length - num_ext == combined_length - num_tail

    dgpl_ancestors = list(
        hybrid_ontology.get_ancestors("decreased gene product level")
    )
    assert "decreased gene product level" in dgpl_ancestors
    assert "altered gene product level" in dgpl_ancestors
    assert "functional effect variant" in dgpl_ancestors
    assert "sequence variant" in dgpl_ancestors
    assert "biological entity" in dgpl_ancestors
    assert "named thing" in dgpl_ancestors
    assert "entity" in dgpl_ancestors
    assert "thing with taxon" in dgpl_ancestors

    lethal_var = hybrid_ontology._nx_graph.nodes["lethal variant"]
    assert lethal_var["label"] == "SO_0001773"

    # second tail ontology: here we don't merge the nodes, but attach 'human
    # disease' as a child of 'disease'

    cf_ancestors = list(hybrid_ontology.get_ancestors("cystic fibrosis"))
    assert "cystic fibrosis" in cf_ancestors
    assert "autosomal recessive disease" in cf_ancestors
    assert "autosomal genetic disease" in cf_ancestors
    assert "hereditary disease" in cf_ancestors
    assert "human disease" in cf_ancestors
    assert "disease" in cf_ancestors
    assert "disease or phenotypic feature" in cf_ancestors
    assert "biological entity" in cf_ancestors
    assert "entity" in cf_ancestors

    # mixins?

    # user extensions
    dsdna_ancestors = list(hybrid_ontology.get_ancestors("dsDNA sequence"))
    assert "chemical entity" in dsdna_ancestors
    assert "association" in hybrid_ontology.get_ancestors(
        "mutation to tissue association"
    )

    # properties
    protein = hybrid_ontology._nx_graph.nodes["protein"]
    assert protein["label"] == "Protein"
    assert "taxon" in protein["properties"].keys()

    # synonyms
    assert "complex" in hybrid_ontology._nx_graph.nodes
    assert "macromolecular complex" not in hybrid_ontology._nx_graph.nodes


def test_show_ontology(hybrid_ontology):
    treevis = hybrid_ontology.show_ontology_structure()

    assert treevis is not None


def test_show_full_ontology(hybrid_ontology):
    treevis = hybrid_ontology.show_ontology_structure(full=True)

    assert treevis is not None


def test_write_ontology(hybrid_ontology, tmp_path):
    passed = hybrid_ontology.show_ontology_structure(to_disk=tmp_path)

    file_path = os.path.join(tmp_path, "ontology_structure.graphml")

    assert passed
    assert os.path.isfile(file_path)


def test_disconnected_exception(disconnected_mapping):
    with pytest.raises(ValueError):
        Ontology(
            head_ontology={
                "url": "test/so.owl",
                "root_node": "sequence_variant",
            },
            ontology_mapping=disconnected_mapping,
        )


def test_manual_format():
    """
    Allow manual specification of ontology file format. Also test for allowing
    no schema config use.
    """
    ontology = Ontology(
        head_ontology={
            "url": "http://semanticweb.cs.vu.nl/2009/11/sem/",
            "root_node": "Core",
            "format": "rdf",
        },
        ontology_mapping=None,
    )

    assert isinstance(ontology._nx_graph, nx.DiGraph)
    assert "event" in ontology._nx_graph.nodes
