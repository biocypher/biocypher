import logging
import os
import re
import sys

import pytest
import pyarrow.parquet as pq

from genericpath import isfile

from biocypher._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode
from biocypher.output.write._batch_writer import parse_label
from biocypher.output.write.graph._neo4j import _Neo4jBatchWriter


def get_csv_content(file_path):
    """Read CSV file content as string."""
    with open(file_path) as f:
        return f.read()


def get_parquet_content_as_rows(file_path):
    table = pq.read_table(file_path)
    return [tuple(row.values()) for row in table.to_pylist()]


def test_neo4j_writer_and_output_dir(bw):
    tmp_path = bw.outdir

    assert os.path.isdir(tmp_path) and isinstance(bw, _Neo4jBatchWriter) and bw.delim == ";"


def test_create_import_call(bw):
    mixed = []
    number_of_items = 4
    for i in range(number_of_items):
        node = BioCypherNode(
            f"i{i + 1}",
            "post translational interaction",
        )
        edge_1 = BioCypherEdge(
            source_id=f"i{i + 1}",
            target_id=f"p{i + 1}",
            relationship_label="IS_SOURCE_OF",
        )
        edge_2 = BioCypherEdge(
            source_id=f"i{i}",
            target_id=f"p{i + 2}",
            relationship_label="IS_TARGET_OF",
        )
        mixed.append(BioCypherRelAsNode(node, edge_1, edge_2))

        edge_3 = BioCypherEdge(
            source_id=f"p{i + 1}",
            target_id=f"p{i + 1}",
            relationship_label="PERTURBED_IN_DISEASE",
        )
        mixed.append(edge_3)

    def gen(lis):
        yield from lis

    passed = bw.write_edges(gen(mixed))

    call = bw.get_import_call()

    tmp_path = bw.outdir

    assert passed
    assert "neo4j-admin" in call
    assert "import" in call
    assert '--delimiter=";"' in call
    assert '--array-delimiter="|" --quote="\'"' in call
    assert (
        f'--nodes="{tmp_path}{os.sep}PostTranslationalInteraction-header.csv,'
        f'{tmp_path}{os.sep}PostTranslationalInteraction-part.*" '
    ) in call
    assert (
        f'--relationships="{tmp_path}{os.sep}IS_SOURCE_OF-header.csv,{tmp_path}{os.sep}IS_SOURCE_OF-part.*" '
    ) in call
    assert (
        f'--relationships="{tmp_path}{os.sep}IS_TARGET_OF-header.csv,{tmp_path}{os.sep}IS_TARGET_OF-part.*" '
    ) in call
    assert (
        f'--relationships="{tmp_path}{os.sep}PERTURBED_IN_DISEASE-header.csv,'
        f'{tmp_path}{os.sep}PERTURBED_IN_DISEASE-part.*" '
    ) in call


@pytest.mark.parametrize("length", [4], scope="module")
def test_neo4j_write_node_data_headers_import_call(bw, _get_nodes):
    # four proteins, four miRNAs
    nodes = _get_nodes

    passed = bw.write_nodes(nodes[:4])
    passed = bw.write_nodes(nodes[4:])
    bw.write_import_call()

    assert passed

    tmp_path = bw.outdir

    protein_header_csv = os.path.join(tmp_path, "Protein-header.csv")
    micro_rna_header_csv = os.path.join(tmp_path, "MicroRNA-header.csv")

    # Determine import call script name based on OS
    if sys.platform.startswith("win"):
        import_call_path = os.path.join(tmp_path, "neo4j-admin-import-call.ps1")
    else:
        import_call_path = os.path.join(tmp_path, "neo4j-admin-import-call.sh")

    with open(protein_header_csv) as f:
        protein_header = f.read()
    with open(micro_rna_header_csv) as f:
        micro_rna_header = f.read()
    with open(import_call_path) as f:
        call = f.read()

    if bw.file_format == "parquet":
        assert protein_header == ":ID;name;score:double;taxon:long;genes;id;preferred_id;:LABEL"
    else:
        assert protein_header == ":ID;name;score:double;taxon:long;genes:string[];id;preferred_id;:LABEL"
    assert micro_rna_header == ":ID;name;taxon:long;id;preferred_id;:LABEL"
    assert "neo4j-admin" in call
    assert "import" in call
    assert '--delimiter=";"' in call
    assert '--nodes="' in call
    assert "Protein-header.csv" in call
    assert 'Protein-part.*"' in call
    assert "MicroRNA-header.csv" in call
    assert 'MicroRNA-part.*"' in call

    # custom import call executable path
    bw.import_call_bin_prefix = "custom/path/"

    os.remove(import_call_path)
    bw.write_import_call()

    with open(import_call_path) as f:
        call = f.read()

    assert "custom/path/neo4j-admin" in call
    assert "import" in call

    # custom file prefix
    # TODO


def test_construct_import_call(bw):
    assert isinstance(bw, _Neo4jBatchWriter)

    import_script = bw._construct_import_call()

    assert "neo4j-admin" in import_script
    assert "import" in import_script
    assert "--database=neo4j" in import_script

    if sys.platform.startswith("win"):
        # PowerShell-specific assertions
        assert ".ps1" in import_script
        assert "$version" in import_script or "powershell" in import_script
        assert "$NEO4J_BIN_PATH_WINDOWS" in import_script
        assert "--overwrite-destination=true" in import_script or "--force=true" in import_script
    else:
        # Bash-specific assertions
        assert "#!" in import_script
        assert "version=$(" in import_script
        assert "if [[ $version -lt 5 ]]" in import_script
        assert 'echo "Neo4j detected version: $version"' in import_script
        assert "bin/neo4j-admin import --database=neo4j" in import_script
        assert "bin/neo4j-admin database import full neo4j" in import_script
        assert "--force=true" in import_script
        assert "--overwrite-destination=true" in import_script


def test_construct_import_call_bash(bw):
    assert isinstance(bw, _Neo4jBatchWriter)

    import_script = bw._construct_import_call_bash()

    if not sys.platform.startswith("win"):
        if "SHELL" in os.environ:
            assert "#!" in import_script
            assert "version=$(" in import_script
            assert 'echo "Neo4j detected version: $version"' in import_script
            assert "if [[ $version -lt 5 ]]" in import_script
            assert "else" in import_script
            assert "fi" in import_script
            assert "--overwrite-destination=true" in import_script
            assert "bin/neo4j-admin import" in import_script
            assert "--force=true" in import_script
            assert "--database=neo4j" in import_script
            assert "bin/neo4j-admin database import full neo4j" in import_script
            assert "bin/neo4j-admin import --database=neo4j" in import_script
            assert '--delimiter=";"' in import_script
            assert '--array-delimiter="|"' in import_script
        else:
            assert "#" in import_script
            assert "bin/neo4j-admin import" in import_script
            assert "--database=neo4j" in import_script
            assert '--delimiter=";"' in import_script
            assert '--array-delimiter="|"' in import_script
            assert "--force=true" in import_script

            assert "bin/neo4j-admin database import full neo4j" in import_script
            assert "--overwrite-destination=true" in import_script


def test_construct_import_call_powershell(bw):
    assert isinstance(bw, _Neo4jBatchWriter)

    import_script = bw._construct_import_call_powershell()

    assert "$version" in import_script or "powershell" in import_script
    assert "neo4j-admin" in import_script
    assert ".ps1" in import_script

    assert "--overwrite-destination=true" in import_script
    assert "$NEO4J_BIN_PATH_WINDOWS $args_neo4j" in import_script
    assert "--force=true" in import_script
    assert "--database=neo4j" in import_script
    assert "neo4j" in import_script
    assert "database import full neo4j" in import_script
    assert "import --database=neo4j" in import_script


