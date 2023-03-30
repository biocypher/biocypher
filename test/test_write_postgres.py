import os
import subprocess

import pytest


@pytest.mark.parametrize('l', [4], scope='module')
def test_write_node_data_from_gen_comma_postgresql(
    bw_comma_postgresql, path, _get_nodes
):
    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    passed = bw_comma_postgresql._write_node_data(
        node_gen(nodes), batch_size=1e6
    )

    p_csv = os.path.join(path, 'Protein-part000.csv')
    m_csv = os.path.join(path, 'MicroRNA-part000.csv')

    with open(p_csv) as f:
        pr = f.read()

    with open(m_csv) as f:
        mi = f.read()

    assert passed
    assert 'p1,"StringProperty1",4.0,9606,"{gene1,gene2}","p1","uniprot","{BiologicalEntity,ChemicalEntityOrProteinOrPolypeptide,Entity,NamedThing,Polypeptide,Protein}"' in pr
    assert 'BiologicalEntity' in pr
    assert 'm1,"StringProperty1",9606,"m1","mirbase"' in mi
    assert 'ChemicalEntity' in mi


@pytest.mark.parametrize('l', [4], scope='module')
def test_write_node_data_from_gen_tab_postgresql(
    bw_tab_postgresql, path, _get_nodes
):
    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    passed = bw_tab_postgresql._write_node_data(node_gen(nodes), batch_size=1e6)

    p_csv = os.path.join(path, 'Protein-part000.csv')
    m_csv = os.path.join(path, 'MicroRNA-part000.csv')

    with open(p_csv) as f:
        pr = f.read()

    with open(m_csv) as f:
        mi = f.read()

    assert passed
    assert 'p1\t"StringProperty1"\t4.0\t9606\t"{gene1,gene2}"\t"p1"\t"uniprot"\t"{BiologicalEntity,ChemicalEntityOrProteinOrPolypeptide,Entity,NamedThing,Polypeptide,Protein}"' in pr
    assert 'BiologicalEntity' in pr
    assert 'm1\t"StringProperty1"\t9606\t"m1"\t"mirbase"' in mi
    assert 'ChemicalEntity' in mi


@pytest.mark.requires_postgresql
@pytest.mark.parametrize('l', [4], scope='module')
def test_database_import_node_data_from_gen_comma_postgresql(
    bw_comma_postgresql, path, _get_nodes, create_database_postgres
):
    dbname, user, port, password, create_database_success = create_database_postgres
    assert create_database_success

    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    bw_comma_postgresql.write_nodes(node_gen(nodes))
    # verify that all files have been created
    assert set(os.listdir(path)) == set(
        [
            'protein-create_table.sql', 'Protein-part000.csv',
            'microrna-create_table.sql', 'MicroRNA-part000.csv'
        ]
    )

    bw_comma_postgresql.write_import_call()
    # verify that import call has been created
    import_scripts = [
        name for name in os.listdir(path) if name.endswith('-import-call.sh')
    ]
    assert len(import_scripts) == 1

    import_script = import_scripts[0]
    script = os.path.join(path, import_script)
    with open(script) as f:
        commands = f.readlines()
        assert len(commands) == 16

    for command in commands:
        result = subprocess.run(command, shell=True)
        assert result.returncode == 0

    # check data in the databases
    command = f'PGPASSWORD={password} psql -c \'SELECT COUNT(*) FROM protein;\' --dbname {dbname} --port {port} --user {user}'
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    # subprocess success
    assert result.returncode == 0
    # 4 entires in table
    assert '4' in result.stdout.decode()

    # check data in the databases
    command = f'PGPASSWORD={password} psql -c \'SELECT COUNT(*) FROM microrna;\' --dbname {dbname} --port {port} --user {user}'
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    # subprocess success
    assert result.returncode == 0
    # 4 entires in table
    assert '4' in result.stdout.decode()


