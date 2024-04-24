import os

import pytest

from biocypher.write.graph._rdf import _RDFWriter


@pytest.fixture(scope="function")
def bw_rdf(translator, deduplicator, tmp_path_session):
    bw_rdf = _RDFWriter(
        translator=translator,
        deduplicator=deduplicator,
        output_directory=tmp_path_session,
        delimiter=",",
    )
    bw_rdf.rdf_format = "xml"
    bw_rdf.namespaces = {}
    yield bw_rdf

    # teardown
    for f in os.listdir(tmp_path_session):
        os.remove(os.path.join(tmp_path_session, f))
