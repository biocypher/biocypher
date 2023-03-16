import neo4j
import pytest

from biocypher._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode
from biocypher._connect import _Neo4jDriver


def test_create_driver(driver):

    assert isinstance(driver, _Neo4jDriver)


def test_connect_to_db(driver):

    assert isinstance(driver._driver.driver, neo4j.Neo4jDriver) or isinstance(driver._driver.driver, neo4j.BoltDriver)


def test_increment_version(driver):
    driver._driver.wipe_db()
    query = "CREATE (n:BioCypher {id: 'v19700101-000000'})"
    driver._driver.query(query)
    driver._update_meta_graph()

    r, summary = driver._driver.query('MATCH (n:BioCypher) '
                                      'RETURN n', )

    assert len(r) == 2


def test_explain(driver):
    query = 'MATCH (n) WITH n LIMIT 25 MATCH (n)--(m)--(f) RETURN n, m, f'
    e = driver._driver.explain(query)
    t = e[0]

    assert 'args' in t and 'identifiers' in t


def test_profile(driver):
    query = 'MATCH (n) RETURN n LIMIT 100'
    p = driver._driver.profile(query)
    t = p[0]

    assert 'args' in t and 'identifiers' in t


def test_add_invalid_biocypher_node(driver):
    # neo4j database needs to be running!

    with pytest.raises(ValueError):
        driver.add_biocypher_nodes(1)

    with pytest.raises(ValueError):
        driver.add_biocypher_nodes('String')


def test_add_single_biocypher_node(driver):
    # neo4j database needs to be running!
    n = BioCypherNode(node_id='test_id1', node_label='Test')
    driver.add_biocypher_nodes(n)
    r, summary = driver._driver.query(
        'MATCH (n:Test) '
        'WITH n, n.id AS id '
        'RETURN id ',
    )
    assert r[0]['id'] == 'test_id1'


def test_add_biocypher_node_list(driver):
    # neo4j database needs to be running!
    n1 = BioCypherNode(node_id='test_id1', node_label='Test')
    n2 = BioCypherNode(node_id='test_id2', node_label='Test')
    driver.add_biocypher_nodes([n1, n2])
    r, summary = driver._driver.query(
        'MATCH (n:Test) '
        'WITH n, n.id AS id '
        'RETURN id ',
    )
    assert set([r[0]['id'], r[1]['id']]) == set(['test_id1', 'test_id2'])


def test_add_biocypher_node_generator(driver):
    # neo4j database needs to be running!
    # generator
    def gen(nodes):
        for g in nodes:
            yield BioCypherNode(g[0], g[1])

    g = gen([('test_id1', 'Test'), ('test_id2', 'Test')])

    driver.add_biocypher_nodes(g)
    r, summary = driver._driver.query(
        'MATCH (n:Test) '
        'WITH n, n.id AS id '
        'RETURN id ',
    )

    ids = [n['id'] for n in r]

    assert 'test_id1' in ids
    assert 'test_id2' in ids


def test_add_specific_id_node(driver):
    n = BioCypherNode(node_id='CHAT', node_label='Gene', preferred_id='hgnc')
    driver.add_biocypher_nodes(n)

    r, summary = driver._driver.query('MATCH (n:Gene) '
                                      'RETURN n', )

    assert r[0]['n'].get('id') == 'CHAT'
    assert r[0]['n'].get('preferred_id') == 'hgnc'


def test_add_generic_id_node(driver):
    n = BioCypherNode(node_id='CHAT', node_label='Gene', preferred_id='HGNC')
    driver.add_biocypher_nodes(n)

    r, summary = driver._driver.query('MATCH (n:Gene) '
                                      'RETURN n', )

    assert r[0]['n'].get('id') is not None


def test_add_invalid_biocypher_edge(driver):
    # neo4j database needs to be running!
    with pytest.raises(ValueError):
        driver.add_biocypher_edges([1, 2, 3])


