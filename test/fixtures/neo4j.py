import os

import pytest

from neo4j.exceptions import ServiceUnavailable

from biocypher import config as bcy_config
from biocypher._logger import logger
from biocypher.output.connect._neo4j_driver import _Neo4jDriver
from biocypher.output.write.graph._neo4j import _Neo4jBatchWriter


@pytest.fixture(scope="function")
def bw(translator, deduplicator, tmp_path_session):
    bw = _Neo4jBatchWriter(
        translator=translator,
        deduplicator=deduplicator,
        output_directory=tmp_path_session,
        delimiter=";",
        array_delimiter="|",
        quote="'",
    )

    yield bw

    # teardown
    for f in os.listdir(tmp_path_session):
        os.remove(os.path.join(tmp_path_session, f))


@pytest.fixture(scope="function")
def bw_tab(translator, deduplicator, tmp_path_session):
    bw_tab = _Neo4jBatchWriter(
        translator=translator,
        deduplicator=deduplicator,
        output_directory=tmp_path_session,
        delimiter="\\t",
        array_delimiter="|",
        quote="'",
    )

    yield bw_tab

    # teardown
    for f in os.listdir(tmp_path_session):
        os.remove(os.path.join(tmp_path_session, f))


@pytest.fixture(scope="function")
def bw_strict(translator, deduplicator, tmp_path_session):
    bw = _Neo4jBatchWriter(
        translator=translator,
        deduplicator=deduplicator,
        output_directory=tmp_path_session,
        delimiter=";",
        array_delimiter="|",
        quote="'",
        strict_mode=True,
    )

    yield bw

    # teardown
    for f in os.listdir(tmp_path_session):
        os.remove(os.path.join(tmp_path_session, f))


@pytest.fixture(scope="session")
def neo4j_param(request):
    keys = (
        "database_name",
        "user",
        "password",
        "uri",
    )

    param = bcy_config("neo4j")

    cli = {key: request.config.getoption(f"--{key}") or param[key] for key in keys}

    # Add neo4j_enterprise flag if provided
    neo4j_enterprise = request.config.getoption("--neo4j_enterprise")
    if neo4j_enterprise:
        cli["neo4j_enterprise"] = neo4j_enterprise.lower() == "true"

    return cli


@pytest.fixture(autouse=True)
def skip_if_offline_neo4j(request, neo4j_param, translator):
    marker = request.node.get_closest_marker("requires_neo4j")

    if marker:
        try:
            marker_args = {}
            # check if marker has attribute param
            if marker and hasattr(marker, "param"):
                marker_args = marker.param

            driver_args = {
                "wipe": True,
                "multi_db": True,
                "translator": translator,
            }
            driver_args.update(marker_args)
            driver_args.update(neo4j_param)

            driver_args["database_name"] = "test"

            # Extract neo4j_enterprise flag if present and pass to driver
            neo4j_enterprise = driver_args.pop("neo4j_enterprise", False)
            if neo4j_enterprise:
                driver_args["force_enterprise"] = True

            _Neo4jDriver(**driver_args)

        except ServiceUnavailable as e:
            pytest.skip(f"Neo4j is offline: {e}")


@pytest.fixture(name="driver", scope="function")
def create_driver(request, neo4j_param, translator):
    marker = None  # request.node.get_closest_marker('inject_driver_args')

    marker_args = {}
    # check if marker has attribute param
    if marker and hasattr(marker, "param"):
        marker_args = marker.param

    # Always create a fresh driver for each test to avoid issues with closed drivers
    # The fixture is function-scoped, so each test gets its own driver instance
    driver_args = {
        "wipe": True,
        "multi_db": True,
        "translator": translator,
    }
    driver_args.update(marker_args)
    driver_args.update(neo4j_param)

    driver_args["database_name"] = "test"

    # Extract neo4j_enterprise flag if present and pass to driver
    neo4j_enterprise = driver_args.pop("neo4j_enterprise", False)
    if neo4j_enterprise:
        driver_args["force_enterprise"] = True

    d = _Neo4jDriver(**driver_args)

    yield d

    # teardown - only cleanup if driver is still available and not closed
    try:
        if d._driver.driver and not (hasattr(d._driver.driver, "_closed") and d._driver.driver._closed):
            d._driver.query("MATCH (n:Test)DETACH DELETE n")
            d._driver.query("MATCH (n:Int1)DETACH DELETE n")
            d._driver.query("MATCH (n:Int2)DETACH DELETE n")

            # to deal with merging on non-existing nodes
            # see test_add_single_biocypher_edge_missing_nodes()
            d._driver.query("MATCH (n2) WHERE n2.id = 'src'DETACH DELETE n2")
            d._driver.query("MATCH (n3) WHERE n3.id = 'tar'DETACH DELETE n3")
    except Exception as e:
        # Driver may already be closed or unavailable, log but don't fail
        logger.warning(f"Could not cleanup test data: {e}")
    finally:
        # Always try to close the driver, but don't fail if it's already closed
        try:
            d._driver.close()
        except Exception:
            pass  # Driver may already be closed
