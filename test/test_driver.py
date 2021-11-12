from biocypher.driver import Driver
from biocypher.create import BioCypherNode, BioCypherEdge
import pytest


def test_add_biocypher_nodes():
    """
    ??:
    Sometimes randomly (?) fails because graph state is not acquired,
    even though there is a check for that in line 534 of `driver.py`.
        self = <Driver neo4j://localhost:7687/user>

        def update_meta_graph(self):
            # add version node
            self.add_biocypher_nodes(self.db_meta)

            # connect version node to previous
            e_meta = BioCypherEdge(
    >           self.db_meta.graph_state['id'],
                self.db_meta.node_id,
                'PRECEDES'
                )
    E       TypeError: 'NoneType' object is not subscriptable

    biocypher/driver.py:547: TypeError

    Currently, each test adds a version node. May be something to avoid in
    the future.
    """
    # neo4j database needs to be running!
    d = Driver(version=False)

    with pytest.raises(Exception):
        d.add_biocypher_nodes(1)

    # single node
    n = BioCypherNode("test", "test")
    d.add_biocypher_nodes(n)
    r = d.query(
        "MATCH (n:test) " "WITH n, n.id AS id " "DELETE n " "RETURN id "
    )
    assert r[0]["id"] == "test"

    # node list
    n2 = BioCypherNode("test2", "test")
    d.add_biocypher_nodes([n, n2])
    r = d.query(
        "MATCH (n:test) " "WITH n, n.id AS id " "DELETE n " "RETURN id "
    )
    assert r[0]["id"] == "test" and r[1]["id"] == "test2"

    # generator
    def gen(nodes):
        for g in nodes:
            yield BioCypherNode(g.get_id(), g.get_label())

    g = gen([n, n2])
    d.add_biocypher_nodes(g)
    r = d.query(
        "MATCH (n:test) " "WITH n, n.id AS id " "DELETE n " "RETURN id "
    )
    assert r[0]["id"] == "test" and r[1]["id"] == "test2"


def test_add_biocypher_edges():
    # neo4j database needs to be running!
    d = Driver(version=False)

    with pytest.raises(Exception):
        d.add_biocypher_edges(1)

    # single edge
    e = BioCypherEdge("src", "tar", "test")
    d.add_biocypher_edges(e)
    r = d.query(
        "MATCH (n)-[r:test]->(n2) "
        "WITH n, n2, n.id AS id, n2.id AS id2, type(r) AS label "
        "DETACH DELETE n, n2 "
        "RETURN id, id2, label"
    )
    assert (
        r[0]["id"] == "src"
        and r[0]["id2"] == "tar"
        and r[0]["label"] == "test"
    )

    # edge list
    e2 = BioCypherEdge("src", "tar2", "test2")
    d.add_biocypher_edges([e, e2])
    r = d.query(
        "MATCH (n3)<-[r2:test2]-(n)-[r:test]->(n2) "
        "WITH n, n2, n3, n.id AS id, n2.id AS id2, n3.id AS id3, "
        "type(r) AS label, type(r2) AS label2 "
        "DETACH DELETE n, n2, n3 "
        "RETURN id, id2, id3, label, label2"
    )
    assert (
        r[0]["id"] == "src"
        and r[0]["id2"] == "tar"
        and r[0]["id3"] == "tar2"
        and r[0]["label"] == "test"
        and r[0]["label2"] == "test2"
    )

    # generator
    def gen(edges):
        for e in edges:
            yield BioCypherEdge(
                e.get_source_id(), e.get_target_id(), e.get_label()
            )

    g = gen([e, e2])
    d.add_biocypher_edges(g)
    r = d.query(
        "MATCH (n3)<-[r2:test2]-(n)-[r:test]->(n2) "
        "WITH n, n2, n3, n.id AS id, n2.id AS id2, n3.id AS id3, "
        "type(r) AS label, type(r2) AS label2 "
        "DETACH DELETE n, n2, n3 "
        "RETURN id, id2, id3, label, label2"
    )
    assert (
        r[0]["id"] == "src"
        and r[0]["id2"] == "tar"
        and r[0]["id3"] == "tar2"
        and r[0]["label"] == "test"
        and r[0]["label2"] == "test2"
    )

    # tuples
    n = BioCypherNode("src", "src")
    n2 = BioCypherNode("tar", "tar")
    i = BioCypherNode("int", "int")
    e = BioCypherEdge("src", "int", "is_source_of")
    e2 = BioCypherEdge("tar", "int", "is_target_of")
    i2 = BioCypherNode("int2", "int2")
    e3 = BioCypherEdge("src", "int2", "is_source_of")
    e4 = BioCypherEdge("tar", "int2", "is_target_of")
    d.add_biocypher_nodes([n, n2])
    d.add_biocypher_edges([(i, e, e2), (i2, e3, e4)])
    r = d.query(
        "MATCH (n3:tar)-[e4:is_target_of]->(i2:int2)<-[e3:is_source_of]-"
        "(n:src)-[e:is_source_of]->(i:int)<-[e2:is_target_of]-(n2:tar)"
        "WITH n, n2, n3, i, i2, n.id AS id, n2.id AS id2, n3.id AS id3, "
        "i.id AS id4, i2.id AS id5, "
        "type(e) AS label, type(e2) AS label2, "
        "type(e3) AS label3, type(e4) AS label4 "
        "DETACH DELETE n, n2, n3, i, i2 "
        "RETURN id, id2, id3, id4, id5, label, label2, label3, label4"
    )
    assert (
        r[0]["id"] == "src"
        and r[0]["id2"] == "tar"
        and r[0]["id3"] == "tar"
        and r[0]["id4"] == "int"
        and r[0]["id5"] == "int2"
        and r[0]["label"] == "is_source_of"
        and r[0]["label2"] == "is_target_of"
        and r[0]["label3"] == "is_source_of"
        and r[0]["label4"] == "is_target_of"
    )


if __name__ == "__main__":
    test_add_biocypher_edges()
    test_add_biocypher_nodes()
