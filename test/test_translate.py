from networkx.classes.graph import Graph
from linkml_runtime.linkml_model.meta import ClassDefinition
import pytest
import networkx as nx

from biocypher._config import module_data_path
from biocypher._create import VersionNode, BioCypherEdge, BioCypherNode
from biocypher._translate import Translator, BiolinkAdapter, OntologyAdapter

__all__ = [
    'biolink_adapter',
    'test_ad_hoc_children_node',
    'test_adapter',
    'test_biolink_yaml_extension',
    'test_custom_bmt_yaml',
    'test_exclude_properties',
    'test_inherit_properties',
    'test_leaves_of_ad_hoc_child',
    'test_log_missing_nodes',
    'test_merge_multiple_inputs_edge',
    'test_merge_multiple_inputs_node',
    'test_multiple_inheritance',
    'test_multiple_inputs_multiple_virtual_leaves_rel_as_node',
    'test_properties_from_config',
    'test_reverse_translate_query',
    'test_reverse_translate_term',
    'test_specific_and_generic_ids',
    'test_translate_edges',
    'test_translate_identifiers',
    'test_translate_nodes',
    'test_translate_query',
    'test_translate_term',
    'test_virtual_leaves_inherit_is_a',
    'test_virtual_leaves_inherit_properties',
    'translator',
    'version_node',
]


@pytest.fixture
def version_node():
    return VersionNode(
        from_config=True,
        config_file='biocypher/_config/test_schema_config.yaml',
        offline=True,
    )


@pytest.fixture
def translator(version_node):
    return Translator(version_node.leaves)


@pytest.fixture
def biolink_adapter(version_node):
    return BiolinkAdapter(
        version_node.leaves,
        schema=module_data_path('test-biolink-model'),
        clear_cache=True,
    )


@pytest.fixture
def ontology_adapter(biolink_adapter):
    return OntologyAdapter(
        head_join_node='sequence variant',
        tail_join_node='sequence_variant',
        biolink_adapter=biolink_adapter,
        tail_ontology_url='test/so.obo',
    )


def test_translate_nodes(translator):
    id_type = [
        (
            'G9205',
            'protein',
            {
                'taxon': 9606,
            },
        ),
        (
            'hsa-miR-132-3p',
            'mirna',
            {
                'taxon': 9606,
            },
        ),
        (
            'ASDB_OSBS',
            'complex',
            {
                'taxon': 9606,
            },
        ),
        ('REACT:25520', 'reactome', {}),
    ]
    t = translator.translate_nodes(id_type)

    assert all(type(n) == BioCypherNode for n in t)

    t = translator.translate_nodes(id_type)
    assert next(t).get_label() == 'protein'
    assert next(t).get_label() == 'microRNA'
    assert next(t).get_label() == 'complex'


def test_specific_and_generic_ids(translator):
    id_type = [
        (
            'CHAT',
            'hgnc',
            {
                'taxon': 9606,
            },
        ),
        ('REACT:25520', 'reactome', {}),
    ]
    t = list(translator.translate_nodes(id_type))

    assert t[0].get_id() == 'CHAT'
    assert t[0].get_properties().get('preferred_id') == 'hgnc'
    assert t[0].get_properties().get('id') == 'CHAT'
    assert t[1].get_id() == 'REACT:25520'
    assert t[1].get_properties().get('preferred_id') == 'reactome'
    assert t[1].get_properties().get('id') == 'REACT:25520'


def test_translate_edges(translator):
    # edge type association (defined in `schema_config.yaml`)
    src_tar_type_edge = [
        ('G15258', 'MONDO1', 'gene_disease', {}),
        ('G15258', 'MONDO2', 'protein_disease', {}),
        ('G15258', 'G15242', 'phosphorylation', {}),
    ]

    def gen_edges():
        yield from src_tar_type_edge

    t = translator.translate_edges(gen_edges())

    assert type(next(t)) == BioCypherEdge
    assert next(t).get_label() == 'PERTURBED_IN_DISEASE'
    assert next(t).get_label() == 'phosphorylation'

    # node type association (defined in `schema_config.yaml`)
    src_tar_type_node = [
        (
            'G21058',
            'G50127',
            'post_translational',
            {
                'prop1': 'test',
            },
        ),
        (
            'G22418',
            'G50123',
            'post_translational',
            {
                'directed': 'arbitrary_string',
            },
        ),
        (
            'G15258',
            'G16347',
            'post_translational',
            {
                'directed': True,
                'effect': -1,
            },
        ),
    ]
    t = translator.translate_edges(src_tar_type_node)
    t = list(t)

    n1 = t[0]
    n2 = t[1]
    n3 = t[2]

    assert n1.get_source_edge().get_label() == 'IS_PART_OF'
    assert n2.get_source_edge().get_label() == 'IS_PART_OF'
    assert n3.get_target_edge().get_label() == 'IS_TARGET_OF'
    assert (
        type(n1.get_node()) == BioCypherNode and
        type(n1.get_source_edge()) == BioCypherEdge and
        type(n1.get_target_edge()) == BioCypherEdge
    )
    assert n3.get_node().get_id() == 'G15258_G16347_True_-1'
    assert n3.get_source_edge().get_source_id() == 'G15258'


