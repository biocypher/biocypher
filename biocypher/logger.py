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
from datetime import datetime


def get_logger(name):
    """
    Main function of providing a logger instance to any module. Should
    be called from each module separately, e.g., after imports, assign
    ``logger = get_logger(__name__)`` to yield a module-specific logger
    that can be used according to Python :py:mod:`logging`.

    The file handler creates a log file named after the current date and
    time. Levels to output to file and console can be set here.

    Args:
        name (str): name of the logger instance

    Returns:
        logging.getLogger: an instance of the Python :py:mod:`Logger`.
    """
    file_formatter = logging.Formatter(
        "%(asctime)s\t%(levelname)s\tmodule:%(module)s\n%(message)s"
    )
    stdout_formatter = logging.Formatter("%(levelname)s -- %(message)s")

    now = datetime.now()
    date_time = now.strftime("%Y%m%d%H%M%S")
    ROOT = os.path.join(
        *os.path.split(os.path.abspath(os.path.dirname(__file__)))
    )
    logfile = ROOT + "/../log/" + date_time + ".log"
    if not os.path.isfile(logfile):
        print(f"Starting BioCypher logger at log/{date_time}.log")

    file_handler = logging.FileHandler(logfile)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.WARN)
    stdout_handler.setFormatter(stdout_formatter)

    logger = logging.getLogger(name)
    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)
    logger.setLevel(logging.DEBUG)

    return logger
