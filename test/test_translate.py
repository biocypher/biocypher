import pytest

from biocypher._create import BioCypherEdge, BioCypherNode
from biocypher._mapping import OntologyMapping
from biocypher._ontology import Ontology
from biocypher._translate import Translator


@pytest.fixture
def mapping():
    return OntologyMapping(
        config_file='biocypher/_config/test_schema_config.yaml',
    )


@pytest.fixture
def translator(mapping):
    return Translator(mapping.extended_schema)


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
                    'url': 'test/so.obo',
                    'head_join_node': 'sequence variant',
                    'tail_join_node': 'sequence_variant',
                },
            'mondo':
                {
                    'url': 'test/mondo.obo',
                    'head_join_node': 'disease',
                    'tail_join_node': 'disease',
                }
        },
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
        ('agpl:001524', 'agpl', {}),
    ]
    t = translator.translate_nodes(id_type)

    assert all(type(n) == BioCypherNode for n in t)

    t = translator.translate_nodes(id_type)
    assert next(t).get_label() == 'protein'
    assert next(t).get_label() == 'microRNA'
    assert next(t).get_label() == 'complex'
    assert next(t).get_label() == 'reactome.pathway'
    assert next(t).get_label() == 'altered gene product level'


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


# def test_biolink_adapter(version_node, translator):
#     # current Biolink model (as opposed to rest of tests)
#     ad = BiolinkAdapter(version_node.extended_schema, translator, clear_cache=True)
#     ver = ad.biolink_version

#     assert isinstance(
#         ad.biolink_leaves['protein']['class_definition'],
#         ClassDefinition,
#     )
#     assert ver

# def test_custom_bmt_yaml(version_node, translator):
#     ad = BiolinkAdapter(
#         version_node.extended_schema,
#         translator,
#         schema=module_data_path('test-biolink-model'),
#         clear_cache=True,
#     )
#     p = ad.biolink_leaves['protein']

#     assert p['class_definition'].description == 'Test'

# def test_biolink_yaml_extension(biolink_adapter):
#     p1 = biolink_adapter.biolink_leaves['post translational interaction']
#     p2 = biolink_adapter.biolink_leaves['phosphorylation']

#     assert (
#         p1['class_definition'].description
#         == 'A pairwise interaction between two proteins' and
#         'PairwiseMolecularInteraction' in p1['ancestors'] and
#         'Entity' in p1['ancestors'] and p2['class_definition'].description
#         == 'The action of one protein phosphorylating another protein' and
#         'PostTranslationalInteraction' in p2['ancestors'] and
#         'Entity' in p2['ancestors']
#     )

# def test_translate_identifiers(translator):
#     # representation of a different schema
#     # host and guest db (which to translate)
#     # TODO
#     pass


def test_merge_multiple_inputs_node(mapping, translator):
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
    assert not any([s for s in mapping.extended_schema.keys() if '.gene' in s])
    assert any([s for s in mapping.extended_schema.keys() if '.pathway' in s])

    # check translator.translate_nodes for unique return type
    assert all([type(n) == BioCypherNode for n in t])
    assert all([n.get_label() == 'gene' for n in t])


def test_merge_multiple_inputs_edge(mapping, translator):
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
            s for s in mapping.extended_schema.keys()
            if '.gene to disease association' in s
        ],
    )
    assert any(
        [s for s in mapping.extended_schema.keys() if '.sequence variant' in s],
    )

    # check translator.translate_nodes for unique return type
    assert all([type(e) == BioCypherEdge for e in t])
    assert all([e.get_label() == 'PERTURBED_IN_DISEASE' for e in t])


def test_virtual_leaves_inherit_is_a(mapping):

    snrna = mapping.extended_schema.get('intact.snRNA sequence')

    assert 'is_a' in snrna.keys()
    assert snrna['is_a'] == ['snRNA sequence', 'nucleic acid entity']

    dsdna = mapping.extended_schema.get('intact.dsDNA sequence')

    assert dsdna['is_a'] == [
        'dsDNA sequence',
        'DNA sequence',
        'nucleic acid entity',
    ]


def test_virtual_leaves_inherit_properties(mapping):

    snrna = mapping.extended_schema.get('intact.snRNA sequence')

    assert 'properties' in snrna.keys()
    assert 'exclude_properties' in snrna.keys()


def test_inherit_properties(mapping):

    dsdna = mapping.extended_schema.get('intact.dsDNA sequence')

    assert 'properties' in dsdna.keys()
    assert 'sequence' in dsdna['properties']


def test_properties_from_config(translator):
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


# we need to load the adapter because the mappings are passed from the adapter
# to the translator
def test_translate_term(translator):
    assert translator.translate_term('hgnc') == 'Gene'
    assert (
        translator.translate_term('protein_disease') == 'PERTURBED_IN_DISEASE'
    )


def test_reverse_translate_term(translator):
    assert 'hgnc' in translator.reverse_translate_term('Gene')
    assert 'protein_disease' in translator.reverse_translate_term(
        'PERTURBED_IN_DISEASE',
    )


def test_translate_query(translator):
    # we translate to PascalCase for cypher queries, not to internal
    # sentence case
    query = 'MATCH (n:hgnc)-[r:gene_disease]->(d:Disease) RETURN n'
    assert (
        translator.translate(query) ==
        'MATCH (n:Gene)-[r:PERTURBED_IN_DISEASE]->(d:Disease) RETURN n'
    )


def test_reverse_translate_query(translator):
    # TODO cannot use sentence case in this context. include sentence to
    # pascal case and back in translation?
    query = 'MATCH (n:Known.SequenceVariant)-[r:Known.SequenceVariant.VariantToGeneAssociation]->(g:Gene) RETURN n'
    with pytest.raises(NotImplementedError):
        translator.reverse_translate(query)

    query = 'MATCH (n:Known.SequenceVariant)-[r:Known.SequenceVariant.VariantToGeneAssociation]->(g:Protein) RETURN n'
    assert (
        translator.reverse_translate(query) ==
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

    m = translator.get_missing_biolink_types()
    assert m.get('missing_protein') == 2
    assert m.get('missing_pathway') == 1


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