def test_write_hybrid_ontology_nodes(bw):
    nodes = []
    for i in range(4):
        nodes.append(
            BioCypherNode(
                node_id=f"agpl:000{i}",
                node_label="altered gene product level",
                properties={},
            ),
        )

    passed = bw.write_nodes(nodes)

    assert passed

    tmp_path = bw.outdir

    header_csv = os.path.join(tmp_path, "AlteredGeneProductLevel-header.csv")
    data_file = os.path.join(
        tmp_path,
        "AlteredGeneProductLevel-part000.csv"
        if bw.file_format != "parquet"
        else "AlteredGeneProductLevel-part000.parquet",
    )

    with open(header_csv) as f:
        header = f.read()

    assert header == ":ID;id;preferred_id;:LABEL"

    if bw.file_format == "parquet":
        rows = get_parquet_content_as_rows(data_file)
        assert rows[0][:-1] == ("agpl:0000", "agpl:0000", "id")
        assert "AlteredGeneProductLevel" in rows[0][-1]
        assert "BiologicalEntity" in rows[0][-1]
    else:
        with open(data_file) as f:
            part = f.read()

        assert "agpl:0000;'agpl:0000';'id'" in part
        assert "AlteredGeneProductLevel" in part
        assert "BiologicalEntity" in part


def test_property_types(bw):
    nodes = []
    for i in range(4):
        biocypher_node_protein = BioCypherNode(
            node_id=f"p{i + 1}",
            node_label="protein",
            properties={
                "score": 4 / (i + 1),
                "name": "StringProperty1",
                "taxon": 9606,
                "genes": ["gene1", "gene2"],
            },
        )
        nodes.append(biocypher_node_protein)

    passed = bw.write_nodes(nodes, batch_size=1e6)

    tmp_path = bw.outdir

    data_csv = os.path.join(
        tmp_path,
        "Protein-part000.csv" if bw.file_format != "parquet" else "Protein-part000.parquet",
    )
    header_csv = os.path.join(tmp_path, "Protein-header.csv")

    assert passed

    if bw.file_format == "parquet":
        rows = get_parquet_content_as_rows(data_csv)
        assert rows[0][:-1] == ("p1", "StringProperty1", 4.0, 9606, ["gene1", "gene2"], "p1", "id")
        assert "BiologicalEntity" in rows[0][-1]
    else:
        with open(data_csv) as f:
            data = f.read()

        with open(header_csv) as f:
            header = f.read()

        assert header == ":ID;name;score:double;taxon:long;genes:string[];id;preferred_id;:LABEL"
        assert "p1;'StringProperty1';4.0;9606;'gene1|gene2';'p1';'id'" in data
        assert "BiologicalEntity" in data


@pytest.mark.parametrize("length", [4], scope="module")
def test_write_node_data_from_list(bw, _get_nodes):
    nodes = _get_nodes

    passed = bw._write_node_data(nodes, batch_size=1e6)

    tmp_path = bw.outdir

    protein_file = os.path.join(
        tmp_path,
        "Protein-part000.csv" if bw.file_format != "parquet" else "Protein-part000.parquet",
    )
    micro_rna_file = os.path.join(
        tmp_path,
        "MicroRNA-part000.csv" if bw.file_format != "parquet" else "MicroRNA-part000.parquet",
    )

    assert passed

    if bw.file_format == "parquet":
        protein_rows = get_parquet_content_as_rows(protein_file)
        micro_rna_rows = get_parquet_content_as_rows(micro_rna_file)
        assert protein_rows[0][:-1] == (
            "p1",
            "StringProperty1",
            4.0,
            9606,
            ["gene1", "gene2"],
            "p1",
            "uniprot",
        )
        assert "BiologicalEntity" in protein_rows[0][-1]
        assert micro_rna_rows[0][:-1] == ("m1", "StringProperty1", 9606, "m1", "mirbase")
        assert "ChemicalEntity" in micro_rna_rows[0][-1]
    else:
        with open(protein_file) as f:
            protein = f.read()

        with open(micro_rna_file) as f:
            micro_rna = f.read()

        assert "p1;'StringProperty1';4.0;9606;'gene1|gene2';'p1';'uniprot'" in protein
        assert "BiologicalEntity" in protein
        assert "m1;'StringProperty1';9606;'m1';'mirbase'" in micro_rna
        assert "ChemicalEntity" in micro_rna


def test_write_node_data_boolean_properties(bw):
    """Boolean node properties must be written as lowercase 'true'/'false' for Neo4j admin import."""
    nodes = [
        BioCypherNode(
            node_id="i1",
            node_label="post translational interaction",
            properties={"directed": True, "effect": -1},
        ),
        BioCypherNode(
            node_id="i2",
            node_label="post translational interaction",
            properties={"directed": False, "effect": 1},
        ),
    ]

    passed = bw._write_node_data(nodes, batch_size=int(1e4))

    post_translational_interaction_output = os.path.join(
        bw.outdir,
        "PostTranslationalInteraction-part000.csv"
        if bw.file_format != "parquet"
        else "PostTranslationalInteraction-part000.parquet",
    )

    assert passed

    if bw.file_format == "parquet":
        rows = get_parquet_content_as_rows(post_translational_interaction_output)
        assert rows[0][:-1] == ("i1", True, -1, "i1", "id")
        assert rows[1][:-1] == ("i2", False, 1, "i2", "id")
    else:
        with open(post_translational_interaction_output) as f:
            post_translational_interaction = f.read()

        assert "i1;true;-1;'i1';'id'" in post_translational_interaction
        assert "i2;false;1;'i2';'id'" in post_translational_interaction
        assert "True" not in post_translational_interaction
        assert "False" not in post_translational_interaction


def test_write_node_data_non_string_list_properties(bw):
    """List properties with non-string elements must not raise TypeError during write."""
    nodes = [
        BioCypherNode(
            node_id="i1",
            node_label="post translational interaction",
            properties={"scores": [1, 2, 3], "weights": [0.1, 0.5, 0.9]},
        ),
        BioCypherNode(
            node_id="i2",
            node_label="post translational interaction",
            properties={"scores": [4, 5, 6], "weights": [0.2, 0.6, 1.0]},
        ),
    ]

    passed = bw._write_node_data(nodes, batch_size=int(1e4))

    csv_path = os.path.join(
        bw.outdir,
        "PostTranslationalInteraction-part000.csv"
        if bw.file_format != "parquet"
        else "PostTranslationalInteraction-part000.parquet",
    )

    assert passed

    if bw.file_format == "parquet":
        rows = get_parquet_content_as_rows(csv_path)
        assert [1, 2, 3] in rows[0]
        assert [0.1, 0.5, 0.9] in rows[0]
    else:
        with open(csv_path) as f:
            content = f.read()

        assert "1|2|3" in content
        assert "0.1|0.5|0.9" in content

    # Verify that the inferred types in node_property_dict use "int[]" / "float[]"
    # rather than the bare "list" that type(v).__name__ would previously return.
    prop_types = bw.node_property_dict.get("post translational interaction", {})
    assert prop_types.get("scores") == "int[]", (
        f"Expected 'int[]' but got {prop_types.get('scores')!r}; list type inference is broken"
    )
    assert prop_types.get("weights") == "float[]", (
        f"Expected 'float[]' but got {prop_types.get('weights')!r}; list type inference is broken"
    )


