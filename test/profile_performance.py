from biocypher import create
from biocypher.create import BioCypherEdge, BioCypherNode
from biocypher.driver import Driver
import random
import cProfile, pstats, io, shutil


def create_network_by_gen(num_nodes, num_edges):
    d = Driver(version=False)

    def node_gen(num_nodes):
        for i in range(num_nodes):
            yield BioCypherNode(i, "test")

    def edge_gen(num_edges):
        for i in range(num_edges):
            src = random.randint(1, num_nodes)
            tar = random.randint(1, num_nodes)

            yield BioCypherEdge(src, tar, "test")

    d.add_biocypher_nodes(node_gen(num_nodes))
    d.add_biocypher_edges(edge_gen(num_edges))

    d.query("MATCH (n:test) DETACH DELETE n")


def create_network_by_list(num_nodes, num_edges):
    d = Driver(version=False)

    def node_list(num_nodes):
        ls = []
        for i in range(num_nodes):
            ls.append(BioCypherNode(i, "test"))

        return ls

    def edge_list(num_edges):
        ls = []
        for i in range(num_edges):
            src = random.randint(1, num_nodes)
            tar = random.randint(1, num_nodes)
            ls.append(BioCypherEdge(src, tar, "test"))

        return ls

    d.add_biocypher_nodes(node_list(num_nodes))
    d.add_biocypher_edges(edge_list(num_edges))

    d.query("MATCH (n:test) DETACH DELETE n")


def create_networks():
    create_network_by_gen(2000, 2000)
    create_network_by_list(2000, 2000)


if __name__ == "__main__":
    profile = cProfile.Profile()
    profile.enable()
    create_networks()
    profile.disable()

    s = io.StringIO()
    sortby = pstats.SortKey.CUMULATIVE
    ps = pstats.Stats(profile, stream=s).sort_stats(sortby)
    ps.print_stats()
    # print(s.getvalue())
    filename = "create_network.prof"  # You can change this if needed
    ps.dump_stats(filename)
