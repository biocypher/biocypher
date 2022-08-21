
from typing import Any, Generator, Mapping

SIMPLE_TYPES = (bytes, str, int, float)
LIST_LIKE = (list, set, tuple, Generator, Mapping)


def to_list(value: Any) -> list:
    """
    Ensures that ``value`` is a list.
    """

    if isinstance(value, LIST_LIKE):

        value = list(value)

    else:

        value = [value]

    return value
