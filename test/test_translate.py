from linkml_runtime.linkml_model.meta import ClassDefinition
import pytest

from biocypher._config import module_data_path
from biocypher._create import BioCypherEdge, BioCypherNode, VersionNode
from biocypher._translate import (
    BiolinkAdapter,
    gen_translate_edges,
    gen_translate_nodes,
)

__all__ = [
    "driver",
    "test_adapter",
    "test_biolink_yaml_extension",
    "test_custom_bmt_yaml",
    "test_translate_edges",
    "test_translate_identifiers",
    "test_translate_nodes",
    "version_node",
]


@pytest.fixture
def version_node():
    return VersionNode(
        from_config=True,
        config_file="biocypher/_config/test_schema_config.yaml",
        offline=True,
    )


@pytest.fixture
def biolink_adapter(version_node):
    return BiolinkAdapter(
        version_node.leaves,
        schema="biocypher",  # this is the default
        # unstable, move to test yaml
    )


def test_translate_nodes(version_node):
    id_type = [
        ("G9205", "protein", {"taxon": 9606}),
        ("hsa-miR-132-3p", "mirna", {"taxon": 9606}),
        ("ASDB_OSBS", "complex", {"taxon": 9606}),
        ("REACT:25520", "reactome", {}),
    ]
    t = gen_translate_nodes(version_node.leaves, id_type)

    assert all(type(n) == BioCypherNode for n in t)

    t = gen_translate_nodes(version_node.leaves, id_type)
    assert next(t).get_label() == "Protein"
    assert next(t).get_label() == "microRNA"
    assert next(t).get_label() == "MacromolecularComplexMixin"


def test_specific_and_generic_ids(version_node):
    id_type = [
        ("CHAT", "hgnc", {"taxon": 9606}),
        ("REACT:25520", "reactome", {}),
    ]
    t = list(gen_translate_nodes(version_node.leaves, id_type))

    assert (
        t[0].get_id() == "CHAT"
        and t[0].get_properties().get("HGNC") == "CHAT"
        and t[1].get_id() == "REACT:25520"
        and t[1].get_properties().get("REACT") == "REACT:25520"
    )


def test_translate_edges(version_node):
    v = version_node
    # edge type association (defined in `schema_config.yaml`)
    src_tar_type_edge = [
        ("G15258", "MONDO1", "gene_disease", {}),
        ("G15258", "MONDO2", "protein_disease", {}),
        ("G15258", "G15242", "phosphorylation", {}),
    ]
    t = gen_translate_edges(v.leaves, src_tar_type_edge)

    assert type(next(t)) == BioCypherEdge
    assert next(t).get_label() == "PERTURBED_IN_DISEASE"
    assert next(t).get_label() == "Phosphorylation"

    # node type association (defined in `schema_config.yaml`)
    src_tar_type_node = [
        ("G21058", "G50127", "post_translational", {"prop1": "test"}),
        (
            "G22418",
            "G50123",
            "post_translational",
            {"directed": "arbitrary_string"},
        ),
        (
            "G15258",
            "G16347",
            "post_translational",
            {"directed": True, "effect": -1},
        ),
    ]
    t = gen_translate_edges(v.leaves, src_tar_type_node)

    n = next(t)
    n = next(t)
    assert n.get_source_edge().get_label() == "IS_PART_OF"
    n = next(t)
    no = n.get_node()
    assert (
        type(n.get_node()) == BioCypherNode
        and type(n.get_source_edge()) == BioCypherEdge
        and type(n.get_target_edge()) == BioCypherEdge
    )
    assert n.get_node().get_id() == "G15258_G16347_True_-1"
    assert n.get_source_edge().get_source_id() == "G15258"
    assert n.get_target_edge().get_label() == "IS_TARGET_OF"


def test_adapter(version_node):
    ad = BiolinkAdapter(version_node.leaves, schema="biolink")

    assert isinstance(
        ad.biolink_leaves["Protein"]["class_definition"],
        ClassDefinition,
    )


def test_custom_bmt_yaml(version_node):
    ad = BiolinkAdapter(
        version_node.leaves,
        schema=module_data_path("test-biolink-model"),
    )
    p = ad.biolink_leaves["Protein"]

    assert p["class_definition"].description == "Test"


def test_biolink_yaml_extension(biolink_adapter):
    p1 = biolink_adapter.biolink_leaves["PostTranslationalInteraction"]
    p2 = biolink_adapter.biolink_leaves["Phosphorylation"]

    assert (
        p1["class_definition"].description
        == "A pairwise interaction between two proteins"
        and "PairwiseMolecularInteraction" in p1["ancestors"]
        and "Entity" in p1["ancestors"]
        and p2["class_definition"].description
        == "The action of one protein phosphorylating another protein"
        and "PostTranslationalInteraction" in p2["ancestors"]
        and "Entity" in p2["ancestors"]
    )


