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
    '__version__',
    '__author__',
    'module_data',
    'config',
    'logfile',
    'log',
    'Driver',
    'BioCypher',
]

from ._core import BioCypher
from ._config import config, module_data
from ._logger import log, logger, logfile
from ._metadata import __author__, __version__


class Driver(BioCypher):
    logger.warning(
        "The 'Driver' class is deprecated. Please use 'BioCypher' instead."
    )
    pass
