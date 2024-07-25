import os

import pytest

from biocypher import BioCypher


@pytest.fixture(name="core", scope="function")
def create_core(request, tmp_path_session):
    marker = request.node.get_closest_marker("inject_core_args")

    marker_args = {}
    # check if marker has attribute param
    if marker and hasattr(marker, "param"):
        marker_args = marker.param

    else:
        core_args = {
            "schema_config_path": "biocypher/_config/test_schema_config.yaml",
            "output_directory": tmp_path_session,
        }
        core_args.update(marker_args)

        c = BioCypher(**core_args)

    yield c

    # teardown
    for f in os.listdir(tmp_path_session):
        os.remove(os.path.join(tmp_path_session, f))


@pytest.fixture(name="core_no_schema", scope="function")
def create_core_no_schema(request, tmp_path_session):
    marker = request.node.get_closest_marker("inject_core_args")

    marker_args = {}
    # check if marker has attribute param
    if marker and hasattr(marker, "param"):
        marker_args = marker.param

    else:
        core_args = {
            "schema_config_path": None,
            "output_directory": tmp_path_session,
        }
        core_args.update(marker_args)

        c = BioCypher(**core_args)

    yield c

    # teardown
    for f in os.listdir(tmp_path_session):
        os.remove(os.path.join(tmp_path_session, f))