@pytest.mark.parametrize("length", [4], scope="module")
def test_write_node_data_from_list_not_compliant_names(monkeypatch, caplog, bw, _get_nodes_non_compliant_names):
    nodes = _get_nodes_non_compliant_names

    def mock_get_ancestors(self, label):
        return ["First level", label]

    monkeypatch.setattr("biocypher._ontology.Ontology.get_ancestors", mock_get_ancestors)

    with caplog.at_level(logging.INFO):
        passed = bw._write_node_data(nodes, batch_size=1e6)
    tmp_path = bw.outdir

    extension = "parquet" if bw.file_format == "parquet" else "csv"
    expected_file_names = [
        f"PatientPerson-part000.{extension}",
        f"$He524lloWor.Ld-part000.{extension}",
    ]
    for file_name in os.listdir(tmp_path):
        assert file_name in expected_file_names
        assert any("Label is not compliant with Neo4j naming rules" in record.message for record in caplog.records)
    assert any(
        "Label does not start with an alphabetic character or with $" in record.message for record in caplog.records
    )
    assert passed


@pytest.mark.parametrize("length", [4], scope="module")
def test_write_node_data_from_gen(bw, _get_nodes):
    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(node_gen(nodes), batch_size=1e6)

    tmp_path = bw.outdir

    protein_file = os.path.join(
        tmp_path,
        "Protein-part000.csv" if bw.file_format != "parquet" else "Protein-part000.parquet",
    )
    micro_rna_file = os.path.join(
        tmp_path,
        "MicroRNA-part000.csv" if bw.file_format != "parquet" else "MicroRNA-part000.parquet",
    )

    assert passed

    if bw.file_format == "parquet":
        protein_rows = get_parquet_content_as_rows(protein_file)
        micro_rna_rows = get_parquet_content_as_rows(micro_rna_file)
        assert protein_rows[0][:-1] == (
            "p1",
            "StringProperty1",
            4.0,
            9606,
            ["gene1", "gene2"],
            "p1",
            "uniprot",
        )
        assert "BiologicalEntity" in protein_rows[0][-1]
        assert micro_rna_rows[0][:-1] == (
            "m1",
            "StringProperty1",
            9606,
            "m1",
            "mirbase",
        )
        assert "ChemicalEntity" in micro_rna_rows[0][-1]
    else:
        with open(protein_file) as f:
            protein = f.read()

        with open(micro_rna_file) as f:
            micro_rna = f.read()

        assert "p1;'StringProperty1';4.0;9606;'gene1|gene2';'p1';'uniprot'" in protein
        assert "BiologicalEntity" in protein
        assert "m1;'StringProperty1';9606;'m1';'mirbase'" in micro_rna
        assert "ChemicalEntity" in micro_rna


def test_write_node_data_from_gen_no_props(bw):
    nodes = []
    number_of_items = 4
    for i in range(number_of_items):
        biocypher_node_protein = BioCypherNode(
            node_id=f"p{i + 1}",
            node_label="protein",
            properties={
                "score": 4 / (i + 1),
                "name": "StringProperty1",
                "taxon": 9606,
                "genes": ["gene1", "gene2"],
            },
        )
        nodes.append(biocypher_node_protein)
        biocypher_node_micro_rna = BioCypherNode(
            node_id=f"m{i + 1}",
            node_label="microRNA",
        )
        nodes.append(biocypher_node_micro_rna)

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(node_gen(nodes), batch_size=1e6)

    tmp_path = bw.outdir
    assert os.path.exists(tmp_path)

    protein_file = os.path.join(
        tmp_path,
        "Protein-part000.csv" if bw.file_format != "parquet" else "Protein-part000.parquet",
    )
    micro_rna_file = os.path.join(
        tmp_path,
        "MicroRNA-part000.csv" if bw.file_format != "parquet" else "MicroRNA-part000.parquet",
    )

    assert passed

    if bw.file_format == "parquet":
        protein_rows = get_parquet_content_as_rows(protein_file)
        micro_rna_rows = get_parquet_content_as_rows(micro_rna_file)
        assert protein_rows[0][:-1] == (
            "p1",
            "StringProperty1",
            4.0,
            9606,
            ["gene1", "gene2"],
            "p1",
            "id",
        )
        assert "BiologicalEntity" in protein_rows[0][-1]
        assert micro_rna_rows[0][:-1] == ("m1", "m1", "id")
        assert "ChemicalEntity" in micro_rna_rows[0][-1]
    else:
        with open(protein_file) as f:
            protein = f.read()

        with open(micro_rna_file) as f:
            micro_rna = f.read()

        assert "p1;'StringProperty1';4.0;9606;'gene1|gene2';'p1';'id'" in protein
        assert "BiologicalEntity" in protein
        assert "m1;'m1';'id'" in micro_rna
        assert "ChemicalEntity" in micro_rna


@pytest.mark.parametrize("length", [int(1e4 + 4)], scope="module")
def test_write_node_data_from_large_gen(bw, _get_nodes):
    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(
        node_gen(nodes),
        batch_size=int(1e4),
    )  # reduce test time

    tmp_path = bw.outdir

    if bw.file_format == "parquet":
        protein_0_rows = get_parquet_content_as_rows(os.path.join(tmp_path, "Protein-part000.parquet"))
        micro_rna_0_rows = get_parquet_content_as_rows(os.path.join(tmp_path, "MicroRNA-part000.parquet"))
        protein_1_rows = get_parquet_content_as_rows(os.path.join(tmp_path, "Protein-part001.parquet"))
        micro_rna_1_rows = get_parquet_content_as_rows(os.path.join(tmp_path, "MicroRNA-part001.parquet"))
        assert len(protein_0_rows) == 1e4
        assert len(micro_rna_0_rows) == 1e4
        assert len(protein_1_rows) == 4
        assert len(micro_rna_1_rows) == 4
    else:
        protein_0_csv = os.path.join(tmp_path, "Protein-part000.csv")
        micro_rna_0_csv = os.path.join(tmp_path, "MicroRNA-part000.csv")
        protein_1_csv = os.path.join(tmp_path, "Protein-part001.csv")
        micro_rna_1_csv = os.path.join(tmp_path, "MicroRNA-part001.csv")

        protein_lines = sum(1 for _ in open(protein_0_csv))
        micro_rna_lines = sum(1 for _ in open(micro_rna_0_csv))
        protein_lines1 = sum(1 for _ in open(protein_1_csv))
        micro_rna_lines1 = sum(1 for _ in open(micro_rna_1_csv))

        assert (
            passed and protein_lines == 1e4 and micro_rna_lines == 1e4 and protein_lines1 == 4 and micro_rna_lines1 == 4
        )


@pytest.mark.parametrize("length", [1], scope="module")
def test_too_many_properties(bw, _get_nodes):
    nodes = _get_nodes

    biocypher_node_1 = BioCypherNode(
        node_id="p0",
        node_label="protein",
        properties={
            "p1": "StringProperty1",
            "p2": "StringProperty2",
            "p3": "StringProperty3",
            "p4": "StringProperty4",
        },
    )
    nodes.append(biocypher_node_1)

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(
        node_gen(nodes),
        batch_size=int(1e4),
    )  # reduce test time

    assert not passed


@pytest.mark.parametrize("length", [1], scope="module")
def test_not_enough_properties(bw, _get_nodes):
    nodes = _get_nodes

    biocypher_node_1 = BioCypherNode(
        node_id="p0",
        node_label="protein",
        properties={"p1": "StringProperty1"},
    )
    nodes.append(biocypher_node_1)

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(
        node_gen(nodes),
        batch_size=int(1e4),
    )  # reduce test time

    tmp_path = bw.outdir

    protein_0_csv = os.path.join(tmp_path, "Protein-part000.csv")

    assert not passed and not isfile(protein_0_csv)


