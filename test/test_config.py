import pytest

from biocypher._config import _read_yaml


def test_read_yaml():
    schema_config = _read_yaml("biocypher/_config/test_schema_config.yaml")

    assert "protein" in schema_config


def test_for_special_characters():
    with pytest.warns(UserWarning):
        _read_yaml("biocypher/_config/test_config.yaml")
