import pytest
import networkx as nx

from biocypher._misc import create_tree_visualisation

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

disjoint_tree = {
    "B": "A",
    "C": "A",
    "D": "B",
    "F": "E",
    "G": "E",
    "H": "F",
}


def test_tree_vis():
    tree_vis = create_tree_visualisation(inheritance_tree)

    assert tree_vis.DEPTH == 1
    assert tree_vis.WIDTH == 2
    assert tree_vis.root == "A"


def test_tree_vis_from_networkx():
    graph = nx.DiGraph(inheritance_tree)

    tree_vis = create_tree_visualisation(graph)

    assert tree_vis.DEPTH == 1
    assert tree_vis.WIDTH == 2
    assert tree_vis.root == "A"


def test_disjoint_tree():
    with pytest.raises(ValueError):
        create_tree_visualisation(disjoint_tree)


if __name__ == "__main__":
    # to look at it
    print(create_tree_visualisation(nx.DiGraph(inheritance_tree)).show())
