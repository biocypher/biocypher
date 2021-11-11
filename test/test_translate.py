from biocypher.create import BioCypherNode
from biocypher.translate import gen_translate_edges, gen_translate_nodes
from biocypher.check import VersionNode
from biocypher.driver import Driver

def test_translate_nodes():
    v = VersionNode(Driver(version=False))
    id_type = [
        ('G9205', 'protein'), 
        ('hsa-miR-132-3p', 'mirna'), 
        ('ASDB_OSBS', 'complex')]
    t = gen_translate_nodes(v.leaves, id_type)

    assert all(type(n) == BioCypherNode for n in t)

    t = gen_translate_nodes(v.leaves, id_type)
    assert next(t).get_label() == 'Protein'
    assert next(t).get_label() == 'microRNA'
    assert next(t).get_label() == 'MacromolecularComplexMixin'


def test_translate_edges():
    v = VersionNode(Driver(version=False))
    src_tar_type = [
        ('G21058', 'G50127', 'post_translational'),
        ('G15258', 'G16347', 'post_translational'),
        ('G22418', 'G50123', 'post_translational')
    ]
    t = gen_translate_edges(v.leaves, src_tar_type)

    next(t)

if __name__ == "__main__":
    test_translate_nodes()
    test_translate_edges()