def test_write_none_type_property_and_order_invariance(bw):
    # as introduced by translation using defined properties in
    # schema_config.yaml
    nodes = []

    biocypher_node_protein_1 = BioCypherNode(
        node_id="p1",
        node_label="protein",
        properties={
            "taxon": 9606,
            "score": 1,
            "name": None,
            "genes": None,
        },
    )
    biocypher_node_protein_2 = BioCypherNode(
        node_id="p2",
        node_label="protein",
        properties={
            "name": None,
            "genes": ["gene1", "gene2"],
            "score": 2,
            "taxon": 9606,
        },
    )
    biocypher_node_micro_rna = BioCypherNode(
        node_id="m1",
        node_label="microRNA",
        properties={
            "name": None,
            "taxon": 9606,
        },
    )
    nodes.append(biocypher_node_protein_1)
    nodes.append(biocypher_node_protein_2)
    nodes.append(biocypher_node_micro_rna)

    def node_gen(nodes):
        yield from nodes

    passed = bw._write_node_data(
        node_gen(nodes),
        batch_size=int(1e4),
    )  # reduce test time

    tmp_path = bw.outdir

    protein_0_csv = os.path.join(
        tmp_path,
        "Protein-part000.csv" if bw.file_format != "parquet" else "Protein-part000.parquet",
    )

    assert passed

    if bw.file_format == "parquet":
        rows = get_parquet_content_as_rows(protein_0_csv)
        assert len(rows) == 2
        assert rows[0][:-1] == ("p1", None, 1, 9606, None, "p1", "id")
        assert "BiologicalEntity" in rows[0][-1]
    else:
        with open(protein_0_csv) as f:
            protein = f.read()

        assert "p1;;1;9606;;'p1';'id'" in protein
        assert "BiologicalEntity" in protein


@pytest.mark.parametrize("length", [int(1e4)], scope="module")
def test_accidental_exact_batch_size(bw, _get_nodes):
    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    passed = bw.write_nodes(
        node_gen(nodes),
        batch_size=int(1e4),
    )  # reduce test time

    tmp_path = bw.outdir

    if bw.file_format == "parquet":
        protein_0_rows = get_parquet_content_as_rows(os.path.join(tmp_path, "Protein-part000.parquet"))
        micro_rna_0_rows = get_parquet_content_as_rows(os.path.join(tmp_path, "MicroRNA-part000.parquet"))

        protein_header_csv = os.path.join(tmp_path, "Protein-header.csv")
        micro_rna_header_csv = os.path.join(tmp_path, "MicroRNA-header.csv")

        with open(protein_header_csv) as f:
            protein = f.read()
        with open(micro_rna_header_csv) as f:
            micro_rna = f.read()

        assert passed
        assert len(protein_0_rows) == 1e4
        assert len(micro_rna_0_rows) == 1e4
        assert not isfile(os.path.join(tmp_path, "Protein-part001.parquet"))
        assert not isfile(os.path.join(tmp_path, "MicroRNA-part001.parquet"))
        assert protein == ":ID;name;score:double;taxon:long;genes;id;preferred_id;:LABEL"
        assert micro_rna == ":ID;name;taxon:long;id;preferred_id;:LABEL"
    else:
        protein_0_csv = os.path.join(tmp_path, "Protein-part000.csv")
        micro_rna_0_csv = os.path.join(tmp_path, "MicroRNA-part000.csv")
        protein_1_csv = os.path.join(tmp_path, "Protein-part001.csv")
        micro_rna_1_csv = os.path.join(tmp_path, "MicroRNA-part001.csv")

        protein_lines = sum(1 for _ in open(protein_0_csv))
        micro_rna_lines = sum(1 for _ in open(micro_rna_0_csv))

        protein_header_csv = os.path.join(tmp_path, "Protein-header.csv")
        micro_rna_header_csv = os.path.join(tmp_path, "MicroRNA-header.csv")

        with open(protein_header_csv) as f:
            protein = f.read()
        with open(micro_rna_header_csv) as f:
            micro_rna = f.read()

        assert (
            passed
            and protein_lines == 1e4
            and micro_rna_lines == 1e4
            and not isfile(protein_1_csv)
            and not isfile(micro_rna_1_csv)
            and protein == ":ID;name;score:double;taxon:long;genes:string[];id;preferred_id;:LABEL"
            and micro_rna == ":ID;name;taxon:long;id;preferred_id;:LABEL"
        )


@pytest.mark.parametrize("length", [4], scope="module")
def test_write_edge_data_from_gen(bw, _get_edges):
    edges = _get_edges

    def edge_gen(edges):
        yield from edges

    passed = bw._write_edge_data(edge_gen(edges), batch_size=int(1e4))

    tmp_path = bw.outdir

    pid_file = os.path.join(
        tmp_path,
        "PERTURBED_IN_DISEASE-part000.csv" if bw.file_format != "parquet" else "PERTURBED_IN_DISEASE-part000.parquet",
    )
    imi_file = os.path.join(
        tmp_path,
        "Is_Mutated_In-part000.csv" if bw.file_format != "parquet" else "Is_Mutated_In-part000.parquet",
    )

    assert passed

    if bw.file_format == "parquet":
        pid_rows = get_parquet_content_as_rows(pid_file)
        imi_rows = get_parquet_content_as_rows(imi_file)
        assert ("p0", "prel0", "T253", 4, "p1", "PERTURBED_IN_DISEASE") in pid_rows
        assert ("p1", "prel1", "T253", 4, "p2", "PERTURBED_IN_DISEASE") in pid_rows
        assert ("m0", "mrel0", "3-UTR", 1, "p1", "Is_Mutated_In") in imi_rows
        assert ("m1", "mrel1", "3-UTR", 1, "p2", "Is_Mutated_In") in imi_rows
    else:
        with open(pid_file) as f:
            perturbed_in_disease = f.read()
        with open(imi_file) as f:
            is_mutated_in = f.read()

        assert "p0;" in perturbed_in_disease
        assert "prel0;" in perturbed_in_disease
        assert "'T253';" in perturbed_in_disease
        assert "4;" in perturbed_in_disease
        assert "p1;" in perturbed_in_disease
        assert "PERTURBED_IN_DISEASE" in perturbed_in_disease
        assert "p1;" in perturbed_in_disease
        assert "prel1;" in perturbed_in_disease
        assert "'T253';" in perturbed_in_disease
        assert "4;" in perturbed_in_disease
        assert "p2;" in perturbed_in_disease
        assert "PERTURBED_IN_DISEASE" in perturbed_in_disease
        assert "\n" in perturbed_in_disease
        assert "m0;" in is_mutated_in
        assert "mrel0;" in is_mutated_in
        assert "'3-UTR';" in is_mutated_in
        assert "1;" in is_mutated_in
        assert "p1;" in is_mutated_in
        assert "Is_Mutated_In" in is_mutated_in
        assert "m1;" in is_mutated_in
        assert "mrel1;" in is_mutated_in
        assert "'3-UTR';" in is_mutated_in
        assert "1;" in is_mutated_in
        assert "p2;" in is_mutated_in
        assert "Is_Mutated_In" in is_mutated_in
        assert "\n" in is_mutated_in


