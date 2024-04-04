#!/usr/bin/env python

#
# Copyright 2021, Heidelberg University Clinic
#
# File author(s): Sebastian Lobentanzer
#                 ...
#
# Distributed under MIT licence, see the file `LICENSE`.
#
"""
BioCypher: a unifying framework for biomedical knowledge graphs.
"""

__all__ = [
    "__version__",
    "__author__",
    "module_data",
    "config",
    "logfile",
    "log",
    "Driver",
    "BioCypher",
    "Resource",
]

from ._get import Resource
from ._core import BioCypher
from ._config import config, module_data
from ._logger import log, logger, logfile
from ._metadata import __author__, __version__


class Driver(BioCypher):
    # initialise parent class but log a warning
    def __init__(self, *args, **kwargs):
        logger.warning(
            "The class `Driver` is deprecated and will be removed in a future "
            "release. Please use `BioCypher` instead."
        )
        super().__init__(*args, **kwargs)
