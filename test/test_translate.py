from linkml_runtime.linkml_model.meta import ClassDefinition
from biocypher.create import BioCypherEdge, BioCypherNode
from biocypher.translate import (
    gen_translate_edges,
    gen_translate_nodes,
    BiolinkAdapter,
)
from biocypher.check import VersionNode
from biocypher.driver import Driver
import pytest


@pytest.fixture
def driver():
    # neo4j database needs to be running!
    d = Driver(increment_version=False)
    yield d

    # teardown
    d.close()


@pytest.fixture
def version_node(driver):
    return VersionNode(driver)


def test_translate_nodes(version_node):
    id_type = [
        ("G9205", "protein", {"taxon": 9606}),
        ("hsa-miR-132-3p", "mirna", {"taxon": 9606}),
        ("ASDB_OSBS", "complex", {"taxon": 9606}),
    ]
    t = gen_translate_nodes(version_node.leaves, id_type)

    assert all(type(n) == BioCypherNode for n in t)

    t = gen_translate_nodes(version_node.leaves, id_type)
    assert next(t).get_label() == "Protein"
    assert next(t).get_label() == "microRNA"
    assert next(t).get_label() == "MacromolecularComplexMixin"


def test_translate_edges(version_node):
    # edge type association (defined in `schema_config.yaml`)
    # TODO

    # node type association (defined in `schema_config.yaml`)
    v = version_node
    src_tar_type = [
        ("G21058", "G50127", "post_translational", {"prop1": "test"}),
        (
            "G15258",
            "G16347",
            "post_translational",
            {"prop1": "test", "prop2": "test"},
        ),
        ("G22418", "G50123", "post_translational", {}),
    ]
    t = gen_translate_edges(v.leaves, src_tar_type)

    n = next(t)
    no = n.get_node()
    assert (
        type(n.get_node()) == BioCypherNode
        and type(n.get_source_edge()) == BioCypherEdge
        and type(n.get_target_edge()) == BioCypherEdge
    )
    assert n.get_node().get_id() == "G21058_G50127_test"
    assert n.get_source_edge().get_source_id() == "G21058"
    assert n.get_target_edge().get_label() == "IS_TARGET_OF"


def test_adapter(version_node):
    ad = BiolinkAdapter(version_node.leaves, custom_yaml=False)

    assert isinstance(
        ad.leaves["Protein"]["class_definition"], ClassDefinition
    )


def test_custom_bmt_yaml(version_node):
    ad = BiolinkAdapter(
        version_node.leaves, custom_yaml_file="/config/test-biolink-model.yaml"
    )
    p = ad.leaves["Protein"]

    assert p["class_definition"].description == "Test"


def test_biolink_yaml_extension(version_node):
    ad = BiolinkAdapter(
        version_node.leaves,
        custom_yaml_file="/config/biocypher-biolink-model.yaml",
    )
    p1 = ad.leaves["PostTranslationalInteraction"]
    p2 = ad.leaves["Phosphorylation"]

    assert (
        p1["class_definition"].description
        == "A pairwise interaction between two proteins"
        and "biolink:PairwiseMolecularInteraction" in p1["ancestors"]
        and "biolink:Entity" in p1["ancestors"]
        and p2["class_definition"].description
        == "The action of one protein phosphorylating another protein"
        and "biolink:PostTranslationalInteraction" in p2["ancestors"]
        and "biolink:Entity" in p2["ancestors"]
    )
