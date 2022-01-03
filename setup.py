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

__version__ = "2021.0"

from setuptools import setup


def read_requirements():

    with open("requirements.txt", "r") as fp:

        requirements = [
            name.strip() for name in fp if name and not name.startswith("-")
        ]

    return requirements


setup(
    name="biocypher",
    version=__version__,
    py_modules=[
        "biocypher.check",
        "biocypher.create",
        "biocypher.driver",
        "biocypher.translate",
    ],
    install_requires=read_requirements(),
    include_package_data=True,
    data_files=[
        ("biocypher", ["config/schema_config.yaml"]),
        ("biocypher", ["config/module_config.yaml"]),
    ],
)
