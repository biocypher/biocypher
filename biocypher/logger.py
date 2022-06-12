#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles logging for the BioCypher the BioCypher python 
package, homepage: TODO.

Copyright 2021, Heidelberg University Clinic

File author(s): Sebastian Lobentanzer
                ...

Distributed under GPLv3 license, see LICENSE.txt.

Todo:

"""


import logging
import os
import yaml
from datetime import datetime

from biocypher import config


def get_logger(name):
    """
    Method providing central logger instance to main module. Is called
    only from main submodule, :mod:`biocypher.driver`. In child modules,
    the standard Python logging facility is called
    (using ``logging.getLogger(__name__)``), automatically inheriting
    the handlers from the central logger.

    The file handler creates a log file named after the current date and
    time. Levels to output to file and console can be set here.

    Args:
        name (str): name of the logger instance

    Returns:
        logging.getLogger: an instance of the Python :py:mod:`Logger`.

    Todo:
        - call from central __init__.py?
    """
    file_formatter = logging.Formatter(
        "%(asctime)s\t%(levelname)s\tmodule:%(module)s\n%(message)s"
    )
    stdout_formatter = logging.Formatter("%(levelname)s -- %(message)s")

    ROOT = os.path.join(
        *os.path.split(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        )
    )
    now = datetime.now()
    date_time = now.strftime("%Y%m%d-%H%M%S")
    # go two dirs back to project root
    logdir = 'biocypher-log'
    os.makedirs(logdir, exist_ok = True)
    logfile = os.path.join(logdir, f"biocypher-{date_time}.log")
    if not os.path.isfile(logfile):
        version = 0  # TODO
        print(
            f"This is BioCypher v{version}.\n"
            f"Starting BioCypher logger at `{logfile}`."
        )

    conf = config.module_data('module_config')

    file_handler = logging.FileHandler(logfile)
    if conf["debug"]:
        file_handler.setLevel(logging.DEBUG)
    else:
        file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)

    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.WARN)
    stdout_handler.setFormatter(stdout_formatter)

    logger = logging.getLogger(name)
    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)
    logger.setLevel(logging.DEBUG)

    return logger
