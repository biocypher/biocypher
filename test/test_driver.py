from biocypher.driver import Driver
from biocypher.create import BioCypherNode, BioCypherEdge
from neo4j.work.summary import ResultSummary
import pytest


@pytest.fixture
def driver():
    # neo4j database needs to be running!
    d = Driver(version=False)
    # create single node in case of empty DB for testing?
    # d.add_biocypher_nodes(BioCypherNode("TestID", "Test"))
    yield d

    # teardown
    d.query("MATCH (n:Test)" "DETACH DELETE n")
    d.query("MATCH (n:Int1)" "DETACH DELETE n")
    d.query("MATCH (n:Int2)" "DETACH DELETE n")

    # to deal with merging on non-existing nodes
    # see test_add_single_biocypher_edge_missing_nodes()
    d.query("MATCH (n2) WHERE n2.id = 'src'" "DETACH DELETE n2")
    d.query("MATCH (n3) WHERE n3.id = 'tar'" "DETACH DELETE n3")
    d.close()


def test_connect_to_db(driver):

    assert driver.db_exists()


def test_explain(driver):
    query = "MATCH (n) WITH n LIMIT 25 MATCH (n)--(m)--(f) RETURN n, m, f"
    e = driver.explain(query)
    t = e[0]

    assert t[0] == "ProduceResults@" + driver.current_db


def test_profile(driver):
    query = "MATCH (n) RETURN n LIMIT 100"
    p = driver.profile(query)
    t = p[0]

    assert t[0] == "ProduceResults@" + driver.current_db


def test_add_invalid_biocypher_node(driver):
    # neo4j database needs to be running!
    with pytest.raises(Exception):
        driver.add_biocypher_nodes(1)


def test_add_single_biocypher_node(driver):
    # neo4j database needs to be running!
    n = BioCypherNode(node_id="test_id1", node_label="Test")
    driver.add_biocypher_nodes(n)
    r, summary = driver.query(
        "MATCH (n:Test) " "WITH n, n.id AS id " "RETURN id "
    )
    assert r[0]["id"] == "test_id1"


def test_add_biocypher_node_list(driver):
    # neo4j database needs to be running!
    n1 = BioCypherNode(node_id="test_id1", node_label="Test")
    n2 = BioCypherNode(node_id="test_id2", node_label="Test")
    driver.add_biocypher_nodes([n1, n2])
    r, summary = driver.query(
        "MATCH (n:Test) " "WITH n, n.id AS id " "RETURN id "
    )
    assert r[0]["id"] == "test_id1" and r[1]["id"] == "test_id2"


def test_add_biocypher_node_generator(driver):
    # neo4j database needs to be running!
    # generator
    def gen(nodes):
        for g in nodes:
            yield BioCypherNode(g[0], g[1])

    g = gen([("test_id1", "Test"), ("test_id2", "Test")])

    driver.add_biocypher_nodes(g)
    r, summary = driver.query(
        "MATCH (n:Test) " "WITH n, n.id AS id " "RETURN id "
    )
    assert r[0]["id"] == "test_id1" and r[1]["id"] == "test_id2"


def test_add_invalid_biocypher_edge(driver):
    # neo4j database needs to be running!
    with pytest.raises(Exception):
        driver.add_biocypher_edges(1)


def test_add_single_biocypher_edge_explicit_node_creation(driver):
    # neo4j database needs to be running!
    n1 = BioCypherNode("src", "Test")
    n2 = BioCypherNode("tar", "Test")
    driver.add_biocypher_nodes([n1, n2])

    e = BioCypherEdge("src", "tar", "Test")
    driver.add_biocypher_edges(e)
    r, summary = driver.query(
        "MATCH (n1)-[r:Test]->(n2) "
        "WITH n1, n2, n1.id AS id1, n2.id AS id2, type(r) AS label "
        "RETURN id1, id2, label"
    )
    assert (
        r[0]["id1"] == "src"
        and r[0]["id2"] == "tar"
        and r[0]["label"] == "Test"
    )


def test_add_single_biocypher_edge_missing_nodes(driver):
    # neo4j database needs to be running!
    # merging on non-existing nodes creates them without labels; what is
    # the desired behaviour here? do we only want to MATCH?

    e = BioCypherEdge("src", "tar", "Test")
    driver.add_biocypher_edges(e)
    r, summary = driver.query(
        "MATCH (n1)-[r:Test]->(n2) "
        "WITH n1, n2, n1.id AS id1, n2.id AS id2, type(r) AS label "
        "RETURN id1, id2, label"
    )
    assert (
        r[0]["id1"] == "src"
        and r[0]["id2"] == "tar"
        and r[0]["label"] == "Test"
    )


def test_add_biocypher_edge_list(driver):
    # neo4j database needs to be running!
    n1 = BioCypherNode("src", "Test")
    n2 = BioCypherNode("tar1", "Test")
    n3 = BioCypherNode("tar2", "Test")
    driver.add_biocypher_nodes([n1, n2, n3])

    # edge list
    e1 = BioCypherEdge("src", "tar1", "Test1")
    e2 = BioCypherEdge("src", "tar2", "Test2")
    driver.add_biocypher_edges([e1, e2])
    r, summary = driver.query(
        "MATCH (n3)<-[r2:Test2]-(n1)-[r1:Test1]->(n2) "
        "WITH n1, n2, n3, n1.id AS id1, n2.id AS id2, n3.id AS id3, "
        "type(r1) AS label1, type(r2) AS label2 "
        "RETURN id1, id2, id3, label1, label2"
    )
    assert (
        r[0]["id1"] == "src"
        and r[0]["id2"] == "tar1"
        and r[0]["id3"] == "tar2"
        and r[0]["label1"] == "Test1"
        and r[0]["label2"] == "Test2"
    )


