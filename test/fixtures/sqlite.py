import os

import pytest

from biocypher.output.write.relational._sqlite import _SQLiteBatchWriter


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
        remove_file(os.path.join(tmp_path_session, f))
    remove_file("test_sqlite.db")


def remove_file(file_path: str):
    try:
        os.remove(file_path)
    except PermissionError:
        # fix Windows error that once opened files can only be removed after a restart
        # https://groups.google.com/g/python-sqlite/c/2KBI2cR-t70
        os.rename(file_path, f"renamed_{file_path}")
        os.remove(f"renamed_{file_path}")
    except FileNotFoundError:
        # at the moment on windows the file is not created
        pass
