import os
import random
import string
import tempfile
import subprocess

import pytest

from biocypher import config as bcy_config
from biocypher._core import BioCypher
from biocypher._write import _Neo4jBatchWriter, _PostgreSQLBatchWriter
from biocypher._create import BioCypherEdge, BioCypherNode
from biocypher._connect import _Neo4jDriver
from biocypher._mapping import OntologyMapping
from biocypher._ontology import Ontology, OntologyAdapter
from biocypher._translate import Translator


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


@pytest.fixture(name='path_strict', scope='module')
def path_strict():
    path = os.path.join(
        tempfile.gettempdir(),
        f'biocypher-test-{get_random_string(5)}',
    )
    os.makedirs(path, exist_ok=True)
    return path


# biocypher node generator
@pytest.fixture(scope='module')
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


# biocypher edge generator
@pytest.fixture(scope='module')
def _get_edges(l):
    edges = []
    for i in range(l):
        e1 = BioCypherEdge(
            source_id=f'p{i}',
            target_id=f'p{i + 1}',
            relationship_label='PERTURBED_IN_DISEASE',
            properties={
                'residue': 'T253',
                'level': 4,
            },
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e1)
        e2 = BioCypherEdge(
            source_id=f'm{i}',
            target_id=f'p{i + 1}',
            relationship_label='Is_Mutated_In',
            properties={
                'site': '3-UTR',
                'confidence': 1,
            },
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e2)
    return edges


@pytest.fixture(scope='module')
def ontology_mapping():
    return OntologyMapping(
        config_file='biocypher/_config/test_schema_config.yaml'
    )


@pytest.fixture(scope='module')
def translator(ontology_mapping):
    return Translator(ontology_mapping)


@pytest.fixture(scope='module')
def biolink_adapter():
    return OntologyAdapter(
        'https://github.com/biolink/biolink-model/raw/master/biolink-model.owl.ttl',
        'entity'
    )


@pytest.fixture(scope='module')
def so_adapter():
    return OntologyAdapter('test/so.owl', 'sequence_variant')


@pytest.fixture(scope='module')
def go_adapter():
    return OntologyAdapter('test/go.owl', 'molecular_function')


@pytest.fixture(scope='module')
def mondo_adapter():
    return OntologyAdapter('test/mondo.owl', 'disease')


@pytest.fixture(scope='module')
def hybrid_ontology(ontology_mapping):
    return Ontology(
        head_ontology={
            'url':
                'https://github.com/biolink/biolink-model/raw/master/biolink-model.owl.ttl',
            'root_node':
                'entity',
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


# neo4j batch writer fixtures
@pytest.fixture(scope='function')
def bw(hybrid_ontology, translator, path):

    bw = _Neo4jBatchWriter(
        ontology=hybrid_ontology,
        translator=translator,
        output_directory=path,
        delimiter=';',
        array_delimiter='|',
        quote="'",
    )

    yield bw

    # teardown
    for f in os.listdir(path):
        os.remove(os.path.join(path, f))
    os.rmdir(path)


# neo4j batch writer fixtures
@pytest.fixture(scope='function')
def bw_tab(hybrid_ontology, translator, path):

    bw_tab = _Neo4jBatchWriter(
        ontology=hybrid_ontology,
        translator=translator,
        output_directory=path,
        delimiter='\\t',
        array_delimiter='|',
        quote="'",
    )

    yield bw_tab

    # teardown
    for f in os.listdir(path):
        os.remove(os.path.join(path, f))
    os.rmdir(path)


@pytest.fixture(scope='function')
def bw_strict(hybrid_ontology, translator, path_strict):

    bw = _Neo4jBatchWriter(
        ontology=hybrid_ontology,
        translator=translator,
        output_directory=path_strict,
        delimiter=';',
        array_delimiter='|',
        quote="'",
        strict_mode=True,
    )

    yield bw

    # teardown
    for f in os.listdir(path_strict):
        os.remove(os.path.join(path_strict, f))
    os.rmdir(path_strict)


# core instance fixture
@pytest.fixture(name='core', scope='module')
def create_core(request, path):

    marker = request.node.get_closest_marker('inject_core_args')

    marker_args = {}
    # check if marker has attribute param
    if marker and hasattr(marker, 'param'):

        marker_args = marker.param

    if not marker_args and 'CORE' in globals():

        c = globals()['CORE']

    else:

        core_args = {
            'schema_config_path': 'biocypher/_config/test_schema_config.yaml',
            'output_directory': path,
        }
        core_args.update(marker_args)

        c = BioCypher(**core_args)

        if not marker_args:

            globals()['CORE'] = c

    yield c


# neo4j parameters
@pytest.fixture(scope='module')
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
@pytest.fixture(name='driver', scope='module')
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
            'wipe': True,
            'multi_db': True,
            'translator': translator,
            'ontology': hybrid_ontology,
        }
        driver_args.update(marker_args)
        driver_args.update(neo4j_param)

        driver_args['database_name'] = 'test'

        d = _Neo4jDriver(**driver_args)

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


### postgresql ###
def params_postgresql(bcy_config):
    params = bcy_config('postgresql')
    return {
        'db_name': 'postgresql-biocypher-test-TG2C7GsdNw',
        'db_password': params['password'],
        'db_user': params['user'],
        'db_port': params['port'],
        'import_call_bin_prefix': params['import_call_bin_prefix']
    }


@pytest.fixture(scope='function')
def bw_comma_postgresql(hybrid_ontology, translator, path):
    params = params_postgresql(bcy_config)

    bw_comma = _PostgreSQLBatchWriter(
        ontology=hybrid_ontology,
        translator=translator,
        output_directory=path,
        delimiter=',',
        **params
    )

    yield bw_comma

    # teardown
    for f in os.listdir(path):
        os.remove(os.path.join(path, f))
    os.rmdir(path)


@pytest.fixture(scope='function')
def bw_tab_postgresql(hybrid_ontology, translator, path):
    params = params_postgresql(bcy_config)

    bw_tab = _PostgreSQLBatchWriter(
        ontology=hybrid_ontology,
        translator=translator,
        output_directory=path,
        delimiter='\\t',
        **params
    )

    yield bw_tab

    # teardown
    for f in os.listdir(path):
        os.remove(os.path.join(path, f))
    os.rmdir(path)


@pytest.fixture
def create_database_postgres(path):
    params = params_postgresql(bcy_config)
    dbname, user, port, password = params['db_name'], params['db_user'], params['db_port'], params['db_password']

    # create the database
    command = f'PGPASSWORD={password} psql -c \'CREATE DATABASE "{dbname}";\' --port {port} --user {user}'
    process = subprocess.run(command, shell=True)

    yield dbname, user, port, password, process.returncode == 0 # 0 if success
    
    # teardown
    command = f'PGPASSWORD={password} psql -c \'DROP DATABASE "{dbname}";\' --port {port} --user {user}'
    process = subprocess.run(command, shell=True)