def test_adapter(version_node):
    # current Biolink model (as opposed to rest of tests)
    ad = BiolinkAdapter(version_node.leaves, clear_cache=True)
    ver = ad.biolink_version

    assert isinstance(
        ad.biolink_leaves['protein']['class_definition'],
        ClassDefinition,
    )
    assert ver


def test_custom_bmt_yaml(version_node):
    ad = BiolinkAdapter(
        version_node.leaves,
        schema=module_data_path('test-biolink-model'),
        clear_cache=True,
    )
    p = ad.biolink_leaves['protein']

    assert p['class_definition'].description == 'Test'


def test_biolink_yaml_extension(biolink_adapter):
    p1 = biolink_adapter.biolink_leaves['post translational interaction']
    p2 = biolink_adapter.biolink_leaves['phosphorylation']

    assert (
        p1['class_definition'].description
        == 'A pairwise interaction between two proteins' and
        'PairwiseMolecularInteraction' in p1['ancestors'] and
        'Entity' in p1['ancestors'] and p2['class_definition'].description
        == 'The action of one protein phosphorylating another protein' and
        'PostTranslationalInteraction' in p2['ancestors'] and
        'Entity' in p2['ancestors']
    )


def test_translate_identifiers(translator):
    # representation of a different schema
    # host and guest db (which to translate)
    # TODO
    pass


def test_merge_multiple_inputs_node(version_node, translator):
    # Gene has two input labels and one preferred ID
    # no virtual leaves should be created
    # both inputs should lead to creation of the same node type

    # define nodes
    id_type = [
        (
            'CHAT',
            'hgnc',
            {
                'taxon': 9606,
            },
        ),
        (
            'CHRNA4',
            'ensg',
            {
                'taxon': 9606,
            },
        ),
    ]
    t = list(translator.translate_nodes(id_type))

    assert t

    # check unique node type
    assert not any([s for s in version_node.leaves.keys() if '.gene' in s])
    assert any([s for s in version_node.leaves.keys() if '.pathway' in s])

    # check translator.translate_nodes for unique return type
    assert all([type(n) == BioCypherNode for n in t])
    assert all([n.get_label() == 'gene' for n in t])


def test_merge_multiple_inputs_edge(version_node, translator):
    # GeneToDiseaseAssociation has two input labels and one preferred ID
    # no virtual leaves should be created
    # both inputs should lead to creation of the same edge type
    # intersects with driver/writer function

    # define nodes
    src_tar_type = [
        (
            'CHAT',
            'AD',
            'gene_disease',
            {
                'taxon': 9606,
            },
        ),
        (
            'CHRNA4',
            'AD',
            'protein_disease',
            {
                'taxon': 9606,
            },
        ),
    ]
    t = list(translator.translate_edges(src_tar_type))

    # check unique edge type
    assert not any(
        [
            s for s in version_node.leaves.keys()
            if '.gene to disease association' in s
        ],
    )
    assert any(
        [s for s in version_node.leaves.keys() if '.sequence variant' in s],
    )

    # check translator.translate_nodes for unique return type
    assert all([type(e) == BioCypherEdge for e in t])
    assert all([e.get_label() == 'PERTURBED_IN_DISEASE' for e in t])


def test_multiple_inputs_multiple_virtual_leaves_rel_as_node(biolink_adapter):
    vtg = biolink_adapter.biolink_leaves['variant to gene association']
    kvtg = biolink_adapter.biolink_leaves[
        'known.sequence variant.variant to gene association']
    svtg = biolink_adapter.biolink_leaves[
        'known.sequence variant.variant to gene association']

    assert (
        isinstance(vtg['class_definition'], ClassDefinition) and
        'VariantToGeneAssociation' in kvtg['ancestors'] and
        'VariantToGeneAssociation' in svtg['ancestors']
    )


