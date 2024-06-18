import pytest

from biocypher.output.write.graph._networkx import _NetworkXWriter


@pytest.fixture(scope="function")
def bw_networkx(translator, deduplicator, tmp_path_session):
    bw_networkx = _NetworkXWriter(
        translator=translator,
        deduplicator=deduplicator,
        output_directory=tmp_path_session,
    )

    yield bw_networkx
