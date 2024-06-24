#!/usr/bin/env python

#
# Copyright 2021, Heidelberg University Clinic
#
# File author(s): Sebastian Lobentanzer
#                 Nils Krehl
# Distributed under MIT licence, see the file `LICENSE`.
#
"""
BioCypher 'in_memory' module. Handles the in-memory Knowledge Graph instance.
"""
from biocypher._logger import logger
from biocypher._translate import Translator
from biocypher._deduplicate import Deduplicator
from biocypher.output.in_memory._pandas import PandasKG
from biocypher.output.in_memory._networkx import NetworkxKG

logger.debug(f"Loading module {__name__}.")

__all__ = ["get_in_memory_kg"]

IN_MEMORY_DBMS = ["csv", "networkx"]


def get_in_memory_kg(
    dbms: str,
    translator: Translator,
    deduplicator: Deduplicator,
):
    """
    Function to return the in-memory KG class.

    Returns:
        class: the in-memory KG class
    """
    if dbms == "csv":
        return PandasKG(translator, deduplicator)
    elif dbms == "networkx":
        return NetworkxKG(translator, deduplicator)
    else:
        raise NotImplementedError(
            f"Getting the in memory BioCypher KG is not supported for the DBMS {dbms}. Supported: {IN_MEMORY_DBMS}."
        )
