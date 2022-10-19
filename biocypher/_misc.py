from typing import Any, Mapping, KeysView, Generator, ItemsView, ValuesView
from collections.abc import Iterable

from neo4j_utils._misc import if_none  # noqa: F401

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

    return value if isinstance(value, LIST_LIKE) else (value,)


def prettyfloat(n: float) -> str:
    """
    Floats as strings of two value digits, for printing.
    """

    return '%.02g' % n if isinstance(n, float) else str(n)


def dict_str(dct: dict, sep: str = ', ') -> str:
    """
    Compact string representation of a dict.
    """

    if not isinstance(dct, dict):

        return str(dct)

    return sep.join(
        f'{key}={prettyfloat(dct[key])}'
        for key in sorted(dct.key())
    )
