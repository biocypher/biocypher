import os

import pytest

from biocypher.output.write.graph._owl import _OWLWriter


@pytest.fixture(scope="function")
def bw_owl(translator, deduplicator, tmp_path_session):
    bw_owl = _OWLWriter(
        translator=translator,
        deduplicator=deduplicator,
        output_directory=tmp_path_session,
        delimiter=",",
        file_format="turtle",
        file_stem="biocypher",
    )

    yield bw_owl

    # teardown
    for f in os.listdir(tmp_path_session):
        os.remove(os.path.join(tmp_path_session, f))


@pytest.fixture(scope="function")
def bw_owl_ttl(translator, deduplicator, tmp_path_session):
    """Fixture for OWL writer with ttl format."""
    bw_owl_ttl = _OWLWriter(
        translator=translator,
        deduplicator=deduplicator,
        output_directory=tmp_path_session,
        delimiter=",",
        file_format="ttl",  # Using ttl format directly instead of turtle
        file_stem="biocypher",
    )
    yield bw_owl_ttl

    # teardown
    for f in os.listdir(tmp_path_session):
        os.remove(os.path.join(tmp_path_session, f))
