import os
from unittest.mock import MagicMock, patch

import pytest
import yaml

from biocypher import BioCypher
from biocypher.output.in_memory._get_in_memory_kg import IN_MEMORY_DBMS
from biocypher.output.write._get_writer import DBMS_TO_CLASS


def test_biocypher(core):
    assert core._dbms == "neo4j"
    assert core._offline
    assert not core._strict_mode


def test_log_missing_types(core, translator):
    core._translator = translator
    core._translator.notype = {}
    assert core.log_missing_input_labels() is None

    core._translator.notype = {"a": 1, "b": 2}
    real_missing_types = core.log_missing_input_labels()

    assert real_missing_types.get("a") == 1 and real_missing_types.get("b") == 2


@pytest.mark.parametrize("length", [4], scope="function")
def test_log_duplicates(core, deduplicator, _get_nodes):
    core._deduplicator = deduplicator
    nodes = _get_nodes + _get_nodes

    core.add(nodes)
    core.log_duplicates()

    assert "protein" in core._deduplicator.duplicate_entity_types
    assert "p1" in core._deduplicator.duplicate_entity_ids
    assert "microRNA" in core._deduplicator.duplicate_entity_types
    assert "m1" in core._deduplicator.duplicate_entity_ids


@pytest.mark.parametrize("length", [4], scope="function")
def test_write_schema_info(core, _get_nodes, _get_edges, _get_rel_as_nodes):
    core._offline = False
    core._dbms = "csv"
    core.add(_get_nodes)
    core.add(_get_edges)
    core.add(_get_rel_as_nodes)

    schema = core.write_schema_info()

    assert schema.get("is_schema_info")
    assert schema.get("protein").get("present_in_knowledge_graph")
    assert not schema.get("protein").get("is_relationship")
    assert schema.get("microRNA").get("present_in_knowledge_graph")
    assert not schema.get("microRNA").get("is_relationship")
    assert schema.get("gene to disease association").get("present_in_knowledge_graph")

    assert schema.get("gene to disease association").get("is_relationship")
    assert schema.get("mutation to tissue association").get("present_in_knowledge_graph")
    assert schema.get("mutation to tissue association").get("is_relationship")
    assert schema.get("post translational interaction").get("present_in_knowledge_graph")
    assert schema.get("post translational interaction").get("is_relationship")

    path = os.path.join(core._output_directory, "schema_info.yaml")
    assert os.path.exists(path)

    with open(path, "r") as f:
        schema_loaded = yaml.safe_load(f)

    assert schema_loaded == schema


def test_show_full_ontology_structure_without_schema():
    bc = BioCypher(
        head_ontology={
            "url": "test/ontologies/so.owl",
            "root_node": "sequence_variant",
        }
    )
    treevis = bc.show_ontology_structure(full=True)

    assert "sequence variant" in treevis
    assert "functional effect variant" in treevis
    assert "altered gene product level" in treevis
    assert "decreased gene product level" in treevis
    assert "functionally abnormal" in treevis
    assert "lethal variant" in treevis


def test_in_memory_kg_only_in_online_mode(core):
    for in_memory_dbms in IN_MEMORY_DBMS:
        core._dbms = in_memory_dbms
        core._offline = True
        with pytest.raises(ValueError) as e:
            core.get_kg()
        assert "Getting the in-memory KG is only available in online mode for " in str(e.value)
        assert isinstance(e.value.args[0], str), "error message must be a str, not a tuple"


def test_no_in_memory_kg_for_dbms(core):
    for dbms in ["neo4j", "arangodb", "rdf"]:
        core._dbms = dbms
        core._offline = False
        with pytest.raises(ValueError) as e:
            core.get_kg()
        assert "Getting the in-memory KG is only available in online mode for " in str(e.value)


def test_no_in_memory_instance_found(core):
    core._dbms = "csv"
    core._offline = False

    with pytest.raises(ValueError) as e:
        core.get_kg()
    assert str(e.value) == "No in-memory KG instance found. Please call `add()` first."


