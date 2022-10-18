from typing import Any, Mapping, KeysView, Generator, ItemsView, ValuesView
from collections.abc import Iterable

__all__ = ['LIST_LIKE', 'SIMPLE_TYPES', 'ensure_iterable', 'if_none', 'to_list']

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


def if_none(value: Any, fallback: Any) -> Any:
    """
    Use ``value`` unless it's ``None``, then use ``fallback`` instead.
    """

    return fallback if value is None else value
