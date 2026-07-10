import os
import pytest

from biocypher._logger import logger
from biocypher._create import BioCypherEdge, BioCypherNode


def gen_nodes(nb: int):
    for i in range(nb):
        prot1 = BioCypherNode(
            node_id=f"p{i}",
            node_label="protein",
            properties={},
        )
        yield prot1

        prot2 = BioCypherNode(
            node_id=f"p{i+1}",
            node_label="protein",
            properties={},
        )
        yield prot2

        drug = BioCypherNode(
            node_id=f"d{i}",
            node_label="drug",
            properties={},
        )
        yield drug


def gen_edges(nb: int):
    for i in range(nb):
        e1 = BioCypherEdge(
            relationship_id=f"a{i}",
            source_id=f"p{i}",
            target_id=f"p{i+1}",
            relationship_label="regulates",
            properties={},
        )
        yield e1

        e2 = BioCypherEdge(
            relationship_id=f"a{i+1}",
            source_id=f"d{i}",
            target_id=f"p{i}",
            relationship_label="disrupts",
            properties={},
        )
        yield e2


def log_head(s: set, max: int = 15, indent: int = 1):
    for i, e in enumerate(s):
        t = "\t" * indent
        logger.debug(f"{t}{i}. {e}")
        if i >= max:
            logger.debug(f"{t}[…]")
            break


def load(filename: str, max: int = 15):
    res = set()
    dups = set()
    logger.info(f"Load {filename} ...")
    with open(filename) as fd:
        lines = fd.readlines()
        logger.info(f"\t{len(lines)} lines")
        if len(lines) == 0:
            logger.error(f"\t{filename} contains no data")
        for line in lines:
            t = line.strip().split("\t")
            if tuple(t) in res:
                dups.add(tuple(t))
            else:
                res.add(tuple(t))
        logger.info(f"\t{len(res)} triples")
        logger.info(f"\t{len( src(res) | tgt(res) )} unique objects (either source or target)")
    ndup = len(lines) - len(res)
    if ndup > 0:
        logger.debug(f"\tcontains {ndup} duplicates:")
        log_head(dups, max, indent=2)
    else:
        logger.debug("\tcontains no duplicate")
    return res


def sources(data: set, k: str):
    return src(data[k])


def src(s: set):
    res = set()
    for e in s:
        res.add(e[0])
    return res


def targets(data: set, k: str):
    return tgt(data[k])


def tgt(s: set):
    res = set()
    for e in s:
        res.add(e[-1])
    return res


def names(s: set):
    return src(s) | tgt(s)


def has_consistency_errors(path: str = ".") -> int:
    nb_errors = 0

    asked = {}
    asked["brg"] = os.path.join(path, "brg.txt")
    asked["skg"] = os.path.join(path, "skg.txt")
    asked["types"] = os.path.join(path, "entity_types.txt")
    asked["names"] = os.path.join(path, "entity_names.txt")
    asked["max"] = 5

    data = {}
    data["brg"] = load(asked["brg"], asked["max"])
    data["skg"] = load(asked["skg"], asked["max"])
    data["types"] = load(asked["types"], asked["max"])
    data["names"] = load(asked["names"], asked["max"])

    if sources(data, "names") == sources(data, "types"):
        logger.info(f"{asked['types']} and {asked['names']} have the same elements IDs")
    else:
        logger.error(f"{asked['types']} and {asked['names']} DO NOT have the same elements IDs")
        nb_errors += 1

    all_names = sources(data, "skg") | targets(data, "skg") | sources(data, "brg") | targets(data, "brg")

    recorded = sources(data, "names")
    if recorded == all_names:
        logger.info(f"{asked['names']} and input SKG names are the same")
    else:
        n_recorded = len(recorded)
        n_all = len(all_names)
        symdiff = recorded.symmetric_difference(all_names)
        if symdiff:
            logger.error(f"{n_recorded} input SKG names differ from {n_all} sources in {asked['names']}:")
            logger.error(f"There's {len(symdiff)} names that differs.")
            nb_errors += 1

            recorded_diff = recorded.difference(all_names)
            if recorded_diff:
                logger.error(
                    f"There's {len(recorded_diff)} names that are in {asked['names']} but not in input SKG names"
                )
                log_head(recorded_diff, asked["max"])
                nb_errors += 1

            all_diff = all_names.difference(recorded)
            if all_diff:
                logger.error(f"There's {len(all_diff)} names that are in input SKG names but not in {asked['names']}")
                log_head(all_diff, asked["max"])
                nb_errors += 1

                for k in ["skg", "brg"]:
                    diff = names(data[k]).difference(recorded)
                    if diff:
                        logger.error(
                            f"There's {len(diff)} names that are in {vars(asked)[k]} but not in {asked['names']}"
                        )
                        log_head(diff, asked["max"])
                        nb_errors += 1
                    else:
                        logger.info(f"All names in {vars(asked)[k]} are in {asked['names']}")

    return nb_errors


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


@pytest.mark.parametrize("length", [10], scope="module")
def test_biopathnet_targeted_relation(bw_biopathnet_disrupts, length):
    bw = bw_biopathnet_disrupts
    edges = bw.write_edges(gen_edges(length))
    assert edges
    nodes = bw.write_nodes(gen_nodes(length))
    assert nodes

    assert not has_consistency_errors(bw.output_directory)