@pytest.mark.parametrize("length", [int(1e4 + 4)], scope="module")
def test_write_edge_data_from_large_gen(bw, _get_edges):
    edges = _get_edges

    def edge_gen(edges):
        yield from edges

    passed = bw._write_edge_data(edge_gen(edges), batch_size=int(1e4))

    tmp_path = bw.outdir

    perturbed_in_disease_data_0_file = os.path.join(
        tmp_path,
        "PERTURBED_IN_DISEASE-part000.csv" if bw.file_format != "parquet" else "PERTURBED_IN_DISEASE-part000.parquet",
    )
    is_mutated_in_0_file = os.path.join(
        tmp_path,
        "Is_Mutated_In-part000.csv" if bw.file_format != "parquet" else "Is_Mutated_In-part000.parquet",
    )
    perturbed_in_disease_data_1_file = os.path.join(
        tmp_path,
        "PERTURBED_IN_DISEASE-part001.csv" if bw.file_format != "parquet" else "PERTURBED_IN_DISEASE-part001.parquet",
    )
    is_mutated_in_1_file = os.path.join(
        tmp_path,
        "Is_Mutated_In-part001.csv" if bw.file_format != "parquet" else "Is_Mutated_In-part001.parquet",
    )

    if bw.file_format == "parquet":
        perturbed_in_disease_data_0 = len(get_parquet_content_as_rows(perturbed_in_disease_data_0_file))
        is_mutated_in_0 = len(get_parquet_content_as_rows(is_mutated_in_0_file))
        perturbed_in_disease_data_1 = len(get_parquet_content_as_rows(perturbed_in_disease_data_1_file))
        is_mutated_in_1 = len(get_parquet_content_as_rows(is_mutated_in_1_file))
    else:
        perturbed_in_disease_data_0 = sum(1 for _ in open(perturbed_in_disease_data_0_file))
        is_mutated_in_0 = sum(1 for _ in open(is_mutated_in_0_file))
        perturbed_in_disease_data_1 = sum(1 for _ in open(perturbed_in_disease_data_1_file))
        is_mutated_in_1 = sum(1 for _ in open(is_mutated_in_1_file))

    assert (
        passed
        and perturbed_in_disease_data_0 == 1e4
        and is_mutated_in_0 == 1e4
        and perturbed_in_disease_data_1 == 4
        and is_mutated_in_1 == 4
    )


@pytest.mark.parametrize("length", [4], scope="module")
def test_write_edge_data_from_list(bw, _get_edges):
    edges = _get_edges

    passed = bw._write_edge_data(edges, batch_size=int(1e4))

    tmp_path = bw.outdir

    pid_file = os.path.join(
        tmp_path,
        "PERTURBED_IN_DISEASE-part000.csv" if bw.file_format != "parquet" else "PERTURBED_IN_DISEASE-part000.parquet",
    )
    imi_file = os.path.join(
        tmp_path,
        "Is_Mutated_In-part000.csv" if bw.file_format != "parquet" else "Is_Mutated_In-part000.parquet",
    )

    assert passed

    if bw.file_format == "parquet":
        pid_rows = get_parquet_content_as_rows(pid_file)
        imi_rows = get_parquet_content_as_rows(imi_file)
        assert ("p0", "prel0", "T253", 4, "p1", "PERTURBED_IN_DISEASE") in pid_rows
        assert ("m0", "mrel0", "3-UTR", 1, "p1", "Is_Mutated_In") in imi_rows
        assert ("m1", "mrel1", "3-UTR", 1, "p2", "Is_Mutated_In") in imi_rows
    else:
        with open(pid_file) as f:
            perturbed_in_disease = f.read()
        with open(imi_file) as f:
            is_mutated_in = f.read()

        assert "p0;" in perturbed_in_disease
        assert "prel0;" in perturbed_in_disease
        assert "'T253';" in perturbed_in_disease
        assert "4;" in perturbed_in_disease
        assert "p1;" in perturbed_in_disease
        assert "PERTURBED_IN_DISEASE" in perturbed_in_disease
        assert "\n" in perturbed_in_disease
        assert "p2;'PERTURBED_IN_DISEASE'" in perturbed_in_disease
        assert "m0;" in is_mutated_in
        assert "mrel0;" in is_mutated_in
        assert "'3-UTR';" in is_mutated_in
        assert "1;" in is_mutated_in
        assert "p1;" in is_mutated_in
        assert "Is_Mutated_In" in is_mutated_in
        assert "m1;" in is_mutated_in
        assert "\n" in is_mutated_in


@pytest.mark.parametrize("length", [4], scope="module")
def test_write_edge_data_from_list_non_compliant_names(monkeypatch, caplog, bw, _get_edges_non_compliant_names):
    edges = _get_edges_non_compliant_names

    def mock_get_ancestors(self, label):
        return ["First level", label]

    monkeypatch.setattr("biocypher._ontology.Ontology.get_ancestors", mock_get_ancestors)

    with caplog.at_level(logging.INFO):
        passed = bw._write_edge_data(edges, batch_size=int(1e4))
    tmp_path = bw.outdir

    extension = "parquet" if bw.file_format == "parquet" else "csv"
    expected_file_names = [
        f"Is_Mutated_In-part000.{extension}",
        f"CompliantEdge-part000.{extension}",
    ]
    for file_name in os.listdir(tmp_path):
        assert file_name in expected_file_names
    assert any("Label is not compliant with Neo4j naming rules" in record.message for record in caplog.records)
    assert any(
        "Label does not start with an alphabetic character or with $" in record.message for record in caplog.records
    )
    assert passed


@pytest.mark.parametrize("length", [4], scope="module")
def test_write_edge_id_optional(bw, _get_edges):
    edges = _get_edges

    # add phosphorylation edges
    for i in range(4):
        edge_1 = BioCypherEdge(
            relationship_id=f"phos{i}",  # should be ignored
            source_id=f"p{i}",
            target_id=f"p{i + 1}",
            relationship_label="phosphorylation",
        )
        edges.append(edge_1)

    passed = bw.write_edges(edges, batch_size=int(1e4))
    assert passed

    tmp_path = bw.outdir

    pid_file = os.path.join(
        tmp_path,
        "PERTURBED_IN_DISEASE-part000.csv" if bw.file_format != "parquet" else "PERTURBED_IN_DISEASE-part000.parquet",
    )
    phos_file = os.path.join(
        tmp_path,
        "Phosphorylation-part000.csv" if bw.file_format != "parquet" else "Phosphorylation-part000.parquet",
    )

    if bw.file_format == "parquet":
        pid_rows = get_parquet_content_as_rows(pid_file)
        phos_rows = get_parquet_content_as_rows(phos_file)
        assert "prel0" in pid_rows[0]
        assert "phos0" not in phos_rows[0]
    else:
        with open(pid_file) as f:
            perturbed_in_disease = f.read()
        with open(phos_file) as f:
            phosphorylation = f.read()

        assert "prel0;" in perturbed_in_disease
        assert "phos1;" not in phosphorylation

    # Check headers regardless of format
    perturbed_in_disease_header = os.path.join(tmp_path, "PERTURBED_IN_DISEASE-header.csv")
    phosphorylation_header = os.path.join(tmp_path, "Phosphorylation-header.csv")

    with open(perturbed_in_disease_header) as f:
        perturbed_in_disease_header = f.read()
    with open(phosphorylation_header) as f:
        phosphorylation_header = f.read()

    assert "id;" in perturbed_in_disease_header
    assert "id;" not in phosphorylation_header


