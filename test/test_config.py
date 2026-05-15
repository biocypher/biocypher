import pytest

import biocypher._config as cfg_module

from biocypher._config import _read_yaml, _USER_CONFIG_FILE


def test_read_yaml():
    schema_config = _read_yaml("biocypher/_config/test_schema_config.yaml")

    assert "protein" in schema_config


def test_for_special_characters():
    with pytest.warns(UserWarning):
        _read_yaml("biocypher/_config/test_config.yaml")


def test_read_config_merges_user_and_local(monkeypatch):
    """User-level and local config settings for the same top-level key should both be applied.

    Previously, if a key existed in the local config, the user-level settings
    for that same key were silently dropped. This test verifies all three config
    levels are merged: defaults <- user <- local.
    """
    from biocypher._config import read_config

    user_config = {"neo4j": {"uri": "neo4j://myserver:7687"}}
    local_config = {"neo4j": {"database_name": "my_project_db"}}

    _orig = cfg_module._read_yaml

    def patched(path):
        if path == _USER_CONFIG_FILE:
            return user_config
        if path in ("biocypher_config.yaml", "config/biocypher_config.yaml"):
            return local_config
        return _orig(path)

    monkeypatch.setattr(cfg_module, "_read_yaml", patched)

    result = read_config()

    assert result["neo4j"]["uri"] == "neo4j://myserver:7687"   # from user
    assert result["neo4j"]["database_name"] == "my_project_db"  # from local
    assert result["neo4j"]["password"] == "neo4j"               # from defaults
