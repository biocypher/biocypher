import pytest
import networkx as nx

from biocypher._misc import create_tree_visualisation


@pytest.fixture(scope="function")
def _get_inheritance_tree() -> dict:
    inheritance_tree = {
        "B": "A",
        "C": "A",
        "D": "B",
        "E": "B",
        "F": "C",
        "G": "C",
        "H": "E",
        "I": "G",
    }
    return inheritance_tree


@pytest.fixture(scope="function")
def _get_disjoint_tree() -> dict:
    disjoint_tree = {
        "B": "A",
        "C": "A",
        "D": "B",
        "F": "E",
        "G": "E",
        "H": "F",
    }
    return disjoint_tree


def test_tree_vis(_get_inheritance_tree):
    tree_vis = create_tree_visualisation(_get_inheritance_tree)

    assert tree_vis.DEPTH == 1
    assert tree_vis.WIDTH == 2
    assert tree_vis.root == "A"


def test_tree_vis_from_networkx(_get_inheritance_tree):
    graph = nx.DiGraph(_get_inheritance_tree)

    tree_vis = create_tree_visualisation(graph)

    assert tree_vis.DEPTH == 1
    assert tree_vis.WIDTH == 2
    assert tree_vis.root == "A"


def test_disjoint_tree(_get_disjoint_tree):
    with pytest.raises(ValueError):
        create_tree_visualisation(_get_disjoint_tree)


if __name__ == "__main__":
    # to look at it
    print(create_tree_visualisation(nx.DiGraph(_get_inheritance_tree)).show())
