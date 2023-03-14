import os

import networkx as nx

from biocypher._ontology import Ontology


def test_biolink_adapter(biolink_adapter):
    assert biolink_adapter.get_root_label() == 'entity'
    assert biolink_adapter.get_nx_graph().number_of_nodes() > 100

    assert 'biological entity' in biolink_adapter.get_ancestors('gene')
    assert 'macromolecular machine mixin' in biolink_adapter.get_ancestors(
        'macromolecular complex'
    )


def test_so_adapter(so_adapter):
    assert so_adapter.get_root_label() == 'sequence_variant'

    # here without underscores
    assert 'sequence variant' in so_adapter.get_ancestors('lethal variant')


def test_go_adapter(go_adapter):
    assert go_adapter.get_root_label() == 'molecular_function'

    assert 'molecular function' in go_adapter.get_ancestors(
        'RNA helicase activity'
    )


def test_mondo_adapter(mondo_adapter):
    assert mondo_adapter.get_root_label() == 'disease'

    assert 'human disease' in mondo_adapter.get_ancestors('cystic fibrosis')


def test_ontology_functions(hybrid_ontology):
    assert isinstance(hybrid_ontology, Ontology)

    first_tail_ontology = hybrid_ontology._tail_ontologies.get('so'
                                                              ).get_nx_graph()
    assert len(first_tail_ontology) == 6
    assert nx.is_directed_acyclic_graph(first_tail_ontology)

    # subgraph combination
    combined_length = len(hybrid_ontology._head_ontology.get_nx_graph())
    for adapter in hybrid_ontology._tail_ontologies.values():
        combined_length += len(adapter.get_nx_graph())
    hybrid_length = len(hybrid_ontology._nx_graph)

    # subtract number of tail ontologies
    num_tail = len(hybrid_ontology._tail_ontologies)
    # subtract user extensions
    num_ext = len(hybrid_ontology._extended_nodes)

    assert hybrid_length - num_ext == combined_length - num_tail

    dgpl_ancestors = list(
        hybrid_ontology.get_ancestors('decreased gene product level')
    )
    assert len(dgpl_ancestors) == 8
    assert 'altered gene product level' in dgpl_ancestors
    assert 'sequence variant' in dgpl_ancestors
    assert 'entity' in dgpl_ancestors

    lethal_var = hybrid_ontology._nx_graph.nodes['lethal variant']
    assert lethal_var['label'] == 'SO_0001773'

    # second tail ontology
    cf_ancestors = list(hybrid_ontology.get_ancestors('cystic fibrosis'))
    assert len(cf_ancestors) == 11
    assert 'disease' in cf_ancestors
    assert 'disease or phenotypic feature' in cf_ancestors
    assert 'entity' in cf_ancestors

    # mixins?

    # user extensions
    dsdna_ancestors = list(hybrid_ontology.get_ancestors('dsDNA sequence'))
    assert 'chemical entity' in dsdna_ancestors
    assert 'association' in hybrid_ontology.get_ancestors(
        'mutation to tissue association'
    )

    # properties
    protein = hybrid_ontology._nx_graph.nodes['protein']
    assert protein['label'] == 'Protein'
    assert 'taxon' in protein['properties'].keys()

    # synonyms
    assert 'complex' in hybrid_ontology._nx_graph.nodes
    assert 'macromolecular complex' not in hybrid_ontology._nx_graph.nodes


def test_show_ontology(hybrid_ontology):
    treevis = hybrid_ontology.show_ontology_structure()

    assert treevis is not None


def test_show_full_ontology(hybrid_ontology):
    treevis = hybrid_ontology.show_ontology_structure(full=True)

    assert treevis is not None


def test_write_ontology(hybrid_ontology, path):
    passed = hybrid_ontology.show_ontology_structure(to_disk=path)

    f = os.path.join(path, 'ontology_structure.graphml')

    assert passed
    assert os.path.isfile(f)
