import os
import random
import string
import tempfile

import pytest

from biocypher import config as bcy_config
from biocypher._core import BioCypher
from biocypher._driver import Driver


def get_random_string(length):

    # choose from all lowercase letter
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


# temporary output paths
@pytest.fixture(name='path', scope='session')
def path():
    path = os.path.join(
        tempfile.gettempdir(),
        f'biocypher-test-{get_random_string(5)}',
    )
    os.makedirs(path, exist_ok=True)
    return path


__all__ = [
    'create_driver', 'neo4j_param', 'pytest_addoption', 'skip_if_offline'
]


def pytest_addoption(parser):

    options = (
        ('db', 'The Neo4j database to be used for tests.'),
        ('user', 'Tests access Neo4j as this user.'),
        ('pw', 'Password to access Neo4j.'),
        ('uri', 'URI of the Neo4j server.'),
    )

    for name, help_ in options:

        parser.addoption(
            f'--{name}',
            action='store',
            default=None,
            help=help_,
        )


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


@pytest.fixture(scope='session')
def neo4j_param(request):

    keys = (
        'db',
        'user',
        'pw',
        'uri',
    )

    param = {
        key: request.config.getoption(f'--{key}') or bcy_config(key)
        for key in keys
    }

    return bcy_config('neo4j')


@pytest.fixture(name='driver', scope='session')
def create_driver(request, neo4j_param):

    marker = request.node.get_closest_marker('inject_driver_args')

    marker_args = {}
    # check if marker has attribute param
    if marker and hasattr(marker, 'param'):

        marker_args = marker.param

    if not marker_args and 'DRIVER' in globals():

        d = globals()['DRIVER']

    else:

        driver_args = {
            'wipe':
                True,
            'increment_version':
                False,
            'user_schema_config_path':
                'biocypher/_config/test_schema_config.yaml',
            'clear_cache':
                True,
        }
        driver_args.update(marker_args)
        driver_args.update(neo4j_param)

        d = Driver(**driver_args)

        if not marker_args:

            globals()['DRIVER'] = d

    yield d

    # teardown
    d.query('MATCH (n:Test)'
            'DETACH DELETE n')
    d.query('MATCH (n:Int1)'
            'DETACH DELETE n')
    d.query('MATCH (n:Int2)'
            'DETACH DELETE n')

    # to deal with merging on non-existing nodes
    # see test_add_single_biocypher_edge_missing_nodes()
    d.query("MATCH (n2) WHERE n2.id = 'src'"
            'DETACH DELETE n2')
    d.query("MATCH (n3) WHERE n3.id = 'tar'"
            'DETACH DELETE n3')
    d.close()


@pytest.fixture(autouse=True)
def skip_if_offline(request):

    marker = request.node.get_closest_marker('requires_neo4j')

    if marker:

        driver = request.getfixturevalue('driver')

        if driver.status != 'db online':

            pytest.skip('Requires connection to Neo4j server.')
