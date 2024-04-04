import pytest

from biocypher._create import BioCypherEdge, BioCypherNode
from biocypher._deduplicate import Deduplicator


@pytest.mark.parametrize("length", [4], scope="module")
def test_duplicate_nodes(_get_nodes):
    dedup = Deduplicator()
    nodes = _get_nodes
    nodes.append(
        BioCypherNode(
            node_id="p1",
            node_label="protein",
            properties={
                "name": "StringProperty1",
                "score": 4.32,
                "taxon": 9606,
                "genes": ["gene1", "gene2"],
            },
        )
    )

    for node in nodes:
        dedup.node_seen(node)

    assert "protein" in dedup.duplicate_entity_types
    assert "p1" in dedup.duplicate_entity_ids


@pytest.mark.parametrize("length", [4], scope="module")
def test_get_duplicate_nodes(_get_nodes):
    dedup = Deduplicator()
    nodes = _get_nodes
    nodes.append(
        BioCypherNode(
            node_id="p1",
            node_label="protein",
            properties={
                "name": "StringProperty1",
                "score": 4.32,
                "taxon": 9606,
                "genes": ["gene1", "gene2"],
            },
        )
    )

    for node in nodes:
        dedup.node_seen(node)

    duplicates = dedup.get_duplicate_nodes()
    types = duplicates[0]
    ids = duplicates[1]

    assert "protein" in types
    assert "p1" in ids


@pytest.mark.parametrize("length", [4], scope="module")
def test_duplicate_edges(_get_edges):
    dedup = Deduplicator()
    edges = _get_edges
    edges.append(
        BioCypherEdge(
            relationship_id="mrel2",
            source_id="m2",
            target_id="p3",
            relationship_label="Is_Mutated_In",
            properties={
                "score": 4.32,
                "taxon": 9606,
                "genes": ["gene1", "gene2"],
            },
        )
    )
    # this will fail if we go beyond concatenation of ids

    for edge in edges:
        dedup.edge_seen(edge)

    assert "Is_Mutated_In" in dedup.duplicate_relationship_types
    assert ("mrel2") in dedup.duplicate_relationship_ids


@pytest.mark.parametrize("length", [4], scope="module")
def test_get_duplicate_edges(_get_edges):
    dedup = Deduplicator()
    edges = _get_edges
    edges.append(
        BioCypherEdge(
            relationship_id="mrel2",
            source_id="m2",
            target_id="p3",
            relationship_label="Is_Mutated_In",
            properties={
                "score": 4.32,
                "taxon": 9606,
                "genes": ["gene1", "gene2"],
            },
        )
    )
    # this will fail if we go beyond concatenation of ids

    for edge in edges:
        dedup.edge_seen(edge)

    duplicates = dedup.get_duplicate_edges()
    types = duplicates[0]
    ids = duplicates[1]

    assert "Is_Mutated_In" in types
    assert ("mrel2") in ids
