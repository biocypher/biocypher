"""BioCypher 'in_memory' module.

Handles the in-memory Knowledge Graph instance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from biocypher._logger import logger
from biocypher.output.in_memory._airr import AirrKG
from biocypher.output.in_memory._networkx import NetworkxKG
from biocypher.output.in_memory._pandas import PandasKG

if TYPE_CHECKING:
    from biocypher._deduplicate import Deduplicator
    from biocypher.output.in_memory._in_memory_kg import _InMemoryKG

logger.debug(f"Loading module {__name__}.")

__all__ = ["get_in_memory_kg"]

IN_MEMORY_DBMS = ["csv", "pandas", "tabular", "networkx", "airr"]


def get_in_memory_kg(
    dbms: str,
    deduplicator: Deduplicator,
) -> _InMemoryKG:
    """Return the in-memory KG class.

    Returns
    -------
        _InMemoryKG: the in-memory KG class

    """
    if dbms in ["csv", "pandas", "tabular"]:
        return PandasKG(deduplicator)
    if dbms == "networkx":
        return NetworkxKG(deduplicator)
    elif dbms == "airr":
        return AirrKG(deduplicator)
    else:
        msg = f"Getting the in memory BioCypher KG is not supported for the DBMS {dbms}. Supported: {IN_MEMORY_DBMS}."
        logger.error(msg)
        raise NotImplementedError(msg)
