import pytest

from biocypher._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode


@pytest.fixture(scope="function")
def _get_nodes(length: int) -> list:
    nodes = []
    for i in range(length):
        bnp = BioCypherNode(
            node_id=f"p{i + 1}",
            node_label="protein",
            preferred_id="uniprot",
            properties={
                "score": 4 / (i + 1),
                "name": "StringProperty1",
                "taxon": 9606,
                "genes": ["gene1", "gene2"],
            },
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            node_id=f"m{i + 1}",
            node_label="microRNA",
            preferred_id="mirbase",
            properties={
                "name": "StringProperty1",
                "taxon": 9606,
            },
        )
        nodes.append(bnm)

    return nodes


@pytest.fixture(scope="function")
def _get_nodes_non_compliant_names(length: int) -> list:
    nodes = []
    for i in range(length):
        bnp = BioCypherNode(
            node_id=f"p{i + 1}",
            node_label="Patient (person)",
            preferred_id="snomedct",
            properties={},
        )
        nodes.append(bnp)
        bnm = BioCypherNode(
            node_id=f"m{i + 1}",
            node_label="1$He524ll<o wor.ld <(",
            preferred_id="snomedct",
            properties={},
        )
        nodes.append(bnm)

    return nodes


@pytest.fixture(scope="function")
def _get_edges(length):
    edges = []
    for i in range(length):
        e1 = BioCypherEdge(
            relationship_id=f"prel{i}",
            source_id=f"p{i}",
            target_id=f"p{i + 1}",
            relationship_label="PERTURBED_IN_DISEASE",
            properties={
                "residue": "T253",
                "level": 4,
            },
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e1)
        e2 = BioCypherEdge(
            relationship_id=f"mrel{i}",
            source_id=f"m{i}",
            target_id=f"p{i + 1}",
            relationship_label="Is_Mutated_In",
            properties={
                "site": "3-UTR",
                "confidence": 1,
            },
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e2)
    return edges


@pytest.fixture(scope="function")
def _get_edges_non_compliant_names(length):
    edges = []
    for i in range(length):
        e1 = BioCypherEdge(
            relationship_id=f"prel{i}",
            source_id=f"p{i}",
            target_id=f"p{i + 1}",
            relationship_label="(Compliant) edge",
            properties={},
        )
        edges.append(e1)
        e2 = BioCypherEdge(
            relationship_id=f"mrel{i}",
            source_id=f"m{i}",
            target_id=f"p{i + 1}",
            relationship_label="42Is_Mutated_In",
            properties={
                "site": "3-UTR",
                "confidence": 1,
            },
            # we suppose the verb-form relationship label is created by
            # translation functionality in translate.py
        )
        edges.append(e2)
    return edges


@pytest.fixture(scope="function")
def _get_rel_as_nodes(length):
    rels = []
    for i in range(length):
        n = BioCypherNode(
            node_id=f"i{i + 1}",
            node_label="post translational interaction",
            properties={
                "directed": True,
                "effect": -1,
            },
        )
        e1 = BioCypherEdge(
            source_id=f"i{i + 1}",
            target_id=f"p{i + 1}",
            relationship_label="IS_SOURCE_OF",
        )
        e2 = BioCypherEdge(
            source_id=f"i{i}",
            target_id=f"p{i + 2}",
            relationship_label="IS_TARGET_OF",
        )
        rels.append(BioCypherRelAsNode(n, e1, e2))
    return rels


# Immunology data: TCR alpha and beta chains + epitopes


# TCR alpha chain test nodes
@pytest.fixture()
def tra_nodes():
    """Return a list of TCR alpha chain nodes for testing."""
    return [
        BioCypherNode(
            node_id="tra:CAVRWGGKLSF",
            node_label="tra sequence",
            preferred_id="tra:CAVRWGGKLSF",
            properties={
                "junction_aa": "CAVRWGGKLSF",
                "chain_1_type": "tra",
                "chain_1_organism": "HomoSapiens",
                "chain_1_v_gene": "TRAV3*01",
                "chain_1_j_gene": "TRAJ20*01",
            },
        ),
        BioCypherNode(
            node_id="tra:CAGLLPGGGADGLTF",
            node_label="tra sequence",
            preferred_id="tra:CAGLLPGGGADGLTF",
            properties={
                "junction_aa": "CAGLLPGGGADGLTF",
                "chain_1_type": "tra",
                "chain_1_organism": "HomoSapiens",
                "chain_1_v_gene": "TRAV25*01",
                "chain_1_j_gene": "TRAJ45*01",
            },
        ),
        BioCypherNode(
            node_id="tra:CAVDNNNDMRF",
            node_label="tra sequence",
            preferred_id="tra:CAVDNNNDMRF",
            properties={
                "junction_aa": "CAVDNNNDMRF",
                "chain_1_type": "tra",
                "chain_1_v_gene": "TRAV12-2",
                "chain_1_j_gene": "TRAJ24",
            },
        ),
    ]


