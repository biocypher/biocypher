from biocypher._mapping import OntologyMapping


def test_to_graphql_schema_generates_node_and_relationship():
    mapping = OntologyMapping()

    mapping.extended_schema = {
        "protein": {
            "represented_as": "node",
            "preferred_id": "uniprot",
            "properties": {
                "name": "str",
                "score": "float",
            },
        },
        "gene": {
            "represented_as": "node",
            "preferred_id": "ensembl",
            "properties": {
                "symbol": "str",
            },
        },
        "interacts with": {
            "represented_as": "edge",
            "source": "protein",
            "target": "gene",
            "properties": {
                "evidence": "str",
            },
        },
    }

    graphql_schema = mapping.to_graphql_schema()

    assert 'type Protein @node(labels: ["Protein"])' in graphql_schema
    assert "uniprotId: ID!" in graphql_schema
    assert "name: String" in graphql_schema
    assert "score: Float" in graphql_schema

    assert 'type Gene @node(labels: ["Gene"])' in graphql_schema
    assert "ensemblId: ID!" in graphql_schema
    assert "symbol: String" in graphql_schema

    assert '@relationship(type: "INTERACTS_WITH", direction: OUT' in graphql_schema
    assert "interface InteractsWithProps @relationshipProperties" in graphql_schema
    assert "evidence: String" in graphql_schema