#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module is part of the BioCypher python package, homepage: TODO.


Copyright 2021, Heidelberg University Clinic

File author(s): Sebastian Lobentanzer
                ...

Distributed under GPLv3 license, see LICENSE.txt.

Todo:
"""

__version__ = '2021.0'

from distutils.core import setup

setup(
    name='biocypher',
    version=__version__,
    py_modules=[
	'biocypher.check', 
	'biocypher.create',
	'biocypher.driver',
	'biocypher.translate'
	],
    )
