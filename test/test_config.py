import pytest

import biocypher._config as cfg_module

from biocypher._config import _read_yaml, _USER_CONFIG_FILE, _warn_unknown_keys, config, config as _config, reset


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

    assert result["neo4j"]["uri"] == "neo4j://myserver:7687"  # from user
    assert result["neo4j"]["database_name"] == "my_project_db"  # from local
    assert result["neo4j"]["password"] == "neo4j"  # from defaults


def test_config_setter_merges_dict_for_known_key():
    """config(key=dict) merges into the existing dict for a known key."""
    try:
        config(neo4j={"database_name": "customdb"})
        result = config("neo4j")
        assert result["database_name"] == "customdb"
        assert "uri" in result  # other defaults preserved
    finally:
        reset()


def test_config_setter_creates_new_key():
    """config(key=value) must not raise KeyError for a key absent from defaults."""
    try:
        config(custom_unknown_dbms={"database_name": "mydb"})
        result = config("custom_unknown_dbms")
        assert result == {"database_name": "mydb"}
    finally:
        reset()


def test_config_setter_accepts_none_value():
    """config(key=None) sets the value to None without raising AttributeError."""
    try:
        config(neo4j=None)
        assert config("neo4j") is None
    finally:
        reset()


def test_update_from_file_with_unknown_key(tmp_path):
    """update_from_file must not crash when the YAML contains a key not in the defaults."""
    from biocypher._config import update_from_file

    cfg_file = tmp_path / "biocypher_config.yaml"
    cfg_file.write_text("custom_unknown_dbms:\n  database_name: mydb\n")
    try:
        update_from_file(str(cfg_file))
        assert config("custom_unknown_dbms") == {"database_name": "mydb"}
    finally:
        reset()


def test_arangodb_config_present_in_defaults():
    """ArangoDB section must exist in defaults so get_writer("arangodb") doesn't crash.

    Previously, the `arangodb` key was absent from biocypher_config.yaml, so
    _config("arangodb") returned None, get_writer passed labels_order=None to the
    writer, and _check_labels_order() raised a ValueError on first use.
    """
    from biocypher._config import reset

    reset()  # ensure we're reading from the real defaults file

    arango_cfg = _config("arangodb")

    assert arango_cfg is not None, "arangodb section missing from defaults config"
    assert "labels_order" in arango_cfg, "labels_order must be set so get_writer doesn't pass None"
    assert "delimiter" in arango_cfg, "delimiter must be set for ArangoDB CSV output"


def test_sqlite_config_has_labels_order():
    """SQLite section must have labels_order keys so get_writer("sqlite") doesn't crash.

    Previously, the `sqlite` section in biocypher_config.yaml was missing
    `labels_order`, `node_labels_order`, and `edge_labels_order`. Because
    get_writer passes these keys from config to _BatchWriter.__init__, the
    missing keys caused None to be forwarded, overriding the parameter defaults.
    _check_labels_order() then raised a ValueError on first use, making the
    SQLite writer completely unusable via BioCypher(dbms="sqlite").
    """
    from biocypher._config import reset

    reset()  # ensure we're reading from the real defaults file

    sqlite_cfg = _config("sqlite")

    assert sqlite_cfg is not None, "sqlite section missing from defaults config"
    assert "labels_order" in sqlite_cfg, "labels_order must be set so get_writer doesn't pass None"
    assert "node_labels_order" in sqlite_cfg, "node_labels_order must be set so get_writer doesn't pass None"
    assert "edge_labels_order" in sqlite_cfg, "edge_labels_order must be set so get_writer doesn't pass None"
    assert "delimiter" in sqlite_cfg, "delimiter must be set for SQLite CSV output"


def test_warn_unknown_keys_emits_warning():
    valid = {"biocypher": {}, "neo4j": {}}
    config_with_typo = {"biocypher": {}, "postgreql": {}}

    with pytest.warns(UserWarning, match="postgreql"):
        _warn_unknown_keys(config_with_typo, valid, "test config")


def test_warn_unknown_keys_no_warning_for_valid_keys():
    import warnings

    valid = {"biocypher": {}, "neo4j": {}, "postgresql": {}}
    config_valid = {"biocypher": {}, "neo4j": {}}

    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        _warn_unknown_keys(config_valid, valid, "test config")  # must not raise
