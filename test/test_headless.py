"""Tests for headless BioCypher: skipping the head ontology load.

Covers the new path where ``head_ontology`` is unset (or explicitly null in
the YAML config) and the legacy class falls back to a :class:`NullOntology`
shim. Asserts:

* the rdflib graph parser is never called,
* :class:`OntologyMapping` is still built from ``schema_config.yaml``,
* the Translator and CSV write paths still operate on declared classes,
* writer-specific surfaces that genuinely need an OWL graph raise.
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from biocypher import BioCypher
from biocypher._config import read_config
from biocypher._mapping import OntologyMapping
from biocypher._ontology import NullOntology

# Absolute path so tests survive monkeypatch.chdir().
SCHEMA_CONFIG = str(
    Path(__file__).resolve().parent.parent / "biocypher" / "_config" / "test_schema_config.yaml"
)


@pytest.fixture
def headless_config(tmp_path, monkeypatch):
    """Write a tiny biocypher_config.yaml with `head_ontology: null` and cd in."""
    cfg = tmp_path / "biocypher_config.yaml"
    cfg.write_text(
        "biocypher:\n"
        "  dbms: csv\n"
        "  offline: true\n"
        "  strict_mode: false\n"
        "  head_ontology: null\n"
        "  output_directory: biocypher-out\n"
    )
    monkeypatch.chdir(tmp_path)
    return cfg


# ---------------------------------------------------------------------------
# NullOntology unit surface
# ---------------------------------------------------------------------------


def test_null_ontology_get_ancestors_returns_self_label():
    onto = NullOntology(ontology_mapping=OntologyMapping())
    assert onto.get_ancestors("protein") == ["protein"]


def test_null_ontology_exposes_mapping():
    mapping = OntologyMapping(config_file=SCHEMA_CONFIG)
    onto = NullOntology(ontology_mapping=mapping)
    assert onto.mapping is mapping
    # extended_schema must be populated from the YAML, not from rdflib.
    assert onto.mapping.extended_schema


def test_null_ontology_show_structure_raises():
    onto = NullOntology()
    with pytest.raises(NotImplementedError, match="headless mode"):
        onto.show_ontology_structure()


def test_null_ontology_get_rdf_graph_raises():
    onto = NullOntology()
    with pytest.raises(NotImplementedError, match="headless mode"):
        onto.get_rdf_graph()


def test_null_ontology_get_dict_shape():
    onto = NullOntology()
    d = onto.get_dict()
    # Mirror Ontology.get_dict() exactly so the Neo4j connector contract holds.
    assert d["node_label"] == "BioCypher"
    assert "node_id" in d
    assert "schema" in d["properties"]


# ---------------------------------------------------------------------------
# Config merge: explicit null clears a default
# ---------------------------------------------------------------------------


def test_local_config_null_clears_default_head_ontology(tmp_path, monkeypatch):
    """`head_ontology: null` in a local config must clear the shipped default URL."""
    cfg = tmp_path / "biocypher_config.yaml"
    cfg.write_text("biocypher:\n  head_ontology: null\n")
    monkeypatch.chdir(tmp_path)

    merged = read_config()
    assert merged["biocypher"]["head_ontology"] is None


# ---------------------------------------------------------------------------
# BioCypher integration: headless mode actually avoids the network
# ---------------------------------------------------------------------------


def test_bc_headless_no_network_call(headless_config):
    """Instantiating BioCypher with `head_ontology: null` must not touch rdflib."""
    with patch("rdflib.Graph.parse") as parse_mock:
        bc = BioCypher(
            biocypher_config_path=str(headless_config),
            schema_config_path=SCHEMA_CONFIG,
        )
        # Force ontology resolution — this is what triggered the network fetch
        # in the legacy path. Under headless it must return a NullOntology.
        ontology = bc._get_ontology()
    assert isinstance(ontology, NullOntology)
    assert parse_mock.call_count == 0


def test_bc_headless_translator_uses_schema_config(headless_config):
    """Translator still resolves ontology types via schema_config under headless."""
    bc = BioCypher(
        biocypher_config_path=str(headless_config),
        schema_config_path=SCHEMA_CONFIG,
    )
    translator = bc._get_translator()
    # extended_schema must contain entries declared in the test schema_config.
    assert translator.ontology.mapping.extended_schema


def test_bc_headless_tail_without_head_raises(tmp_path, monkeypatch):
    """`tail_ontologies` without `head_ontology` is nonsensical and must fail loudly."""
    cfg = tmp_path / "biocypher_config.yaml"
    cfg.write_text(
        "biocypher:\n"
        "  dbms: csv\n"
        "  offline: true\n"
        "  strict_mode: false\n"
        "  head_ontology: null\n"
    )
    monkeypatch.chdir(tmp_path)

    bc = BioCypher(
        biocypher_config_path=str(cfg),
        schema_config_path=SCHEMA_CONFIG,
        tail_ontologies={"so": {"url": "x", "head_join_node": "h", "tail_join_node": "t"}},
    )
    with pytest.raises(ValueError, match="tail_ontologies"):
        bc._get_ontology()


def test_bc_headless_required_config_no_longer_demands_ontology(tmp_path, monkeypatch):
    """`head_ontology` is no longer in REQUIRED_CONFIG; a config without it must work."""
    cfg = tmp_path / "biocypher_config.yaml"
    cfg.write_text(
        "biocypher:\n"
        "  dbms: csv\n"
        "  offline: true\n"
        "  strict_mode: false\n"
        # No head_ontology key at all.
    )
    monkeypatch.chdir(tmp_path)

    bc = BioCypher(
        biocypher_config_path=str(cfg),
        schema_config_path=SCHEMA_CONFIG,
    )
    onto = bc._get_ontology()
    assert isinstance(onto, NullOntology)