def test_virtual_leaves_inherit_is_a(version_node):

    snrna = version_node.leaves.get('intact.snRNA sequence')

    assert 'is_a' in snrna.keys()
    assert snrna['is_a'] == ['snRNA sequence', 'nucleic acid entity']

    dsdna = version_node.leaves.get('intact.dsDNA sequence')

    assert dsdna['is_a'] == [
        'dsDNA sequence',
        'DNA sequence',
        'nucleic acid entity',
    ]


def test_virtual_leaves_inherit_properties(version_node):

    snrna = version_node.leaves.get('intact.snRNA sequence')

    assert 'properties' in snrna.keys()
    assert 'exclude_properties' in snrna.keys()


def test_ad_hoc_children_node(biolink_adapter):

    se = biolink_adapter.biolink_leaves['side effect']

    assert 'PhenotypicFeature' in se['ancestors']


def test_leaves_of_ad_hoc_child(biolink_adapter):

    snrna = biolink_adapter.biolink_leaves.get('intact.snRNA sequence')

    assert snrna
    assert 'SnRNASequence' in snrna['ancestors']

    dsdna = biolink_adapter.biolink_leaves.get('intact.dsDNA sequence')

    assert dsdna['ancestors'][1:4] == [
        'DsDNASequence',
        'DNASequence',
        'NucleicAcidEntity',
    ]


def test_inherit_properties(version_node):

    dsdna = version_node.leaves.get('intact.dsDNA sequence')

    assert 'properties' in dsdna.keys()
    assert 'sequence' in dsdna['properties']


def test_multiple_inheritance(biolink_adapter):

    mta = biolink_adapter.biolink_leaves.get('mutation to tissue association')

    assert 'MutationToTissueAssociation' in mta['ancestors']
    assert 'GenotypeToTissueAssociation' in mta['ancestors']
    assert 'EntityToTissueAssociation' in mta['ancestors']
    assert 'Association' in mta['ancestors']


def test_synonym(biolink_adapter):

    comp = biolink_adapter.biolink_leaves.get('complex')

    assert comp
    assert 'Complex' in comp['ancestors']
    assert 'MacromolecularComplexMixin' in comp['ancestors']


def test_properties_from_config(version_node, translator):
    id_type = [
        (
            'G49205',
            'protein',
            {
                'taxon': 9606,
                'name': 'test',
            },
        ),
        (
            'G92035',
            'protein',
            {
                'taxon': 9606,
            },
        ),
        (
            'G92205',
            'protein',
            {
                'taxon': 9606,
                'name': 'test2',
                'test': 'should_not_be_returned',
            },
        ),
    ]
    t = translator.translate_nodes(id_type)

    r = list(t)
    assert (
        'name' in r[0].get_properties().keys() and
        'name' in r[1].get_properties().keys() and
        'test' not in r[2].get_properties().keys()
    )

    src_tar_type = [
        (
            'G49205',
            'AD',
            'gene_gene',
            {
                'directional': True,
                'score': 0.5,
            },
        ),
        (
            'G92035',
            'AD',
            'gene_gene',
            {
                'directional': False,
                'curated': True,
                'score': 0.5,
                'test': 'should_not_be_returned',
            },
        ),
    ]

    t = translator.translate_edges(src_tar_type)

    r = list(t)
    assert (
        'directional' in r[0].get_properties().keys() and
        'directional' in r[1].get_properties().keys() and
        'curated' in r[1].get_properties().keys() and
        'score' in r[0].get_properties().keys() and
        'score' in r[1].get_properties().keys() and
        'test' not in r[1].get_properties().keys()
    )


def test_exclude_properties(translator):
    id_type = [
        (
            'CHAT',
            'ensg',
            {
                'taxon': 9606,
                'accession': 'should_not_be_returned',
            },
        ),
        (
            'ACHE',
            'ensg',
            {
                'taxon': 9606,
            },
        ),
    ]
    t = translator.translate_nodes(id_type)

    r = list(t)
    assert (
        'taxon' in r[0].get_properties().keys() and
        'taxon' in r[1].get_properties().keys() and
        'accession' not in r[0].get_properties().keys()
    )

    src_tar_type = [
        (
            'G49205',
            'AD',
            'gene_disease',
            {
                'directional': True,
                'score': 0.5,
            },
        ),
        (
            'G92035',
            'AD',
            'gene_disease',
            {
                'directional': False,
                'score': 0.5,
                'accession': 'should_not_be_returned',
            },
        ),
    ]

    t = translator.translate_edges(src_tar_type)

    r = list(t)
    assert (
        'directional' in r[0].get_properties().keys() and
        'directional' in r[1].get_properties().keys() and
        'score' in r[0].get_properties().keys() and
        'score' in r[1].get_properties().keys() and
        'accession' not in r[1].get_properties().keys()
    )


