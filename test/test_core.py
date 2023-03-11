def test_biocypher(core):
    assert core._dbms == 'neo4j'
    assert core._offline == True
    assert core._strict_mode == False
