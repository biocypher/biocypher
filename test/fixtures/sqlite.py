import os

import pytest

from biocypher.write.relational._sqlite import _SQLiteBatchWriter


@pytest.fixture(scope="function")
def bw_tab_sqlite(translator, deduplicator, tmp_path_session):
    bw_tab = _SQLiteBatchWriter(
        db_name="test_sqlite.db",
        translator=translator,
        deduplicator=deduplicator,
        output_directory=tmp_path_session,
        delimiter="\\t",
    )

    yield bw_tab

    # teardown
    for f in os.listdir(tmp_path_session):
        try:
            os.remove(os.path.join(tmp_path_session, f))
        except PermissionError:
            # fix Windows error that once opened files can only be removed after a restart
            # https://groups.google.com/g/python-sqlite/c/2KBI2cR-t70
            os.rename(f, f"{f}_renamed")
            os.remove(f"{f}_renamed")
