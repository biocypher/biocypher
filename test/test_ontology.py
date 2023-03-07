import pytest
import networkx as nx

from biocypher._ontology import Ontology, OntologyAdapter


@pytest.fixture
def biolink_adapter():
    return OntologyAdapter(
        'https://raw.githubusercontent.com/biolink/biolink-model/master/biolink-model.owl.ttl',
        'entity'
    )


@pytest.fixture
def so_adapter():
    return OntologyAdapter(
        'https://raw.githubusercontent.com/The-Sequence-Ontology/SO-Ontologies/master/Ontology_Files/so.owl',
        'sequence_variant'
    )


@pytest.fixture
def go_adapter():
    return OntologyAdapter(
        'http://purl.obolibrary.org/obo/go.owl', 'molecular_function'
    )


@pytest.fixture
def mondo_adapter():
    return OntologyAdapter(
        'http://purl.obolibrary.org/obo/mondo.owl', 'disease'
    )


@pytest.fixture
def hybrid_ontology():
    return Ontology(
        head_ontology={
            'url':
                'https://raw.githubusercontent.com/biolink/biolink-model/master/biolink-model.owl.ttl',
            'root_node':
                'entity',
        },
        tail_ontologies={
            'so':
                {
                    'url': 'test/so.owl',
                    'head_join_node': 'sequence variant',
                    'tail_join_node': 'sequence_variant',
                },
            'mondo':
                {
                    'url': 'test/mondo.owl',
                    'head_join_node': 'disease',
                    'tail_join_node': 'disease',
                }
        },
    )


def test_biolink_adapter(biolink_adapter):
    assert biolink_adapter.get_root_label() == 'entity'
    assert biolink_adapter.get_nx_graph().number_of_nodes() > 100

    assert 'biological entity' in biolink_adapter.get_ancestors('gene')
    assert 'macromolecular machine mixin' in biolink_adapter.get_ancestors(
        'macromolecular complex'
    )


def test_so_adapter(so_adapter):
    assert so_adapter.get_root_label() == 'sequence_variant'
    assert so_adapter.get_nx_graph().number_of_nodes() > 100

    # here without underscores
    assert 'sequence variant' in so_adapter.get_ancestors('lethal variant')


def test_go_adapter(go_adapter):
    assert go_adapter.get_root_label() == 'molecular_function'
    assert go_adapter.get_nx_graph().number_of_nodes() > 100

    assert 'molecular function' in go_adapter.get_ancestors(
        'RNA helicase activity'
    )


def test_mondo_adapter(mondo_adapter):
    assert mondo_adapter.get_root_label() == 'disease'
    assert mondo_adapter.get_nx_graph().number_of_nodes() > 100

    assert 'disease' in mondo_adapter.get_ancestors('cancer')


def test_hybridise(hybrid_ontology):
    assert isinstance(hybrid_ontology, Ontology)

    first_tail_ontology = hybrid_ontology._tail_ontologies.get('so'
                                                              ).get_nx_graph()
    assert len(first_tail_ontology) == 6
    assert nx.is_directed_acyclic_graph(first_tail_ontology)

    # subgraph combination
    combined_length = len(hybrid_ontology._head_ontology.get_nx_graph())
    for adapter in hybrid_ontology._tail_ontologies.values():
        combined_length += len(adapter.get_nx_graph())
    hybrid_length = len(hybrid_ontology._hybrid_ontology_nx_graph)

    assert hybrid_length == combined_length - len(
        hybrid_ontology._tail_ontologies
    )

    # TODO where does the +1 come from? i would assume that by merging head and
    # tail nodes, we remove one for each tail ontology. however, we are,
    # somehow, losing one additional node.

    # get predecessors of terminal node from hybrid ontology (successors because
    # of inverted graph)
    predecessors = list(
        hybrid_ontology.get_ancestors('decreased gene product level')
    )
    assert len(predecessors) == 8
    assert 'altered gene product level' in predecessors
    assert 'sequence variant' in predecessors
    assert 'entity' in predecessors

    lethal_var = hybrid_ontology._hybrid_ontology_nx_graph.nodes[
        'lethal variant']
    assert lethal_var['label'] == 'SO_0001773'

    # second tail ontology
    cf_predecessors = list(hybrid_ontology.get_ancestors('cystic fibrosis'))
    assert len(cf_predecessors) == 11
    assert 'disease' in cf_predecessors
    assert 'disease or phenotypic feature' in cf_predecessors
    assert 'entity' in cf_predecessors
    # mixins?
