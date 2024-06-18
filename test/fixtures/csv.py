import pytest

from biocypher.output.write.relational._csv import _PandasCSVWriter


@pytest.fixture(scope="function")
def bw_comma_csv(translator, deduplicator, tmp_path_session):
    bw_comma = _PandasCSVWriter(
        translator=translator,
        deduplicator=deduplicator,
        output_directory=tmp_path_session,
        delimiter=",",
    )

    yield bw_comma