@pytest.mark.requires_postgresql
@pytest.mark.parametrize('l', [5], scope='module')
def test_database_import_node_data_from_gen_tab_postgresql(
    bw_tab_postgresql, path, _get_nodes, create_database_postgres
):
    dbname, user, port, password, create_database_success = create_database_postgres
    assert create_database_success

    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    bw_tab_postgresql.write_nodes(node_gen(nodes))
    # verify that all files have been created
    assert set(os.listdir(path)) == set(
        [
            'protein-create_table.sql', 'Protein-part000.csv',
            'microrna-create_table.sql', 'MicroRNA-part000.csv'
        ]
    )

    bw_tab_postgresql.write_import_call()
    # verify that import call has been created
    import_scripts = [
        name for name in os.listdir(path) if name.endswith('-import-call.sh')
    ]
    assert len(import_scripts) == 1

    import_script = import_scripts[0]
    script = os.path.join(path, import_script)
    with open(script) as f:
        commands = f.readlines()
        assert len(commands) == 16

    for command in commands:
        result = subprocess.run(command, shell=True)
        assert result.returncode == 0

    # check data in the databases
    command = f'PGPASSWORD={password} psql -c \'SELECT COUNT(*) FROM protein;\' --dbname {dbname} --port {port} --user {user}'
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    # subprocess success
    assert result.returncode == 0
    # 5 entires in table
    assert '5' in result.stdout.decode()

    # check data in the databases
    command = f'PGPASSWORD={password} psql -c \'SELECT COUNT(*) FROM microrna;\' --dbname {dbname} --port {port} --user {user}'
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    # subprocess success
    assert result.returncode == 0
    # 5 entires in table
    assert '5' in result.stdout.decode()


@pytest.mark.requires_postgresql
@pytest.mark.parametrize('l', [8], scope='module')
def test_database_import_edge_data_from_gen_comma_postgresql(
    bw_comma_postgresql, path, _get_nodes, create_database_postgres, _get_edges
):
    dbname, user, port, password, create_database_success = create_database_postgres
    assert create_database_success

    edges = _get_edges

    nodes = _get_nodes

    def edge_gen1(edges):
        yield from edges[:4]

    def edge_gen2(edges):
        yield from edges[4:]

    p1 = bw_comma_postgresql.write_edges(edge_gen1(edges))
    p2 = bw_comma_postgresql.write_edges(edge_gen2(edges))
    p3 = bw_comma_postgresql.write_nodes(nodes)

    assert all([p1, p2, p3])

    bw_comma_postgresql.write_import_call()

    # verify that import call has been created
    import_scripts = [
        name for name in os.listdir(path) if name.endswith('-import-call.sh')
    ]
    assert len(import_scripts) == 1

    import_script = import_scripts[0]
    script = os.path.join(path, import_script)
    with open(script) as f:
        commands = f.readlines()
        assert len(commands) > 0

    for command in commands:
        result = subprocess.run(command, shell=True)
        assert result.returncode == 0

    # check data in the databases
    command = f'PGPASSWORD={password} psql -c \'SELECT COUNT(*) FROM is_mutated_in;\' --dbname {dbname} --port {port} --user {user}'
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    # subprocess success
    assert result.returncode == 0
    # 2 entries in table
    assert '2' in result.stdout.decode()

    command = f'PGPASSWORD={password} psql -c \'SELECT COUNT(*) FROM perturbed_in_disease;\' --dbname {dbname} --port {port} --user {user}'
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    # subprocess success
    assert result.returncode == 0
    # 2 entries in table
    assert '2' in result.stdout.decode()


@pytest.mark.requires_postgresql
@pytest.mark.parametrize('l', [8], scope='module')
def test_database_import_edge_data_from_gen_tab_postgresql(
    bw_tab_postgresql, path, _get_nodes, create_database_postgres, _get_edges
):
    dbname, user, port, password, create_database_success = create_database_postgres
    assert create_database_success

    edges = _get_edges

    nodes = _get_nodes

    def edge_gen1(edges):
        yield from edges[:4]

    def edge_gen2(edges):
        yield from edges[4:]

    p1 = bw_tab_postgresql.write_edges(edge_gen1(edges))
    p2 = bw_tab_postgresql.write_edges(edge_gen2(edges))
    p3 = bw_tab_postgresql.write_nodes(nodes)

    assert all([p1, p2, p3])

    bw_tab_postgresql.write_import_call()

    # verify that import call has been created
    import_scripts = [
        name for name in os.listdir(path) if name.endswith('-import-call.sh')
    ]
    assert len(import_scripts) == 1

    import_script = import_scripts[0]
    script = os.path.join(path, import_script)
    with open(script) as f:
        commands = f.readlines()
        assert len(commands) == 32

    for command in commands:
        result = subprocess.run(command, shell=True)
        assert result.returncode == 0

    # check data in the databases
    command = f'PGPASSWORD={password} psql -c \'SELECT COUNT(*) FROM is_mutated_in;\' --dbname {dbname} --port {port} --user {user}'
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    # subprocess success
    assert result.returncode == 0
    # 2 entires in table
    assert '2' in result.stdout.decode()

    command = f'PGPASSWORD={password} psql -c \'SELECT COUNT(*) FROM perturbed_in_disease;\' --dbname {dbname} --port {port} --user {user}'
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    # subprocess success
    assert result.returncode == 0
    # 2 entires in table
    assert '2' in result.stdout.decode()