def test_translate_identifiers(version_node):
    # representation of a different schema
    # host and guest db (which to translate)
    pass


def test_merge_multiple_inputs_node(version_node):
    # Gene has two input labels and one preferred ID
    # no virtual leaves should be created
    # both inputs should lead to creation of the same node type

    # define nodes
    id_type = [
        ("CHAT", "hgnc", {"taxon": 9606}),
        ("CHRNA4", "ensg", {"taxon": 9606}),
    ]
    t = list(gen_translate_nodes(version_node.leaves, id_type))

    # check unique node type
    assert not any([s for s in version_node.leaves.keys() if ".Gene" in s])
    assert any([s for s in version_node.leaves.keys() if ".Pathway" in s])

    # check gen_translate_nodes for unique return type
    assert all([type(n) == BioCypherNode for n in t])
    assert all([n.get_label() == "Gene" for n in t])


def test_merge_multiple_inputs_edge(version_node):
    # GeneToDiseaseAssociation has two input labels and one preferred ID
    # no virtual leaves should be created
    # both inputs should lead to creation of the same node type
    # intersects with driver/writer function

    # define nodes
    src_tar_type = [
        ("CHAT", "AD", "gene_disease", {"taxon": 9606}),
        ("CHRNA4", "AD", "protein_disease", {"taxon": 9606}),
    ]
    t = list(gen_translate_edges(version_node.leaves, src_tar_type))

    # check unique edge type
    assert not any(
        [
            s
            for s in version_node.leaves.keys()
            if ".GeneToDiseaseAssociation" in s
        ]
    )
    assert any(
        [s for s in version_node.leaves.keys() if ".SequenceVariant" in s]
    )

    # check gen_translate_nodes for unique return type
    assert all([type(e) == BioCypherEdge for e in t])
    assert all([e.get_label() == "PERTURBED_IN_DISEASE" for e in t])


def test_multiple_inputs_multiple_virtual_leaves_rel_as_node(biolink_adapter):
    vtg = biolink_adapter.biolink_leaves["VariantToGeneAssociation"]
    kvtg = biolink_adapter.biolink_leaves[
        "Known.SequenceVariant.VariantToGeneAssociation"
    ]
    svtg = biolink_adapter.biolink_leaves[
        "Known.SequenceVariant.VariantToGeneAssociation"
    ]

    assert (
        isinstance(vtg["class_definition"], ClassDefinition)
        and "VariantToGeneAssociation" in kvtg["ancestors"]
        and "VariantToGeneAssociation" in svtg["ancestors"]
    )


def test_ad_hoc_children_node(biolink_adapter):

    se = biolink_adapter.biolink_leaves["SideEffect"]

    assert "PhenotypicFeature" in se["ancestors"]


def test_multiple_inheritance(biolink_adapter):

    mta = biolink_adapter.biolink_leaves.get("MutationToTissueAssociation")
    gta = biolink_adapter.biolink_leaves.get("GenotypeToTissueAssociation")
    eta = biolink_adapter.biolink_leaves.get("EntityToTissueAssociation")

    assert (
        "MutationToTissueAssociation" in mta["ancestors"]
        and "GenotypeToTissueAssociation" in mta["ancestors"]
        and "EntityToTissueAssociation" in mta["ancestors"]
        and "Association" in mta["ancestors"]
        and "GenotypeToTissueAssociation" in gta["ancestors"]
        and "EntityToTissueAssociation" in gta["ancestors"]
        and "Association" in gta["ancestors"]
        and "EntityToTissueAssociation" in eta["ancestors"]
        and "Association" in eta["ancestors"]
    )


def test_properties_from_config(version_node):
    id_type = [
        ("G49205", "protein", {"taxon": 9606, "name": "test"}),
        ("G92035", "protein", {"taxon": 9606}),
        (
            "G92205",
            "protein",
            {"taxon": 9606, "name": "test2", "test": "should_not_be_returned"},
        ),
    ]
    t = gen_translate_nodes(version_node.leaves, id_type)

    r = list(t)
    assert (
        "name" in r[0].get_properties().keys()
        and "name" in r[1].get_properties().keys()
        and "test" not in r[2].get_properties().keys()
    )

    src_tar_type = [
        (
            "G49205",
            "AD",
            "gene_gene",
            {
                "directional": True,
                "score": 0.5,
            },
        ),
        (
            "G92035",
            "AD",
            "gene_gene",
            {
                "directional": False,
                "curated": True,
                "score": 0.5,
                "test": "should_not_be_returned",
            },
        ),
    ]

    t = gen_translate_edges(version_node.leaves, src_tar_type)

    r = list(t)
    assert (
        "directional" in r[0].get_properties().keys()
        and "directional" in r[1].get_properties().keys()
        and "curated" in r[1].get_properties().keys()
        and "score" in r[0].get_properties().keys()
        and "score" in r[1].get_properties().keys()
        and "test" not in r[1].get_properties().keys()
    )
