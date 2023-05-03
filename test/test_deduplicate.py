import pytest
from biocypher._create import BioCypherNode, BioCypherEdge
from biocypher._deduplicate import Deduplicator

@pytest.mark.parametrize('l', [4], scope='module')
def test_duplicate_nodes(_get_nodes):
    dedup = Deduplicator()
    nodes = _get_nodes
    nodes.append(
        BioCypherNode(
            node_id='p1',
            node_label='protein',
            properties={
                'name': 'StringProperty1',
                'score': 4.32,
                'taxon': 9606,
                'genes': ['gene1', 'gene2']
            }
        )
    )

    for node in nodes:
        dedup.node_seen(node)

    assert 'protein' in dedup.duplicate_node_types
    assert 'p1' in dedup.duplicate_node_ids


@pytest.mark.parametrize('l', [4], scope='module')
def test_get_duplicate_nodes(_get_nodes):
    dedup = Deduplicator()
    nodes = _get_nodes
    nodes.append(
        BioCypherNode(
            node_id='p1',
            node_label='protein',
            properties={
                'name': 'StringProperty1',
                'score': 4.32,
                'taxon': 9606,
                'genes': ['gene1', 'gene2']
            }
        )
    )

    for node in nodes:
        dedup.node_seen(node)

    d = dedup.get_duplicate_nodes()
    types = d[0]
    ids = d[1]

    assert 'protein' in types
    assert 'p1' in ids

@pytest.mark.parametrize('l', [4], scope='module')
def test_duplicate_edges(_get_edges):
    dedup = Deduplicator()
    edges = _get_edges
    edges.append(
        BioCypherEdge(
            source_id='m2',
            target_id='p3',
            relationship_label='Is_Mutated_In',
            properties={
                'score': 4.32,
                'taxon': 9606,
                'genes': ['gene1', 'gene2']
            }
        )
    )
    # this will fail if we go beyond concatenation of ids

    for edge in edges:
        dedup.edge_seen(edge)

    assert 'Is_Mutated_In' in dedup.duplicate_edge_types
    assert ('m2_p3') in dedup.duplicate_edge_ids

@pytest.mark.parametrize('l', [4], scope='module')
def test_get_duplicate_edges(_get_edges):
    dedup = Deduplicator()
    edges = _get_edges
    edges.append(
        BioCypherEdge(
            source_id='m2',
            target_id='p3',
            relationship_label='Is_Mutated_In',
            properties={
                'score': 4.32,
                'taxon': 9606,
                'genes': ['gene1', 'gene2']
            }
        )
    )
    # this will fail if we go beyond concatenation of ids

    for edge in edges:
        dedup.edge_seen(edge)

    d = dedup.get_duplicate_edges()
    types = d[0]
    ids = d[1]

    assert 'Is_Mutated_In' in types
    assert ('m2_p3') in ids