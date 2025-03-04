import os

import pytest

from biocypher.output.write.graph._rdf import _RDFWriter


@pytest.fixture(scope="function")
def bw_rdf(translator, deduplicator, tmp_path_session):
    bw_rdf = _RDFWriter(
        translator=translator,
        deduplicator=deduplicator,
        output_directory=tmp_path_session,
        file_format="xml",
        rdf_namespaces={},
        delimiter=",",
    )
    yield bw_rdf

    # teardown
    for f in os.listdir(tmp_path_session):
        os.remove(os.path.join(tmp_path_session, f))