def test_add_single_biocypher_edge_explicit_node_creation(driver):
    # neo4j database needs to be running!
    n1 = BioCypherNode('src', 'Test')
    n2 = BioCypherNode('tar', 'Test')
    driver.add_biocypher_nodes([n1, n2])

    e = BioCypherEdge('src', 'tar', 'Test')
    driver.add_biocypher_edges(e)
    r, summary = driver._driver.query(
        'MATCH (n1)-[r:Test]->(n2) '
        'WITH n1, n2, n1.id AS id1, n2.id AS id2, type(r) AS label '
        'RETURN id1, id2, label',
    )
    assert (
        r[0]['id1'] == 'src' and r[0]['id2'] == 'tar' and
        r[0]['label'] == 'Test'
    )


def test_add_single_biocypher_edge_missing_nodes(driver):
    # neo4j database needs to be running!
    # merging on non-existing nodes creates them without labels; what is
    # the desired behaviour here? do we only want to MATCH?

    e = BioCypherEdge('src', 'tar', 'Test')
    driver.add_biocypher_edges(e)
    r, summary = driver._driver.query(
        'MATCH (n1)-[r:Test]->(n2) '
        'WITH n1, n2, n1.id AS id1, n2.id AS id2, type(r) AS label '
        'RETURN id1, id2, label',
    )
    assert (
        r[0]['id1'] == 'src' and r[0]['id2'] == 'tar' and
        r[0]['label'] == 'Test'
    )


def test_add_biocypher_edge_list(driver):
    # neo4j database needs to be running!
    n1 = BioCypherNode('src', 'Test')
    n2 = BioCypherNode('tar1', 'Test')
    n3 = BioCypherNode('tar2', 'Test')
    driver.add_biocypher_nodes([n1, n2, n3])

    # edge list
    e1 = BioCypherEdge('src', 'tar1', 'Test1')
    e2 = BioCypherEdge('src', 'tar2', 'Test2')
    driver.add_biocypher_edges([e1, e2])
    r, summary = driver._driver.query(
        'MATCH (n3)<-[r2:Test2]-(n1)-[r1:Test1]->(n2) '
        'WITH n1, n2, n3, n1.id AS id1, n2.id AS id2, n3.id AS id3, '
        'type(r1) AS label1, type(r2) AS label2 '
        'RETURN id1, id2, id3, label1, label2',
    )
    assert (
        r[0]['id1'] == 'src' and r[0]['id2'] == 'tar1' and
        r[0]['id3'] == 'tar2' and r[0]['label1'] == 'Test1' and
        r[0]['label2'] == 'Test2'
    )


def test_add_biocypher_edge_generator(driver):
    # neo4j database needs to be running!
    n1 = BioCypherNode('src', 'Test')
    n2 = BioCypherNode('tar1', 'Test')
    n3 = BioCypherNode('tar2', 'Test')
    driver.add_biocypher_nodes([n1, n2, n3])

    # generator
    def gen(edges):
        for e in edges:
            yield BioCypherEdge(
                e.get_source_id(),
                e.get_target_id(),
                e.get_label(),
            )

    # edge list
    e1 = BioCypherEdge('src', 'tar1', 'Test1')
    e2 = BioCypherEdge('src', 'tar2', 'Test2')
    g = gen([e1, e2])

    driver.add_biocypher_edges(g)
    r, summary = driver._driver.query(
        'MATCH (n3)<-[r2:Test2]-(n1)-[r1:Test1]->(n2) '
        'WITH n1, n2, n3, n1.id AS id1, n2.id AS id2, n3.id AS id3, '
        'type(r1) AS label1, type(r2) AS label2 '
        'RETURN id1, id2, id3, label1, label2',
    )
    assert (
        r[0]['id1'] == 'src' and r[0]['id2'] == 'tar1' and
        r[0]['id3'] == 'tar2' and r[0]['label1'] == 'Test1' and
        r[0]['label2'] == 'Test2'
    )


