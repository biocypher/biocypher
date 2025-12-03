"""BioCypher 'connect' module.

Handles the connecting and writing a Knowledge Graph to a database.
"""

from biocypher._config import config as _config
from biocypher._logger import logger
from biocypher._translate import Translator

logger.debug(f"Loading module {__name__}.")

__all__ = ["get_connector"]


def get_connector(
    dbms: str,
    translator: Translator,
):
    """Return the connector class.

    Returns
    -------
        class: the connector class

    Raises
    ------
        NotImplementedError: if the DBMS is not supported
        ImportError: if Neo4j driver is not installed when using Neo4j

    """
    dbms_config = _config(dbms)

    if dbms == "neo4j":
        # Import Neo4j driver only when needed
        try:
            from biocypher.output.connect._neo4j_driver import _Neo4jDriver
        except ImportError as e:
            msg = (
                "Neo4j driver is not installed. Install it with: "
                "pip install biocypher[neo4j] or pip install neo4j>=5.0"
            )
            logger.error(msg)
            raise ImportError(msg) from e

        return _Neo4jDriver(
            database_name=dbms_config["database_name"],
            wipe=dbms_config["wipe"],
            uri=dbms_config["uri"],
            user=dbms_config["user"],
            password=dbms_config["password"],
            multi_db=dbms_config["multi_db"],
            translator=translator,
        )

    msg = f"Online mode is not supported for the DBMS {dbms}."
    logger.error(msg)
    raise NotImplementedError(msg)
