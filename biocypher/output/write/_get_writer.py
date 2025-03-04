"""Module to provide one of the available writer classes.

The writer classes are responsible for writing the node and edge representations
to disk in a format suitable for import into a DBMS.
"""

from typing import TYPE_CHECKING

from biocypher._config import config as _config
from biocypher._logger import logger
from biocypher.output.write._batch_writer import _BatchWriter
from biocypher.output.write.graph._arangodb import _ArangoDBBatchWriter
from biocypher.output.write.graph._neo4j import _Neo4jBatchWriter
from biocypher.output.write.graph._networkx import _NetworkXWriter
from biocypher.output.write.graph._owl import _OWLWriter
from biocypher.output.write.graph._rdf import _RDFWriter
from biocypher.output.write.relational._csv import _PandasCSVWriter
from biocypher.output.write.relational._postgresql import _PostgreSQLBatchWriter
from biocypher.output.write.relational._sqlite import _SQLiteBatchWriter

logger.debug(f"Loading module {__name__}.")

__all__ = ["get_writer", "DBMS_TO_CLASS"]

if TYPE_CHECKING:
    from biocypher._deduplicate import Deduplicator
    from biocypher._translate import Translator

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
    "rdf": _RDFWriter,
    "RDF": _RDFWriter,
    "owl": _OWLWriter,
    "OWL": _OWLWriter,
    "csv": _PandasCSVWriter,
    "CSV": _PandasCSVWriter,
    "pandas": _PandasCSVWriter,
    "Pandas": _PandasCSVWriter,
    "tabular": _PandasCSVWriter,
    "Tabular": _PandasCSVWriter,
    "networkx": _NetworkXWriter,
    "NetworkX": _NetworkXWriter,
}


def get_writer(
    dbms: str,
    translator: "Translator",
    deduplicator: "Deduplicator",
    output_directory: str,
    strict_mode: bool,
) -> _BatchWriter | None:
    """Return the writer class based on the selection in the config file.

    Args:
    ----
        dbms: the database management system; for options, see DBMS_TO_CLASS.
        translator: the Translator object.
        deduplicator: the Deduplicator object.
        output_directory: the directory to output.write the output files to.
        strict_mode: whether to use strict mode.

    Returns:
    -------
        instance: an instance of the selected writer class.

    """
    dbms_config = _config(dbms)

    writer = DBMS_TO_CLASS[dbms]

    if "rdf_format" in dbms_config:
        logger.warning("The 'rdf_format' config option is deprecated, use 'file_format' instead.")
        if "file_format" not in dbms_config:
            format = dbms_config["rdf_format"]
            logger.warning(f"I will set 'file_format: {format}' for you.")
            dbms_config["file_format"] = format
            dbms_config.pop("rdf_format")
        logger.warning("NOTE: this warning will become an error in next versions.")

    if not writer:
        msg = f"Unknown dbms: {dbms}"
        raise ValueError(msg)

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
            skip_bad_relationships=dbms_config.get("skip_bad_relationships"),  # neo4j
            skip_duplicate_nodes=dbms_config.get("skip_duplicate_nodes"),  # neo4j
            db_user=dbms_config.get("user"),  # psql
            db_password=dbms_config.get("password"),  # psql
            db_port=dbms_config.get("port"),  # psql
            file_format=dbms_config.get("file_format"),  # rdf, owl
            rdf_namespaces=dbms_config.get("rdf_namespaces"),  # rdf, owl
            edge_model=dbms_config.get("edge_model"),  # owl
        )
    return None
