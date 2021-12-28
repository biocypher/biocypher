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

    logger.warn(f"Starting BioCypher logger at log/{date_time}.log")

    return logger
