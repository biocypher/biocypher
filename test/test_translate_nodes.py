from biocypher.create import BioCypherNode
from biocypher.translate import translate_nodes
from biocypher.check import VersionNode
from biocypher.driver import Driver

def test():
    v = VersionNode(Driver())
    id_type = [
        ('G9205', 'protein'), 
        ('hsa-miR-132-3p', 'mirna'), 
        ('ASDB_OSBS', 'complex')]
    t = translate_nodes(v.leaves, id_type)

    assert all(type(n) == BioCypherNode for n in t)
    assert t[0].get_label() == 'Protein'
    assert t[1].get_label() == 'microRNA'
    assert t[2].get_label() == 'MacromolecularComplexMixin'

if __name__ == "__main__":
    test()