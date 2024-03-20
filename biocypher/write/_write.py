#!/usr/bin/env python

#
# Copyright 2021, Heidelberg University Clinic
#
# File author(s): Sebastian Lobentanzer
#                 Michael Hartung
#
# Distributed under MIT licence, see the file `LICENSE`.
#
"""
BioCypher 'offline' module. Handles the writing of node and edge representations
suitable for import into a DBMS.
"""

from biocypher._logger import logger
from biocypher.write.graph._neo4j import _Neo4jBatchWriter
from biocypher.write.graph._arangodb import _ArangoDBBatchWriter
from biocypher.write.relational._sqlite import _SQLiteBatchWriter
from biocypher.write.relational._postgresql import _PostgreSQLBatchWriter

logger.debug(f"Loading module {__name__}.")

from typing import TYPE_CHECKING

from biocypher._config import config as _config

__all__ = ["get_writer"]

if TYPE_CHECKING:
    from biocypher._translate import Translator
    from biocypher._deduplicate import Deduplicator

DBMS_TO_CLASS = {
    "neo": _Neo4jBatchWriter,
    "neo4j": _Neo4jBatchWriter,
    "Neo4j": _Neo4jBatchWriter,
    "postgres": _PostgreSQLBatchWriter,
    "postgresql": _PostgreSQLBatchWriter,
    "PostgreSQL": _PostgreSQLBatchWriter,
    "arango": _ArangoDBBatchWriter,
    "arangodb": _ArangoDBBatchWriter,
    "ArangoDB": _ArangoDBBatchWriter,
    "sqlite": _SQLiteBatchWriter,
    "sqlite3": _SQLiteBatchWriter,
}


def get_writer(
    dbms: str,
    translator: "Translator",
    deduplicator: "Deduplicator",
    output_directory: str,
    strict_mode: bool,
):
    """
    Function to return the writer class based on the selection in the config
    file.

    Args:

        dbms: the database management system; for options, see DBMS_TO_CLASS.

        translator: the Translator object.

        output_directory: the directory to write the output files to.

        strict_mode: whether to use strict mode.

    Returns:

        instance: an instance of the selected writer class.

    """

    dbms_config = _config(dbms)

    writer = DBMS_TO_CLASS[dbms]

    if not writer:
        raise ValueError(f"Unknown dbms: {dbms}")

    if writer is not None:
        return writer(
            translator=translator,
            deduplicator=deduplicator,
            delimiter=dbms_config.get("delimiter"),
            array_delimiter=dbms_config.get("array_delimiter"),
            quote=dbms_config.get("quote_character"),
            output_directory=output_directory,
            db_name=dbms_config.get("database_name"),
            import_call_bin_prefix=dbms_config.get("import_call_bin_prefix"),
            import_call_file_prefix=dbms_config.get("import_call_file_prefix"),
            wipe=dbms_config.get("wipe"),
            strict_mode=strict_mode,
            skip_bad_relationships=dbms_config.get(
                "skip_bad_relationships"
            ),  # neo4j
            skip_duplicate_nodes=dbms_config.get(
                "skip_duplicate_nodes"
            ),  # neo4j
            db_user=dbms_config.get("user"),  # psql
            db_password=dbms_config.get("password"),  # psql
            db_port=dbms_config.get("port"),  # psql
        )