def test_add_biocypher_interaction_as_BioCypherRelAsNode_list(driver):
    # neo4j database needs to be running!
    i1 = BioCypherNode('int1', 'Int1')
    i2 = BioCypherNode('int2', 'Int2')
    driver.add_biocypher_nodes([i1, i2])
    e1 = BioCypherEdge('src', 'int1', 'is_source_of')
    e2 = BioCypherEdge('tar', 'int1', 'is_target_of')
    e3 = BioCypherEdge('src', 'int2', 'is_source_of')
    e4 = BioCypherEdge('tar', 'int2', 'is_target_of')
    r1, r2 = BioCypherRelAsNode(i1, e1, e2), BioCypherRelAsNode(i2, e3, e4)
    driver.add_biocypher_edges([r1, r2])
    r, summary = driver._driver.query(
        'MATCH (n2)-[e4:is_target_of]->(i2:Int2)<-[e3:is_source_of]-'
        '(n1)-[e1:is_source_of]->(i1:Int1)<-[e2:is_target_of]-(n2)'
        'WITH n1, n2, i1, i2, n1.id AS id1, n2.id AS id2, '
        'i1.id AS id3, i2.id AS id4, '
        'type(e1) AS label1, type(e2) AS label2, '
        'type(e3) AS label3, type(e4) AS label4 '
        'RETURN id1, id2, id3, id4, label1, label2, label3, label4',
    )
    assert (
        r[0]['id1'] == 'src' and r[0]['id2'] == 'tar' and
        r[0]['id3'] == 'int1' and r[0]['id4'] == 'int2' and
        r[0]['label1'] == 'is_source_of' and
        r[0]['label2'] == 'is_target_of' and
        r[0]['label3'] == 'is_source_of' and r[0]['label4'] == 'is_target_of'
    )


def test_add_biocypher_interaction_as_BioCypherRelAsNode_generator(driver):
    # neo4j database needs to be running!
    i1 = BioCypherNode('int1', 'Int1')
    i2 = BioCypherNode('int2', 'Int2')
    driver.add_biocypher_nodes([i1, i2])
    e1 = BioCypherEdge('src', 'int1', 'is_source_of')
    e2 = BioCypherEdge('tar', 'int1', 'is_target_of')
    e3 = BioCypherEdge('src', 'int2', 'is_source_of')
    e4 = BioCypherEdge('tar', 'int2', 'is_target_of')
    r1, r2 = BioCypherRelAsNode(i1, e1, e2), BioCypherRelAsNode(i2, e3, e4)
    relasnode_list = [r1, r2]

    def gen(lis):
        for tup in lis:
            yield tup

    driver.add_biocypher_edges(gen(relasnode_list))
    r, summary = driver._driver.query(
        'MATCH (n2)-[e4:is_target_of]->(i2:Int2)<-[e3:is_source_of]-'
        '(n1)-[e1:is_source_of]->(i1:Int1)<-[e2:is_target_of]-(n2)'
        'WITH n1, n2, i1, i2, n1.id AS id1, n2.id AS id2, '
        'i1.id AS id3, i2.id AS id4, '
        'type(e1) AS label1, type(e2) AS label2, '
        'type(e3) AS label3, type(e4) AS label4 '
        'RETURN id1, id2, id3, id4, label1, label2, label3, label4',
    )
    assert (
        r[0]['id1'] == 'src' and r[0]['id2'] == 'tar' and
        r[0]['id3'] == 'int1' and r[0]['id4'] == 'int2' and
        r[0]['label1'] == 'is_source_of' and
        r[0]['label2'] == 'is_target_of' and
        r[0]['label3'] == 'is_source_of' and r[0]['label4'] == 'is_target_of'
    )


def test_pretty_profile(driver):
    prof, printout = driver._driver.profile(
        'UNWIND [1,2,3,4,5] as id '
        'MERGE (n:Test {id: id}) '
        'MERGE (x:Test {id: id + 1})',
    )

    assert 'args' in prof and 'ProduceResults' in printout[1]


def test_pretty_explain(driver):
    plan, printout = driver._driver.explain(
        'UNWIND [1,2,3,4,5] as id '
        'MERGE (n:Test {id: id}) '
        'MERGE (x:Test {id: id + 1})',
    )

    assert 'args' in plan and 'ProduceResults' in printout[0]
