from linkml_runtime.linkml_model.meta import ClassDefinition
import pytest

from biocypher._check import VersionNode
from biocypher._config import module_data_path
from biocypher._create import BioCypherEdge, BioCypherNode
from biocypher._driver import Driver
from biocypher._translate import (
    BiolinkAdapter,
    gen_translate_edges,
    gen_translate_nodes,
)

__all__ = ['driver', 'test_adapter', 'test_biolink_yaml_extension', 'test_custom_bmt_yaml', 'test_translate_edges', 'test_translate_identifiers', 'test_translate_nodes', 'version_node']




@pytest.fixture
def version_node():
    return VersionNode(
        from_config=True, 
        config_file="test_schema_config", 
        offline=True,
    )


def test_translate_nodes(version_node):
    id_type = [
        ('G9205', 'protein', {'taxon': 9606}),
        ('hsa-miR-132-3p', 'mirna', {'taxon': 9606}),
        ('ASDB_OSBS', 'complex', {'taxon': 9606}),
    ]
    t = gen_translate_nodes(version_node.leaves, id_type)

    assert all(type(n) == BioCypherNode for n in t)

    t = gen_translate_nodes(version_node.leaves, id_type)
    assert next(t).get_label() == 'Protein'
    assert next(t).get_label() == 'microRNA'
    assert next(t).get_label() == 'MacromolecularComplexMixin'


def test_translate_edges(version_node):
    v = version_node
    # edge type association (defined in `schema_config.yaml`)
    src_tar_type_edge = [
        ('G15258', 'MONDO1', 'gene_disease', {}),
        ('G15258', 'MONDO2', 'protein_disease', {}),
    ]
    t = gen_translate_edges(v.leaves, src_tar_type_edge)
    t = list(t)

    # node type association (defined in `schema_config.yaml`)
    src_tar_type_node = [
        ('G21058', 'G50127', 'post_translational', {'prop1': 'test'}),
        (
            'G22418',
            'G50123',
            'post_translational',
            {'directed': 'arbitrary_string'},
        ),
        (
            'G15258',
            'G16347',
            'post_translational',
            {'directed': True, 'effect': -1},
        ),
    ]
    t = gen_translate_edges(v.leaves, src_tar_type_node)

    n = next(t)
    n = next(t)
    assert n.get_source_edge().get_label() == 'IS_PART_OF'
    n = next(t)
    no = n.get_node()
    assert (
        type(n.get_node()) == BioCypherNode
        and type(n.get_source_edge()) == BioCypherEdge
        and type(n.get_target_edge()) == BioCypherEdge
    )
    assert n.get_node().get_id() == 'G15258_G16347_True_-1'
    assert n.get_source_edge().get_source_id() == 'G15258'
    assert n.get_target_edge().get_label() == 'IS_TARGET_OF'


def test_adapter(version_node):
    ad = BiolinkAdapter(version_node.leaves, schema='biolink')

    assert isinstance(
        ad.biolink_leaves['Protein']['class_definition'], ClassDefinition,
    )


def test_custom_bmt_yaml(version_node):
    ad = BiolinkAdapter(
        version_node.leaves, schema=module_data_path('test-biolink-model'),
    )
    p = ad.biolink_leaves['Protein']

    assert p['class_definition'].description == 'Test'


def test_biolink_yaml_extension(version_node):
    ad = BiolinkAdapter(
        version_node.leaves,
        schema='biocypher', # this is the default
        # unstable, move to test yaml
    )
    p1 = ad.biolink_leaves['PostTranslationalInteraction']
    p2 = ad.biolink_leaves['Phosphorylation']

    assert (
        p1['class_definition'].description
        == 'A pairwise interaction between two proteins'
        and 'biolink:PairwiseMolecularInteraction' in p1['ancestors']
        and 'biolink:Entity' in p1['ancestors']
        and p2['class_definition'].description
        == 'The action of one protein phosphorylating another protein'
        and 'biolink:PostTranslationalInteraction' in p2['ancestors']
        and 'biolink:Entity' in p2['ancestors']
    )


def test_translate_identifiers(version_node):
    # representation of a different schema
    # host and guest db (which to translate)
    pass
