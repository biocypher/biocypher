from biocypher.driver import Driver
from biocypher.create import BioCypherNode
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
    """
    # neo4j database needs to be running!
    d = Driver()

    with pytest.raises(Exception):
        d.add_biocypher_nodes(1)

    # single node
    n = BioCypherNode("test", "test")
    d.add_biocypher_nodes(n)
    r = d.query(
        "MATCH (n:test) "
        "WITH n, n.id AS id "
        "DELETE n "
        "RETURN id "
    )
    assert r[0]['id'] == 'test'

    # node list
    n2 = BioCypherNode("test2", "test")
    d.add_biocypher_nodes([n, n2])
    r = d.query(
        "MATCH (n:test) "
        "WITH n, n.id AS id "
        "DELETE n "
        "RETURN id "
    )
    assert r[0]['id'] == 'test' and r[1]['id'] == 'test2'

    # generator
    def gen(nodes):
        for g in nodes:
            yield BioCypherNode(g.get_id(), g.get_label())

    g = gen([n, n2])
    d.add_biocypher_nodes(g)
    r = d.query(
        "MATCH (n:test) "
        "WITH n, n.id AS id "
        "DELETE n "
        "RETURN id "
    )
    assert r[0]['id'] == 'test' and r[1]['id'] == 'test2'


if __name__ == "__main__":
    test_add_biocypher_nodes()