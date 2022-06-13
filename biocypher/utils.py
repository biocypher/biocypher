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
Miscellaneous, generic purpose methods used across the module.
"""

from .logger import logger
logger.debug(f"Loading module {__name__}.")

from typing import Optional


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def pretty(d, lines: Optional[list]=None, indent: int=0) -> list:
    """
    Takes Neo4j profile dictionary and an optional header as
    list and creates a list of output strings to be printed.
    """

    lines = lines or []

    # if more items, branch
    if d:
        if isinstance(d, list):
            for sd in d:
                pretty(sd, lines, indent)
        elif isinstance(d, dict):
            typ = d.pop("operatorType", None)
            if typ:
                lines.append(
                    ("\t" * (indent))
                    + "|"
                    + "\t"
                    + f"{bcolors.OKBLUE}Step: {typ} {bcolors.ENDC}"
                )

            # buffer children
            chi = d.pop("children", None)

            for key, value in d.items():

                if key == "args":

                    pretty(value, lines, indent)

                # both are there for some reason, sometimes
                # both in the same process
                elif key == "Time" or key == "time":

                    lines.append(
                        ("\t" * (indent))
                        + "|"
                        + "\t"
                        + str(key)
                        + ": "
                        + f"{bcolors.WARNING}{value:,}{bcolors.ENDC}".replace(
                            ",", " "
                        )
                    )

                else:

                    lines.append(
                        ("\t" * (indent))
                        + "|"
                        + "\t"
                        + str(key)
                        + ": "
                        + str(value)
                    )

            # now the children
            pretty(chi, lines, indent + 1)

    return lines
