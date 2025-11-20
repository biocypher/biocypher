import pytest

from biocypher.output.write.graph._biopathnet import _BioPathNetWriter


@pytest.fixture(scope="function")
def bw_biopathnet(translator, deduplicator, tmp_path_session):
    bw_biopathnet = _BioPathNetWriter(
        translator=translator,
        deduplicator=deduplicator,
        output_directory=tmp_path_session,
        file_format="txt",
        entity_types_file_stem="entity_types",
        background_graph_file_stem="train1",
        learning_graph_file_stem="train2",

    )

    yield bw_biopathnet
