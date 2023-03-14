#!/usr/bin/env python

#
# Copyright 2021, Heidelberg University Clinic
#
# File author(s): Sebastian Lobentanzer
#                 ...
#
# Distributed under MIT licence, see the file `LICENSE`.
#
"""
Handy functions for use in various places.
"""
from ._logger import logger

logger.debug(f'Loading module {__name__}.')

from typing import (
    Any,
    Union,
    Mapping,
    KeysView,
    Generator,
    ItemsView,
    ValuesView,
)
from collections.abc import Iterable
import re

from treelib import Tree
import networkx as nx
import stringcase

__all__ = ['LIST_LIKE', 'SIMPLE_TYPES', 'ensure_iterable', 'to_list']

SIMPLE_TYPES = (
    bytes,
    str,
    int,
    float,
    bool,
    type(None),
)

LIST_LIKE = (
    list,
    set,
    tuple,
    Generator,
    ItemsView,
    KeysView,
    Mapping,
    ValuesView,
)


def to_list(value: Any) -> list:
    """
    Ensures that ``value`` is a list.
    """

    if isinstance(value, LIST_LIKE):

        value = list(value)

    else:

        value = [value]

    return value


def ensure_iterable(value: Any) -> Iterable:
    """
    Returns iterables, except strings, wraps simple types into tuple.
    """

    return value if isinstance(value, LIST_LIKE) else (value, )


def create_tree_visualisation(inheritance_tree: Union[dict, nx.Graph]) -> str:
    """
    Creates a visualisation of the inheritance tree using treelib.
    """

    if isinstance(inheritance_tree, nx.Graph):

        inheritance_tree = nx.to_dict_of_lists(inheritance_tree)
        # unlist values
        inheritance_tree = {k: v[0] for k, v in inheritance_tree.items() if v}

    # find root node
    classes = set(inheritance_tree.keys())
    parents = set(inheritance_tree.values())
    root = list(parents - classes)

    if len(root) > 1:

        if 'entity' in root:

            root = 'entity'  # default: good standard? TODO

        else:

            raise ValueError(
                'Inheritance tree cannot have more than one root node. '
                f'Found {len(root)}: {root}.'
            )

    else:

        root = root[0]

    if not root:
        # find key whose value is None
        root = list(inheritance_tree.keys())[list(inheritance_tree.values()
                                                 ).index(None)]

    tree = Tree()

    tree.create_node(root, root)

    while classes:

        for child in classes:

            parent = inheritance_tree[child]

            if parent in tree.nodes.keys() or parent == root:

                tree.create_node(child, child, parent=parent)

        for node in tree.nodes.keys():

            if node in classes:

                classes.remove(node)

    return tree


# string conversion, adapted from Biolink Model Toolkit
lowercase_pattern = re.compile(r'[a-zA-Z]*[a-z][a-zA-Z]*')
underscore_pattern = re.compile(r'(?<!^)(?=[A-Z][a-z])')


def from_pascal(s: str, sep: str = ' ') -> str:
    underscored = underscore_pattern.sub(sep, s)
    lowercased = lowercase_pattern.sub(
        lambda match: match.group(0).lower(),
        underscored,
    )
    return lowercased


def pascalcase_to_sentencecase(s: str) -> str:
    """
    Convert PascalCase to sentence case.

    Args:
        s: Input string in PascalCase

    Returns:
        string in sentence case form
    """
    return from_pascal(s, sep=' ')


def snakecase_to_sentencecase(s: str) -> str:
    """
    Convert snake_case to sentence case.

    Args:
        s: Input string in snake_case

    Returns:
        string in sentence case form
    """
    return stringcase.sentencecase(s).lower()


def sentencecase_to_snakecase(s: str) -> str:
    """
    Convert sentence case to snake_case.

    Args:
        s: Input string in sentence case

    Returns:
        string in snake_case form
    """
    return stringcase.snakecase(s).lower()


def sentencecase_to_pascalcase(s: str) -> str:
    """
    Convert sentence case to PascalCase.

    Args:
        s: Input string in sentence case

    Returns:
        string in PascalCase form
    """
    return re.sub(r'(?:^| )([a-zA-Z])', lambda match: match.group(1).upper(), s)


def to_lower_sentence_case(s: str) -> str:
    """
    Convert any string to lower sentence case. Works with snake_case,
    PascalCase, and sentence case.

    Args:
        s: Input string

    Returns:
        string in lower sentence case form
    """
    if '_' in s:
        return snakecase_to_sentencecase(s)
    elif ' ' in s:
        return s.lower()
    elif s[0].isupper():
        return pascalcase_to_sentencecase(s)
    else:
        return s
