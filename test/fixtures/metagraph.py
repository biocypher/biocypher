import os

import pytest

from biocypher.output.write.graph._metagraph import _MetaGraphWriter


@pytest.fixture(scope="function")
def bw_metagraph(translator, deduplicator, tmp_path_session):
    bw_metagraph = _MetaGraphWriter(
        translator=translator,
        deduplicator=deduplicator,
        use_IRI = False,
        output_directory=tmp_path_session,
        delimiter=",",
        file_format="cytoscape.json",
        file_stem="biocypher",
    )

    yield bw_metagraph

    # teardown
    for f in os.listdir(tmp_path_session):
        os.remove(os.path.join(tmp_path_session, f))