def test_write_edge_data_from_list_no_props(bw):
    number_of_items = 4
    edges = []
    for i in range(number_of_items):
        edge_1 = BioCypherEdge(
            source_id=f"p{i}",
            target_id=f"p{i + 1}",
            relationship_label="PERTURBED_IN_DISEASE",
        )
        edges.append(edge_1)
        edge_2 = BioCypherEdge(
            source_id=f"m{i}",
            target_id=f"p{i + 1}",
            relationship_label="Is_Mutated_In",
        )
        edges.append(edge_2)

    passed = bw._write_edge_data(edges, batch_size=int(1e4))

    tmp_path = bw.outdir

    pid_file = os.path.join(
        tmp_path,
        "PERTURBED_IN_DISEASE-part000.csv" if bw.file_format != "parquet" else "PERTURBED_IN_DISEASE-part000.parquet",
    )
    imi_file = os.path.join(
        tmp_path,
        "Is_Mutated_In-part000.csv" if bw.file_format != "parquet" else "Is_Mutated_In-part000.parquet",
    )

    assert passed

    if bw.file_format == "parquet":
        pid_rows = get_parquet_content_as_rows(pid_file)
        imi_rows = get_parquet_content_as_rows(imi_file)
        assert pid_rows[0][:-1] == ("p0", "", "p1")
        assert "PERTURBED_IN_DISEASE" in pid_rows[0][-1]
        assert pid_rows[1][:-1] == ("p1", "", "p2")
        assert "PERTURBED_IN_DISEASE" in pid_rows[1][-1]
        assert imi_rows[0][:-1] == ("m0", "", "p1")
        assert "Is_Mutated_In" in imi_rows[0][-1]
        assert imi_rows[1][:-1] == ("m1", "", "p2")
        assert "Is_Mutated_In" in imi_rows[1][-1]
    else:
        with open(pid_file) as f:
            perturbed_in_disease = f.read()
        with open(imi_file) as f:
            is_mutated_in = f.read()

        assert "p0;" in perturbed_in_disease
        assert "p1;" in perturbed_in_disease
        assert "PERTURBED_IN_DISEASE" in perturbed_in_disease
        assert "p1;" in perturbed_in_disease
        assert "p2;" in perturbed_in_disease
        assert "PERTURBED_IN_DISEASE" in perturbed_in_disease
        assert "\n" in perturbed_in_disease
        assert "m0;" in is_mutated_in
        assert "p1;" in is_mutated_in
        assert "Is_Mutated_In" in is_mutated_in
        assert "m1;" in is_mutated_in
        assert "p2;" in is_mutated_in
        assert "Is_Mutated_In" in is_mutated_in
        assert "\n" in is_mutated_in


def test_write_edge_data_boolean_properties(bw_csv):
    """Boolean properties must be written as lowercase 'true'/'false' for Neo4j admin import."""
    edges = [
        BioCypherEdge(
            relationship_id="gg1",
            source_id="g1",
            target_id="g2",
            relationship_label="gene to gene association",
            properties={"directional": True, "curated": False, "score": 0.9},
        ),
        BioCypherEdge(
            relationship_id="gg2",
            source_id="g3",
            target_id="g4",
            relationship_label="gene to gene association",
            properties={"directional": False, "curated": True, "score": 0.5},
        ),
    ]

    passed = bw_csv._write_edge_data(edges, batch_size=int(1e4))

    tmp_path = bw_csv.outdir
    gene_gene_csv = os.path.join(tmp_path, "GeneToGeneAssociation-part000.csv")

    with open(gene_gene_csv) as f:
        gene_gene = f.read()

    assert passed
    assert "true" in gene_gene
    assert "false" in gene_gene
    assert "True" not in gene_gene
    assert "False" not in gene_gene


def test_write_edge_data_non_string_list_properties(bw):
    """List properties on edges must infer typed array annotations, not bare 'list'."""
    edges = [
        BioCypherEdge(
            relationship_id="ph1",
            source_id="p1",
            target_id="p2",
            relationship_label="phosphorylation",
            properties={"sites": ["S100", "T200"], "scores": [0.8, 0.95]},
        ),
        BioCypherEdge(
            relationship_id="ph2",
            source_id="p3",
            target_id="p4",
            relationship_label="phosphorylation",
            properties={"sites": ["Y50"], "scores": [0.6]},
        ),
    ]

    passed = bw._write_edge_data(edges, batch_size=int(1e4))

    assert passed

    if bw.file_format == "parquet":
        # For parquet, data is stored as native lists
        phosphorylation_file = os.path.join(bw.outdir, "Phosphorylation-part000.parquet")
        parquet_data = get_parquet_content_as_rows(phosphorylation_file)
        assert parquet_data[0][1:3] == (["S100", "T200"], [0.8, 0.95])
        assert parquet_data[1][1:3] == (["Y50"], [0.6])
    else:
        phosphorylation_file = os.path.join(bw.outdir, "Phosphorylation-part000.csv")
        with open(phosphorylation_file) as f:
            content = f.read()
            # CSV should have pipe-delimited lists
            assert "S100" in content or "Y50" in content
            assert "0.8" in content or "0.6" in content

    # Type inference should work for both formats
    prop_types = bw.edge_property_dict.get("phosphorylation", {})
    assert prop_types.get("sites") == "str[]", (
        f"Expected 'str[]' but got {prop_types.get('sites')!r}; list type inference is broken for edges"
    )
    assert prop_types.get("scores") == "float[]", (
        f"Expected 'float[]' but got {prop_types.get('scores')!r}; list type inference is broken for edges"
    )


@pytest.mark.parametrize("length", [8], scope="module")
def test_write_edge_data_headers_import_call(bw, _get_nodes, _get_edges):
    edges = _get_edges

    nodes = _get_nodes

    def edge_gen1(edges):
        yield from edges[:4]

    def edge_gen2(edges):
        yield from edges[4:]

    passed = bw.write_edges(edge_gen1(edges))
    assert passed

    passed = bw.write_edges(edge_gen2(edges))
    assert passed

    passed = bw.write_nodes(nodes)
    assert passed

    bw.write_import_call()

    tmp_path = bw.outdir

    perturbed_in_disease_csv = os.path.join(tmp_path, "PERTURBED_IN_DISEASE-header.csv")
    is_mutated_in_csv = os.path.join(tmp_path, "Is_Mutated_In-header.csv")

    # Determine import call script name based on OS
    if sys.platform.startswith("win"):
        call_csv = os.path.join(tmp_path, "neo4j-admin-import-call.ps1")
    else:
        call_csv = os.path.join(tmp_path, "neo4j-admin-import-call.sh")

    with open(perturbed_in_disease_csv) as f:
        perturbed_in_disease = f.read()
    with open(is_mutated_in_csv) as f:
        is_mutated_in = f.read()
    with open(call_csv) as f:
        call = f.read()

    assert perturbed_in_disease == ":START_ID;id;residue;level:long;:END_ID;:TYPE"
    assert is_mutated_in == ":START_ID;id;site;confidence:long;:END_ID;:TYPE"

    assert "neo4j-admin" in call
    assert "import" in call
    assert '--delimiter=";"' in call
    assert '--nodes="' in call
    assert "PERTURBED_IN_DISEASE" in call
    assert "Is_Mutated_In" in call


@pytest.mark.parametrize("length", [4], scope="module")
def test_write_duplicate_edges(bw, _get_edges):
    edges = _get_edges
    edges.append(edges[0])

    passed = bw.write_edges(edges)

    tmp_path = bw.outdir

    if bw.file_format == "parquet":
        perturbed_in_disease_file = os.path.join(tmp_path, "PERTURBED_IN_DISEASE-part000.parquet")
        is_mutated_in_file = os.path.join(tmp_path, "Is_Mutated_In-part000.parquet")

        pid_data = get_parquet_content_as_rows(perturbed_in_disease_file)
        imi_data = get_parquet_content_as_rows(is_mutated_in_file)

        # Count entries in parquet (number of rows in first column)
        perturbed_in_disease = len(pid_data)
        is_mutated_in = len(imi_data)
    else:
        perturbed_in_disease_csv = os.path.join(tmp_path, "PERTURBED_IN_DISEASE-part000.csv")
        is_mutated_in_csv = os.path.join(tmp_path, "Is_Mutated_In-part000.csv")

        perturbed_in_disease = sum(1 for _ in open(perturbed_in_disease_csv))
        is_mutated_in = sum(1 for _ in open(is_mutated_in_csv))

    assert passed and perturbed_in_disease == 4 and is_mutated_in == 4


