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

from ._metadata import __version__, __author__
import biocypher._config as config
from .driver import Driver
from .logger import logfile, log
