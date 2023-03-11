import os
import random
import string
import tempfile

import pytest

from biocypher import config as bcy_config
from biocypher._core import BioCypher
from biocypher._create import BioCypherNode
from biocypher._driver import _Driver
from biocypher._mapping import OntologyMapping
from biocypher._ontology import Ontology, OntologyAdapter
from biocypher._translate import Translator


# temporary output paths
def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


@pytest.fixture(name='path', scope='session')
def path():
    path = os.path.join(
        tempfile.gettempdir(),
        f'biocypher-test-{get_random_string(5)}',
    )
    os.makedirs(path, exist_ok=True)
    return path


# biocypher node generator
@pytest.fixture(scope='function')
def _get_nodes(l: int) -> list:
    nodes = []
    for i in range(l):
        bnp = BioCypherNode(
            node_id=f'p{i+1}',
            node_label='protein',
            preferred_id='uniprot',
            properties={
                'score': 4 / (i + 1),
                'name': 'StringProperty1',
                'taxon': 9606,
                'genes': ['gene1', 'gene2'],
            },
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            node_id=f'm{i+1}',
            node_label='microRNA',
            preferred_id='mirbase',
            properties={
                'name': 'StringProperty1',
                'taxon': 9606,
            },
        )
        nodes.append(bnm)

    return nodes


@pytest.fixture(scope='session')
def ontology_mapping():
    return OntologyMapping(
        config_file='biocypher/_config/test_schema_config.yaml'
    )


@pytest.fixture(scope='session')
def translator(ontology_mapping):
    return Translator(ontology_mapping)


@pytest.fixture(scope='session')
def biolink_adapter():
    return OntologyAdapter(
        '/Users/slobentanzer/Downloads/biolink-model.owl.ttl', 'entity'
    )


@pytest.fixture(scope='session')
def so_adapter():
    return OntologyAdapter('test/so.owl', 'sequence_variant')


@pytest.fixture(scope='session')
def go_adapter():
    return OntologyAdapter('test/go.owl', 'molecular_function')


@pytest.fixture(scope='session')
def mondo_adapter():
    return OntologyAdapter('test/mondo.owl', 'disease')


@pytest.fixture(scope='session')
def hybrid_ontology(ontology_mapping):
    return Ontology(
        head_ontology={
            'url': '/Users/slobentanzer/Downloads/biolink-model.owl.ttl',
            'root_node': 'entity',
        },
        ontology_mapping=ontology_mapping,
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


# CLI option parser
def pytest_addoption(parser):

    options = (
        ('database_name', 'The Neo4j database to be used for tests.'),
        ('user', 'Tests access Neo4j as this user.'),
        ('password', 'Password to access Neo4j.'),
        ('uri', 'URI of the Neo4j server.'),
    )

    for name, help_ in options:

        parser.addoption(
            f'--{name}',
            action='store',
            default=None,
            help=help_,
        )


# core instance fixture
@pytest.fixture(name='core', scope='session')
def create_core(request, path):

    marker = request.node.get_closest_marker('inject_core_args')

    marker_args = {}
    # check if marker has attribute param
    if marker and hasattr(marker, 'param'):

        marker_args = marker.param

    if not marker_args and 'CORE' in globals():

        c = globals()['CORE']

    else:

        core_args = {'output_directory': path}
        core_args.update(marker_args)

        c = BioCypher(**core_args)

        if not marker_args:

            globals()['CORE'] = c

    yield c


# neo4j parameters
@pytest.fixture(scope='session')
def neo4j_param(request):

    keys = (
        'database_name',
        'user',
        'password',
        'uri',
    )

    param = bcy_config('neo4j')

    cli = {
        key: request.config.getoption(f'--{key}') or param[key]
        for key in keys
    }

    return cli


# neo4j driver fixture
@pytest.fixture(name='driver', scope='session')
def create_driver(request, neo4j_param, translator, hybrid_ontology):

    marker = request.node.get_closest_marker('inject_driver_args')

    marker_args = {}
    # check if marker has attribute param
    if marker and hasattr(marker, 'param'):

        marker_args = marker.param

    if not marker_args and 'DRIVER' in globals():

        d = globals()['DRIVER']

    else:

        driver_args = {
            'translator': translator,
            'ontology': hybrid_ontology,
        }
        driver_args.update(marker_args)
        driver_args.update(neo4j_param)

        d = _Driver(**driver_args)

        if not marker_args:

            globals()['DRIVER'] = d

    yield d

    # teardown
    d._driver.query('MATCH (n:Test)'
                    'DETACH DELETE n')
    d._driver.query('MATCH (n:Int1)'
                    'DETACH DELETE n')
    d._driver.query('MATCH (n:Int2)'
                    'DETACH DELETE n')

    # to deal with merging on non-existing nodes
    # see test_add_single_biocypher_edge_missing_nodes()
    d._driver.query("MATCH (n2) WHERE n2.id = 'src'"
                    'DETACH DELETE n2')
    d._driver.query("MATCH (n3) WHERE n3.id = 'tar'"
                    'DETACH DELETE n3')
    d._driver.close()


# skip test if neo4j is offline
@pytest.fixture(autouse=True)
def skip_if_offline(request):

    marker = request.node.get_closest_marker('requires_neo4j')

    if marker:

        driver = request.getfixturevalue('driver')

        if driver.status != 'db online':

            pytest.skip('Requires connection to Neo4j server.')