@pytest.mark.parametrize("length", [4], scope="module")
def test_write_edges_all_duplicates(bw, _get_edges):
    edges = _get_edges

    first = bw.write_edges(edges)
    second = bw.write_edges(edges)

    assert first
    assert second, "all-deduplicated write_edges call should succeed, not error"


@pytest.mark.parametrize("length", [4], scope="module")
def test_BioCypherRelAsNode_implementation(bw, _get_rel_as_nodes):
    trips = _get_rel_as_nodes

    def gen(lis):
        yield from lis

    passed = bw.write_edges(gen(trips))

    tmp_path = bw.outdir

    if bw.file_format == "parquet":
        is_source_of_file = os.path.join(tmp_path, "IS_SOURCE_OF-part000.parquet")
        is_target_of_file = os.path.join(tmp_path, "IS_TARGET_OF-part000.parquet")
        post_translational_interaction_file = os.path.join(tmp_path, "PostTranslationalInteraction-part000.parquet")

        is_source_of_data = get_parquet_content_as_rows(is_source_of_file)
        is_target_of_data = get_parquet_content_as_rows(is_target_of_file)
        post_translational_interaction_data = get_parquet_content_as_rows(post_translational_interaction_file)

        assert is_source_of_data[0] == ("i1", "p1", "IS_SOURCE_OF")
        assert is_target_of_data[0] == ("i0", "p2", "IS_TARGET_OF")
        assert post_translational_interaction_data[0][:-1] == ("i1", True, -1, "i1", "id")
        assert "Association" in post_translational_interaction_data[0][-1]
    else:
        is_source_of_csv = os.path.join(tmp_path, "IS_SOURCE_OF-part000.csv")
        is_target_of_csv = os.path.join(tmp_path, "IS_TARGET_OF-part000.csv")
        post_translational_interaction_csv = os.path.join(tmp_path, "PostTranslationalInteraction-part000.csv")

        with open(is_source_of_csv) as f:
            is_source_of = f.read()
        with open(is_target_of_csv) as f:
            is_target_of = f.read()
        with open(post_translational_interaction_csv) as f:
            post_translational_interaction = f.read()

        assert "i1;" in is_source_of
        assert "p1;" in is_source_of
        assert "IS_SOURCE_OF" in is_source_of
        assert "\n" in is_source_of
        assert "i0;" in is_target_of
        assert "p2;" in is_target_of
        assert "IS_TARGET_OF" in is_target_of
        assert "\n" in is_target_of
        assert "i1;true;-1;'i1';'id'" in post_translational_interaction
        assert "Association" in post_translational_interaction
        assert "\n" in post_translational_interaction

    assert passed


@pytest.mark.parametrize("length", [8], scope="module")
def test_RelAsNode_overwrite_behaviour(bw, _get_rel_as_nodes):
    # if rel as node is called from successive write calls, SOURCE_OF,
    # TARGET_OF, and PART_OF should be continued, not overwritten
    trips = _get_rel_as_nodes

    def gen1(lis):
        yield from lis[:5]

    def gen2(lis):
        yield from lis[5:]

    passed1 = bw.write_edges(gen1(trips))
    passed2 = bw.write_edges(gen2(trips))

    tmp_path = bw.outdir

    if bw.file_format == "parquet":
        is_source_of_file = os.path.join(tmp_path, "IS_SOURCE_OF-part001.parquet")
    else:
        is_source_of_file = os.path.join(tmp_path, "IS_SOURCE_OF-part001.csv")

    assert passed1 and passed2 and isfile(is_source_of_file)


def test_write_mixed_edges(bw):
    mixed = []
    number_of_items = 4
    for i in range(number_of_items):
        edge_3 = BioCypherEdge(
            source_id=f"p{i + 1}",
            target_id=f"p{i + 1}",
            relationship_label="PERTURBED_IN_DISEASE",
        )
        mixed.append(edge_3)

        node = BioCypherNode(
            f"i{i + 1}",
            "post translational interaction",
        )
        edge_1 = BioCypherEdge(
            source_id=f"i{i + 1}",
            target_id=f"p{i + 1}",
            relationship_label="IS_SOURCE_OF",
        )
        edge_2 = BioCypherEdge(
            source_id=f"i{i}",
            target_id=f"p{i + 2}",
            relationship_label="IS_TARGET_OF",
        )
        mixed.append(BioCypherRelAsNode(node, edge_1, edge_2))

    def gen(lis):
        yield from lis

    passed = bw.write_edges(gen(mixed))

    tmp_path = bw.outdir

    post_translational_interaction_csv = os.path.join(tmp_path, "PostTranslationalInteraction-header.csv")
    is_source_of_csv = os.path.join(tmp_path, "IS_SOURCE_OF-header.csv")
    is_target_of_csv = os.path.join(tmp_path, "IS_TARGET_OF-header.csv")
    perturbed_in_disease_csv = os.path.join(tmp_path, "PERTURBED_IN_DISEASE-header.csv")

    assert (
        passed
        and os.path.isfile(post_translational_interaction_csv)
        and os.path.isfile(is_source_of_csv)
        and os.path.isfile(is_target_of_csv)
        and os.path.isfile(perturbed_in_disease_csv)
    )


def test_duplicate_id(bw):
    nodes = []

    tmp_path = bw.outdir

    csv = os.path.join(tmp_path, "Protein-part000.csv" if bw.file_format != "parquet" else "Protein-part000.parquet")

    # remove csv file in path
    if os.path.exists(csv):
        os.remove(csv)

    # four proteins, four miRNAs
    for _ in range(2):
        biocypher_node_protein = BioCypherNode(
            node_id="p1",
            node_label="protein",
            properties={
                "name": "StringProperty1",
                "score": 4.32,
                "taxon": 9606,
                "genes": ["gene1", "gene2"],
            },
        )
        nodes.append(biocypher_node_protein)

    passed = bw.write_nodes(nodes)

    assert passed

    if bw.file_format == "parquet":
        rows = get_parquet_content_as_rows(csv)
        assert len(rows) == 1
    else:
        l_lines0 = sum(1 for _ in open(csv))
        assert l_lines0 == 1


def test_write_synonym(bw):
    nodes = []

    tmp_path = bw.outdir

    csv = os.path.join(tmp_path, "Complex-part000.csv" if bw.file_format != "parquet" else "Complex-part000.parquet")

    # remove csv file in path
    if os.path.exists(csv):
        os.remove(csv)
    # four proteins, four miRNAs
    for _ in range(4):
        biocypher_node_protein = BioCypherNode(
            node_id=f"p{_ + 1}",
            node_label="complex",
            properties={
                "name": "StringProperty1",
                "score": 4.32,
                "taxon": 9606,
            },
        )
        nodes.append(biocypher_node_protein)

    passed = bw.write_nodes(nodes)

    assert passed and os.path.exists(csv)

    if bw.file_format == "parquet":
        rows = get_parquet_content_as_rows(csv)
        assert rows[0][:-1] == ("p1", "StringProperty1", 4.32, 9606, "p1", "id")
        assert "Complex" in rows[0][-1]
    else:
        with open(csv) as f:
            complex = f.read()

        assert "p1;'StringProperty1';4.32;9606;'p1';'id'" in complex
        assert "Complex" in complex