def test_translate_term(biolink_adapter):
    assert biolink_adapter.translate_term('hgnc') == 'Gene'
    assert (
        biolink_adapter.translate_term('protein_disease') ==
        'PERTURBED_IN_DISEASE'
    )


def test_reverse_translate_term(biolink_adapter):
    assert 'hgnc' in biolink_adapter.reverse_translate_term('Gene')
    assert 'protein_disease' in biolink_adapter.reverse_translate_term(
        'PERTURBED_IN_DISEASE',
    )


def test_translate_query(biolink_adapter):
    # we translate to PascalCase for cypher queries, not to internal
    # sentence case
    query = 'MATCH (n:hgnc)-[r:gene_disease]->(d:Disease) RETURN n'
    assert (
        biolink_adapter.translate(query) ==
        'MATCH (n:Gene)-[r:PERTURBED_IN_DISEASE]->(d:Disease) RETURN n'
    )


def test_reverse_translate_query(biolink_adapter):
    # TODO cannot use sentence case in this context. include sentence to
    # pascal case and back in translation?
    query = 'MATCH (n:Known.SequenceVariant)-[r:Known.SequenceVariant.VariantToGeneAssociation]->(g:Gene) RETURN n'
    with pytest.raises(NotImplementedError):
        biolink_adapter.reverse_translate(query)

    query = 'MATCH (n:Known.SequenceVariant)-[r:Known.SequenceVariant.VariantToGeneAssociation]->(g:Protein) RETURN n'
    assert (
        biolink_adapter.reverse_translate(query) ==
        'MATCH (n:Known_variant)-[r:VARIANT_FOUND_IN_GENE_Known_variant_Gene]->(g:protein) RETURN n'
    )


def test_log_missing_nodes(translator):
    tn = translator.translate_nodes(
        [
            (
                'G49205',
                'missing_protein',
                {
                    'taxon': 9606,
                },
            ),
            ('G92035', 'missing_protein', {}),
            ('REACT:25520', 'missing_pathway', {}),
        ],
    )

    tn = list(tn)

    m = translator.get_missing_bl_types()
    assert m.get('missing_protein') == 2
    assert m.get('missing_pathway') == 1


def test_show_ontology(biolink_adapter):
    treevis = biolink_adapter.show_ontology_structure()

    assert treevis is not None


def test_strict_mode_error(translator):
    translator.strict_mode = True

    n1 = (
        'n2', 'Test', {
            'prop': 'val',
            'source': 'test',
            'licence': 'test',
            'version': 'test'
        }
    )

    assert list(translator.translate_nodes([n1])) is not None

    # test 'license' instead of 'licence'
    n2 = (
        'n2', 'Test', {
            'prop': 'val',
            'source': 'test',
            'license': 'test',
            'version': 'test'
        }
    )

    assert list(translator.translate_nodes([n2])) is not None

    n3 = ('n1', 'Test', {'prop': 'val'})

    with pytest.raises(ValueError):
        list(translator.translate_nodes([n1, n2, n3]))

    e1 = (
        'n1', 'n2', 'Test', {
            'prop': 'val',
            'source': 'test',
            'licence': 'test',
            'version': 'test',
        }
    )

    assert list(translator.translate_edges([e1])) is not None

    e2 = ('n1', 'n2', 'Test', {'prop': 'val'})

    with pytest.raises(ValueError):
        list(translator.translate_edges([e1, e2]))


def test_strict_mode_property_filter(translator):
    translator.strict_mode = True

    p1 = (
        'p1', 'protein', {
            'taxon': 9606,
            'source': 'test',
            'licence': 'test',
            'version': 'test',
        }
    )

    l = list(translator.translate_nodes([p1]))

    assert 'source' in l[0].get_properties().keys()
    assert 'licence' in l[0].get_properties().keys()
    assert 'version' in l[0].get_properties().keys()


def test_networkx_from_treedict(biolink_adapter):
    graph = biolink_adapter.get_networkx_graph()

    assert isinstance(graph, Graph)
    assert 'sequence variant' in graph.nodes


def test_generic_ontology_adapter(ontology_adapter):
    assert isinstance(ontology_adapter, OntologyAdapter)
    assert len(ontology_adapter.tail_ontology) == 7
    assert nx.is_directed_acyclic_graph(ontology_adapter.tail_ontology)

    # subgraph combination
    combined_length = len(ontology_adapter.head_ontology
                         ) + len(ontology_adapter.tail_ontology)
    assert len(ontology_adapter.hybrid_ontology) == combined_length - 2