def test_online_mode_not_supported_for_dbms(core):
    for dbms in ["arangodb", "rdf", "postgres", "sqlite3"]:
        core._dbms = dbms
        core._offline = False
        with pytest.raises(NotImplementedError) as e:
            core._get_driver()
        assert str(e.value) == f"Online mode is not supported for the DBMS {dbms}."


def test_get_driver_in_offline_mode(core):
    for dbms in ["neo4j"]:
        core._dbms = dbms
        core._offline = True
        with pytest.raises(NotImplementedError) as e:
            core._get_driver()
        assert str(e.value) == "Cannot get driver in offline mode."


def test_get_writer_in_online_mode(core):
    for dbms in DBMS_TO_CLASS.keys():
        core._dbms = dbms
        core._offline = False
        with pytest.raises(NotImplementedError) as e:
            core._initialize_writer()
        assert str(e.value) == "Cannot get writer in online mode."


@pytest.mark.parametrize("length", [4], scope="function")
def test_online_add_edges_calls_add_biocypher_edges(core, _get_edges):
    """_add_edges must call add_biocypher_edges (not add_biocypher_nodes) on the driver."""
    mock_driver = MagicMock()
    mock_driver.add_biocypher_edges.return_value = True

    core._offline = False
    core._dbms = "neo4j"

    with patch.object(core, "_get_driver", return_value=mock_driver):
        core.write_edges(_get_edges)

    mock_driver.add_biocypher_edges.assert_called_once()
    mock_driver.add_biocypher_nodes.assert_not_called()


def test_pandas_and_tabular_work_in_offline_mode(tmp_path):
    """pandas and tabular are aliases for csv and should work in offline mode."""
    for dbms in ["pandas", "tabular"]:
        bc = BioCypher(
            dbms=dbms,
            offline=True,
            schema_config_path="biocypher/_config/test_schema_config.yaml",
            output_directory=str(tmp_path),
        )
        assert bc._dbms == dbms
        assert bc._offline


def test_translate_term_via_core(core):
    """BioCypher.translate_term must lazily initialise the translator and return the mapped label."""
    assert core._translator is None
    result = core.translate_term("hgnc")
    assert result == "Gene"
    assert core._translator is not None


def test_reverse_translate_term_via_core(core):
    """BioCypher.reverse_translate_term must lazily initialise the translator and reverse-map the label."""
    assert core._translator is None
    result = core.reverse_translate_term("Gene")
    assert result is not None
    assert "hgnc" in result


def test_translate_query_via_core(core):
    """BioCypher.translate_query must lazily initialise the translator and translate Cypher labels."""
    assert core._translator is None
    query = "MATCH (n:hgnc) RETURN n"
    result = core.translate_query(query)
    assert "Gene" in result
    assert "hgnc" not in result


def test_reverse_translate_query_via_core(core):
    """BioCypher.reverse_translate_query must lazily initialise the translator."""
    assert core._translator is None
    query = "MATCH (n:Protein)-[r:POST_TRANSLATIONAL_INTERACTION]->(m:Protein) RETURN n"
    result = core.reverse_translate_query(query)
    assert isinstance(result, str)


@pytest.mark.parametrize("length", [4], scope="function")
def test_add_nodes_first_call_does_not_crash(core, _get_nodes):
    """add_nodes must not crash when self._nodes is still None (first call)."""
    # self._nodes starts as None; passing a list used to raise
    # TypeError: 'NoneType' object is not iterable via itertools.chain
    core.add_nodes(_get_nodes)
    assert core._nodes == _get_nodes


@pytest.mark.parametrize("length", [4], scope="function")
def test_add_nodes_accumulates_across_calls(core, _get_nodes):
    """Successive add_nodes calls must append, not crash on the second call."""
    first_half = _get_nodes[:4]
    second_half = _get_nodes[4:]
    core.add_nodes(first_half)
    core.add_nodes(second_half)
    assert len(core._nodes) == len(first_half) + len(second_half)


@pytest.mark.parametrize("length", [4], scope="function")
def test_add_edges_first_call_does_not_crash(core, _get_edges):
    """add_edges must not crash when self._edges is still None (first call)."""
    core.add_edges(_get_edges)
    assert core._edges == _get_edges