def test_write_strict(bw_strict):
    node_1 = BioCypherNode(
        node_id="p1",
        node_label="protein",
        properties={
            "name": "StringProperty1",
            "score": 4.32,
            "taxon": 9606,
            "genes": ["gene1", "gene2"],
            "source": "source1",
            "version": "version1",
            "licence": "licence1",
        },
    )

    passed = bw_strict.write_nodes([node_1])

    assert passed

    tmp_path = bw_strict.outdir

    csv = os.path.join(
        tmp_path,
        "Protein-part000.csv" if bw_strict.file_format != "parquet" else "Protein-part000.parquet",
    )

    if bw_strict.file_format == "parquet":
        rows = get_parquet_content_as_rows(csv)
        assert len(rows) == 1
        assert rows[0][:-1] == (
            "p1",
            "StringProperty1",
            4.32,
            9606,
            ["gene1", "gene2"],
            "p1",
            "id",
            "source1",
            "version1",
            "licence1",
        )
        assert "BiologicalEntity" in rows[0][-1]
    else:
        with open(csv) as f:
            protein = f.read()

        assert "p1;'StringProperty1';4.32;9606;'gene1|gene2';'p1';'id';'source1';'version1';'licence1'" in protein
        assert "BiologicalEntity" in protein


def test_write_strict_edge_does_not_mutate_schema(bw_strict):
    """In strict mode, writing edges must not modify the schema properties dict.

    Previously, `d = cprops` (a reference) was used instead of `d = dict(cprops)`
    (a copy), so strict-mode keys ("source", "version", "licence") were injected
    permanently into the extended_schema on the first write of each edge label.
    """
    schema = bw_strict.translator.ontology.mapping.extended_schema
    original_props = dict(schema["gene to gene association"]["properties"])

    edge = BioCypherEdge(
        source_id="g1",
        target_id="g2",
        relationship_label="gene to gene association",
        properties={"directional": True, "curated": False, "score": 0.9},
    )

    bw_strict._write_edge_data([edge], batch_size=int(1e4))

    mutated_props = schema["gene to gene association"]["properties"]
    assert "source" not in mutated_props, "strict-mode key 'source' was injected into schema"
    assert "version" not in mutated_props, "strict-mode key 'version' was injected into schema"
    assert "licence" not in mutated_props, "strict-mode key 'licence' was injected into schema"
    assert mutated_props == original_props, "schema properties were modified by _write_edge_data"


@pytest.mark.parametrize("length", [4], scope="module")
def test_tab_delimiter(bw_tab, _get_nodes):
    passed = bw_tab.write_nodes(_get_nodes)

    assert passed

    tmp_path = bw_tab.outdir

    header = os.path.join(tmp_path, "Protein-header.csv")

    with open(header) as f:
        protein = f.read()

    assert "\t" in protein

    call = bw_tab._construct_import_call()

    assert '--delimiter="\\t"' in call


def test_check_label_name():
    # Test case 1: label with compliant characters
    assert parse_label("Compliant_Label") == "Compliant_Label"

    # Test case 2: label with non-compliant characters
    assert parse_label("Non@Compl<>i(an)t_Labe#l") == "NonCompliant_Label"

    # Test case 3: label starts with a number
    assert parse_label("15Invalid_Label") == "Invalid_Label"

    # Test case 4: label starts with a non-alphanumeric character
    assert parse_label("@Invalid_Label") == "Invalid_Label"

    # Additional test case: label with dot (for class hierarchy of BioCypher)
    assert parse_label("valid.label") == "valid.label"

    # Additional test case: label with dot and non-compliant characters
    assert parse_label("In.valid.Label@1") == "In.valid.Label1"

    # Test case: label contains only non-compliant characters (would previously crash with IndexError)
    assert parse_label("@#^&") == ""


def make_labels(bw, order):
    bw.node_labels_order = order
    bw.edge_labels_order = order
    nodes = [
        BioCypherNode(
            node_id="agpl:0001",
            node_label="altered gene product level",
            properties={},
        ),
    ]

    passed = bw.write_nodes(nodes)
    assert passed
    tmp_path = bw.outdir

    labels = []

    if bw.file_format == "parquet":
        f_parquet = os.path.join(tmp_path, "AlteredGeneProductLevel-part000.parquet")
        parquet_data = get_parquet_content_as_rows(f_parquet)
        label_strings = parquet_data[0][-1]
        if isinstance(label_strings, str):
            lbls = [i.strip("'") for i in label_strings.split("|")]
            if lbls:
                labels.append(lbls)
    else:
        files = ["AlteredGeneProductLevel-part000.csv"]
        lines = []
        for f in files:
            f_csv = os.path.join(tmp_path, f)
            with open(f_csv) as fd:
                lines += fd.readlines()

        for line in lines:
            lbl = line.strip().split(";")[-1].strip("'")
            lbls = [i.strip("'") for i in lbl.split("|")]
            if lbls:
                labels.append(lbls)

    assert len(labels) > 0
    return labels


def test_labels_order_alpha(bw):
    alpha = make_labels(bw, "Alphabetical")
    for labels in alpha:
        ordered = sorted(labels)
        assert labels == ordered


def test_labels_order_leaves(bw):
    asc = make_labels(bw, "Leaves")
    for labels in asc:
        assert len(labels) == 1
        # No other choice than to test actual values,
        # or else it would mean re-implementing get_ancestors.
        assert labels[0] == "AlteredGeneProductLevel"


def test_labels_order_asc(bw):
    asc = make_labels(bw, "Ascending")
    assert asc[0] == [
        "AlteredGeneProductLevel",
        "FunctionalEffectVariant",
        "SequenceVariant",
        "BiologicalEntity",
        "NamedThing",
        "Entity",
    ]


def test_labels_order_dsc(bw):
    dsc = make_labels(bw, "Descending")
    assert dsc[0] == [
        "Entity",
        "NamedThing",
        "BiologicalEntity",
        "SequenceVariant",
        "FunctionalEffectVariant",
        "AlteredGeneProductLevel",
    ]


def test_powershell_template_structure():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(
        base_dir,
        "..",
        "..",
        "..",
        "..",
        "biocypher",
        "output",
        "templates",
        "powershell_template.ps1",
    )
    template_path = os.path.normpath(template_path)

    with open(template_path, encoding="utf-8") as f:
        content = f.read()

    # Check for Neo4j bin path placeholder and output
    assert "{neo4j_bin_path}" in content
    assert "$NEO4J_BIN_PATH_WINDOWS" in content

    # Check for Neo4j version check placeholder and output
    assert "{neo4j_version_check}" in content
    assert "$version" in content

    # Check for major version extraction
    assert "$major_version" in content
    assert "$major = [int]$major_version" in content

    # Check for v4 and v5 argument placeholders
    assert "{args_neo4j_v4}" in content
    assert "{args_neo4j_v5}" in content

    # Check for conditional logic for version
    assert "if ( $major -lt 5 )" in content
    assert "else" in content

    # Check for import call
    assert 'Invoke-Expression "$NEO4J_BIN_PATH_WINDOWS $args_neo4j"' in content

    # Check for exit code handling
    assert "if ($LASTEXITCODE -eq 0)" in content
    assert "Import completed successfully" in content
    assert "Import failed with exit code $LASTEXITCODE" in content

    # Check for script finished message
    assert "Script finished." in content

    # Optionally, check for all placeholders using regex
    placeholders = re.findall(r"\{[a-zA-Z0-9_]+\}", content)
    expected_placeholders = {
        "{neo4j_bin_path}",
        "{neo4j_version_check}",
        "{args_neo4j_v4}",
        "{args_neo4j_v5}",
    }
    assert expected_placeholders.issubset(set(placeholders))
