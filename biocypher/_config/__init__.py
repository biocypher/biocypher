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
Module data directory, including:

* The BioLink database schema
* The default config files
"""

from typing import Any, Optional
import os

import yaml
import appdirs

__all__ = ['module_data', 'module_data_path', 'read_config', 'config', 'reset']


def module_data_path(name: str) -> str:
    """
    Absolute path to a YAML file shipped with the module.
    """

    here = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(here, f'{name}.yaml')


def module_data(name: str) -> Any:
    """
    Retrieve the contents of a YAML file shipped with this module.
    """

    path = module_data_path(name)

    return _read_yaml(path)


def _read_yaml(path: str) -> Optional[dict]:

    if os.path.exists(path):

        with open(path, 'r') as fp:

            return yaml.load(fp.read(), Loader=yaml.FullLoader)


def read_config() -> dict:
    """
    Read the module config.

    Read and merge the built-in default, the user level and directory level
    configuration.
    """

    defaults = module_data('module_config')
    local = _read_yaml('biocypher.yaml') or {}
    user_confdir = appdirs.user_config_dir('biocypher', 'saezlab')
    user = _read_yaml(os.path.join(user_confdir, 'conf.yaml')) or {}

    defaults.update(local)
    defaults.update(user)

    return defaults


def config(*args, **kwargs) -> Optional[Any]:
    """
    Set or get module config parameters.
    """

    if args and kwargs:

        raise ValueError(
            'Setting and getting values in the same call is not allowed.'
        )

    if args:

        result = tuple(
            globals()['_config'].get(key, None)
            for key in args
        )

        return result[0] if len(result) == 1 else result

    globals()['_config'].update(kwargs)


def reset():
    """
    Reload configuration from the config files.
    """

    globals()['_config'] = read_config()


reset()