# TCR beta chain test nodes
@pytest.fixture()
def trb_nodes():
    """Return a list of TCR beta chain nodes for testing."""
    return [
        BioCypherNode(
            node_id="trb:CASSEGGVETQYF",
            node_label="trb sequence",
            preferred_id="trb:CASSEGGVETQYF",
            properties={
                "junction_aa": "CASSEGGVETQYF",
                "chain_1_type": "trb",
                "chain_1_organism": "HomoSapiens",
                "chain_1_v_gene": "TRBV13*01",
                "chain_1_j_gene": "TRBJ2-5*01",
            },
        ),
        BioCypherNode(
            node_id="trb:CASSSRGGQETQYF",
            node_label="trb sequence",
            preferred_id="trb:CASSSRGGQETQYF",
            properties={
                "junction_aa": "CASSSRGGQETQYF",
                "chain_1_type": "trb",
                "chain_1_organism": "HomoSapiens",
                "chain_1_v_gene": "TRBV7-3*01",
                "chain_1_j_gene": "TRBJ2-5*01",
            },
        ),
        BioCypherNode(
            node_id="trb:CASSPRGDSGNTIYF",
            node_label="trb sequence",
            preferred_id="trb:CASSPRGDSGNTIYF",
            properties={
                "junction_aa": "CASSPRGDSGNTIYF",
                "chain_1_type": "trb",
                "chain_1_v_gene": "TRBV7-9",
                "chain_1_j_gene": "TRBJ2-2",
            },
        ),
    ]


# Epitope test nodes
@pytest.fixture()
def epitope_nodes():
    """Return a list of epitope nodes for testing."""
    return [
        BioCypherNode(
            node_id="epitope:NLVPMVATV",
            node_label="epitope",
            preferred_id="epitope:NLVPMVATV",
            properties={
                "antigen_name": "pp65",
                "antigen_organism": "CMV",
                "MHC_class": "MHCI",
            },
        ),
        BioCypherNode(
            node_id="epitope:KLGGALQAK",
            node_label="epitope",
            preferred_id="epitope:KLGGALQAK",
            properties={
                "antigen_name": "IE1",
                "antigen_organism": "CMV",
                "MHC_class": "MHCI",
            },
        ),
        BioCypherNode(
            node_id="epitope:GILGFVFTL",
            node_label="epitope",
            preferred_id="epitope:GILGFVFTL",
            properties={
                "antigen_name": "M",
                "antigen_organism": "InfluenzaA",
                "MHC_class": "MHCI",
            },
        ),
    ]


# TCR pairing edges
@pytest.fixture()
def tcr_pair_edges():
    """Return a list of TCR alpha-beta pairing edges for testing."""
    return [
        BioCypherEdge(
            source_id="tra:CAVRWGGKLSF",
            target_id="trb:CASSEGGVETQYF",
            relationship_id="tra:CAVRWGGKLSF-trb:CASSEGGVETQYF",
            relationship_label="alpha sequence to beta sequence association",
        ),
        BioCypherEdge(
            source_id="tra:CAGLLPGGGADGLTF",
            target_id="trb:CASSSRGGQETQYF",
            relationship_id="tra:CAGLLPGGGADGLTF-trb:CASSSRGGQETQYF",
            relationship_label="alpha sequence to beta sequence association",
        ),
        BioCypherEdge(
            source_id="tra:CAVDNNNDMRF",
            target_id="trb:CASSPRGDSGNTIYF",
            relationship_id="tra:CAVDNNNDMRF-trb:CASSPRGDSGNTIYF",
            relationship_label="alpha sequence to beta sequence association",
        ),
    ]


# TCR-epitope association edges
@pytest.fixture()
def tcr_epitope_edges():
    """Return a list of TCR-to-epitope binding edges for testing."""
    return [
        BioCypherEdge(
            source_id="tra:CAVRWGGKLSF",
            target_id="epitope:NLVPMVATV",
            relationship_id="bind1",
            relationship_label="t cell receptor sequence to epitope association",
        ),
        BioCypherEdge(
            source_id="tra:CAVRWGGKLSF",
            target_id="epitope:KLGGALQAK",
            relationship_id="bind2",
            relationship_label="t cell receptor sequence to epitope association",
        ),
        BioCypherEdge(
            source_id="trb:CASSPRGDSGNTIYF",
            target_id="epitope:NLVPMVATV",
            relationship_id="bind3",
            relationship_label="t cell receptor sequence to epitope association",
        ),
        BioCypherEdge(
            source_id="tra:CAVDNNNDMRF",
            target_id="epitope:GILGFVFTL",
            relationship_id="bind4",
            relationship_label="t cell receptor sequence to epitope association",
        ),
        BioCypherEdge(
            source_id="tra:CAVDNNNDMRF",
            target_id="epitope:NLVPMVATV",
            relationship_id="bind5",
            relationship_label="t cell receptor sequence to epitope association",
        ),
    ]
