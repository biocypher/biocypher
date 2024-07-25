import os

import pytest

from biocypher.output.write.graph._arangodb import _ArangoDBBatchWriter


@pytest.fixture(scope="function")
def bw_arango(translator, deduplicator, tmp_path_session):
    bw_arango = _ArangoDBBatchWriter(
        translator=translator,
        deduplicator=deduplicator,
        output_directory=tmp_path_session,
        delimiter=",",
    )

    yield bw_arango

    # teardown
    for f in os.listdir(tmp_path_session):
        os.remove(os.path.join(tmp_path_session, f))
