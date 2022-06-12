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
Package metadata (version, authors, etc).
"""

__all__ = ["get_metadata", "metadata", "__version__", "__author__"]

import os
import pathlib
import importlib
import toml


def get_metadata():
    """
    Basic package metadata.

    Retrieves package metadata from the current project directory or from
    the installed package.
    """

    here = pathlib.Path(__file__).parent
    pyproj_toml = "pyproject.toml"
    meta = {}

    for project_dir in (here, here.parent):

        toml_path = str(project_dir.joinpath(pyproj_toml).absolute())

        if os.path.exists(toml_path):

            pyproject = toml.load(toml_path)

            meta = {
                "name": pyproject["tool"]["poetry"]["name"],
                "version": pyproject["tool"]["poetry"]["version"],
                "author": pyproject["tool"]["poetry"]["authors"],
                "license": pyproject["tool"]["poetry"]["license"],
                "full_metadata": pyproject,
            }

            break

    if not meta:

        installed_meta = importlib.metadata.metadata(here.name).split("\n")

        meta = dict(
            (
                key.strip().lower(),
                val.strip(),
            )
            for key, val in
            (
                item.split(":")
                for item in installed_meta
            )
        )

    return meta


metadata = get_metadata()
__version__ = metadata.get("version", None)
__author__ = metadata.get("author", None)
__license__ = metadata.get("license", None)
