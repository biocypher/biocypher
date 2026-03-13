import os

import pytest

from biocypher._logger import logger


@pytest.mark.parametrize("length", [4], scope="module")
def test_biopathnet_writer_nodes(bw_biopathnet, _get_nodes):
    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    passed_nodes = bw_biopathnet.write_nodes(node_gen(nodes), batch_size=1e6)
    assert passed_nodes
    #    write_result = bw_biopathnet.write_import_call()
    #    assert write_result

    tmp_path = bw_biopathnet.output_directory

    produced_files = os.listdir(tmp_path)
    assert len(produced_files) > 0
    assert len(produced_files) <= 4
    logger.debug(f"produced_files : {produced_files}")
    expected_files = ["entity_types.txt", "entity_names.txt", "brg.txt", "skg.txt"]
    for file in produced_files:
        assert file in expected_files
        f = open(os.path.join(tmp_path, file), "r")
        logger.debug(f"Contents of {file} is \n{f.read()}")

# TODO: add test
#    len_lines = 0
#    with open(f"{tmp_path}/entity_types.txt", "rb") as f:
#        lines = f.readlines()
#        len_lines = len(lines)
#    assert len(nodes) == len_lines


@pytest.mark.parametrize("length", [4], scope="module")
def test_biopathnet_writer_edges(bw_biopathnet, _get_edges):
    edges = _get_edges

    def edge_gen(nodes):
        yield from nodes

    passed_edges = bw_biopathnet.write_edges(edge_gen(edges), batch_size=1e6)
    assert passed_edges
    #    write_result = bw_biopathnet.write_import_call()
    #    assert write_result

    tmp_path = bw_biopathnet.output_directory

    produced_files = os.listdir(tmp_path)
    assert len(produced_files) > 0
    assert len(produced_files) <= 4
    logger.debug(f"produced_files : {produced_files}")
    expected_files = ["entity_types.txt", "entity_names.txt", "brg.txt", "skg.txt"]
    for file in produced_files:
        assert file in expected_files
        f = open(os.path.join(tmp_path, file), "r")
        logger.debug(f"Contents of {file} is \n{f.read()}")
