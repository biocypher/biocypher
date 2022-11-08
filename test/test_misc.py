from biocypher._misc import create_tree_visualisation

inheritance_tree = {
    'B': 'A',
    'C': 'A',
    'D': 'B',
    'E': 'B',
    'F': 'C',
    'G': 'C',
    'H': 'E',
    'I': 'G',
}


def test_tree_vis():

    tree_vis = create_tree_visualisation(inheritance_tree)

    assert tree_vis.DEPTH == 1
    assert tree_vis.WIDTH == 2
    assert tree_vis.root == 'A'


if __name__ == '__main__':
    # to look at it
    print(create_tree_visualisation(inheritance_tree).show())
