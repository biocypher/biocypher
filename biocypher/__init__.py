#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright 2021, Heidelberg University Clinic
#
# File author(s): Sebastian Lobentanzer
#                 ...
#
# Distributed under GPLv3 license, see the file `LICENSE`.
#

"""
Graph database standard for molecular biology
"""

__all__ = [
    '__version__',
    '__author__',
    'module_data',
    'config',
    'logfile',
    'log',
    'Driver',
]

from ._metadata import __version__, __author__
from ._config import module_data, config
from ._logger import logfile, log
from ._driver import Driver
