import os

import yaml
import pytest

from biocypher import BioCypher


def test_biocypher(core):
    assert core._dbms == "neo4j"
    assert core._offline == True
    assert core._strict_mode == False


def test_log_missing_types(core, translator):
    core._translator = translator
    core._translator.notype = {}
    assert core.log_missing_input_labels() == None

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
    core.add(_get_nodes)
    core.add(_get_edges)
    core.add(_get_rel_as_nodes)

    schema = core.write_schema_info()

    assert schema.get("is_schema_info") == True
    assert schema.get("protein").get("present_in_knowledge_graph") == True
    assert schema.get("protein").get("is_relationship") == False
    assert schema.get("microRNA").get("present_in_knowledge_graph") == True
    assert schema.get("microRNA").get("is_relationship") == False
    assert (
        schema.get("gene to disease association").get(
            "present_in_knowledge_graph"
        )
        == True
    )
    assert (
        schema.get("gene to disease association").get("is_relationship") == True
    )
    assert (
        schema.get("mutation to tissue association").get(
            "present_in_knowledge_graph"
        )
        == True
    )
    assert (
        schema.get("mutation to tissue association").get("is_relationship")
        == True
    )
    assert (
        schema.get("post translational interaction").get(
            "present_in_knowledge_graph"
        )
        == True
    )
    assert (
        schema.get("post translational interaction").get("is_relationship")
        == True
    )

    path = os.path.join(core._output_directory, "schema_info.yaml")
    assert os.path.exists(path)

    with open(path, "r") as f:
        schema_loaded = yaml.safe_load(f)

    assert schema_loaded == schema


def test_show_full_ontology_structure_without_schema():
    bc = BioCypher(
        head_ontology={
            "url": "test/so.owl",
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


# def test_access_translate(driver):

#     driver.start_ontology()

#     assert driver.translate_term('mirna') == 'MicroRNA'
#     assert (driver.reverse_translate_term('SideEffect') == 'sider')
#     assert (
#         driver.translate_query('MATCH (n:reactome) RETURN n') ==
#         'MATCH (n:Reactome.Pathway) RETURN n'
#     )
#     assert (
#         driver.reverse_translate_query(
#             'MATCH (n:Wikipathways.Pathway) RETURN n',
#         ) == 'MATCH (n:wikipathways) RETURN n'
#     )