def test_add_biocypher_edge_generator(driver):
    # neo4j database needs to be running!
    n1 = BioCypherNode("src", "Test")
    n2 = BioCypherNode("tar1", "Test")
    n3 = BioCypherNode("tar2", "Test")
    driver.add_biocypher_nodes([n1, n2, n3])

    # generator
    def gen(edges):
        for e in edges:
            yield BioCypherEdge(
                e.get_source_id(), e.get_target_id(), e.get_label()
            )

    # edge list
    e1 = BioCypherEdge("src", "tar1", "Test1")
    e2 = BioCypherEdge("src", "tar2", "Test2")
    g = gen([e1, e2])

    driver.add_biocypher_edges(g)
    r, summary = driver.query(
        "MATCH (n3)<-[r2:Test2]-(n1)-[r1:Test1]->(n2) "
        "WITH n1, n2, n3, n1.id AS id1, n2.id AS id2, n3.id AS id3, "
        "type(r1) AS label1, type(r2) AS label2 "
        "RETURN id1, id2, id3, label1, label2"
    )
    assert (
        r[0]["id1"] == "src"
        and r[0]["id2"] == "tar1"
        and r[0]["id3"] == "tar2"
        and r[0]["label1"] == "Test1"
        and r[0]["label2"] == "Test2"
    )


def test_add_biocypher_interaction_as_node_tuples(driver):
    # neo4j database needs to be running!
    i1 = BioCypherNode("int1", "Int1")
    i2 = BioCypherNode("int2", "Int2")
    driver.add_biocypher_nodes([i1, i2])
    e1 = BioCypherEdge("src", "int1", "is_source_of")
    e2 = BioCypherEdge("tar", "int1", "is_target_of")
    e3 = BioCypherEdge("src", "int2", "is_source_of")
    e4 = BioCypherEdge("tar", "int2", "is_target_of")
    driver.add_biocypher_edges([(i1, e1, e2), (i2, e3, e4)])
    r, summary = driver.query(
        "MATCH (n2)-[e4:is_target_of]->(i2:Int2)<-[e3:is_source_of]-"
        "(n1)-[e1:is_source_of]->(i1:Int1)<-[e2:is_target_of]-(n2)"
        "WITH n1, n2, i1, i2, n1.id AS id1, n2.id AS id2, "
        "i1.id AS id3, i2.id AS id4, "
        "type(e1) AS label1, type(e2) AS label2, "
        "type(e3) AS label3, type(e4) AS label4 "
        "RETURN id1, id2, id3, id4, label1, label2, label3, label4"
    )
    assert (
        r[0]["id1"] == "src"
        and r[0]["id2"] == "tar"
        and r[0]["id3"] == "int1"
        and r[0]["id4"] == "int2"
        and r[0]["label1"] == "is_source_of"
        and r[0]["label2"] == "is_target_of"
        and r[0]["label3"] == "is_source_of"
        and r[0]["label4"] == "is_target_of"
    )


def test_add_biocypher_interaction_as_node_tuples_generator(driver):
    # neo4j database needs to be running!
    i1 = BioCypherNode("int1", "Int1")
    i2 = BioCypherNode("int2", "Int2")
    driver.add_biocypher_nodes([i1, i2])
    e1 = BioCypherEdge("src", "int1", "is_source_of")
    e2 = BioCypherEdge("tar", "int1", "is_target_of")
    e3 = BioCypherEdge("src", "int2", "is_source_of")
    e4 = BioCypherEdge("tar", "int2", "is_target_of")
    tuplist = [(i1, e1, e2), (i2, e3, e4)]

    def gen(list):
        for tup in list:
            yield tup

    driver.add_biocypher_edges(gen(tuplist))
    r, summary = driver.query(
        "MATCH (n2)-[e4:is_target_of]->(i2:Int2)<-[e3:is_source_of]-"
        "(n1)-[e1:is_source_of]->(i1:Int1)<-[e2:is_target_of]-(n2)"
        "WITH n1, n2, i1, i2, n1.id AS id1, n2.id AS id2, "
        "i1.id AS id3, i2.id AS id4, "
        "type(e1) AS label1, type(e2) AS label2, "
        "type(e3) AS label3, type(e4) AS label4 "
        "RETURN id1, id2, id3, id4, label1, label2, label3, label4"
    )
    assert (
        r[0]["id1"] == "src"
        and r[0]["id2"] == "tar"
        and r[0]["id3"] == "int1"
        and r[0]["id4"] == "int2"
        and r[0]["label1"] == "is_source_of"
        and r[0]["label2"] == "is_target_of"
        and r[0]["label3"] == "is_source_of"
        and r[0]["label4"] == "is_target_of"
    )


def test_pretty(driver):
    driver.profile(
        "UNWIND [1,2,3,4,5] as id "
        "MERGE (n:Test {id: id}) "
        "MERGE (x:Test {id: id + 1})"
    )

    assert True
