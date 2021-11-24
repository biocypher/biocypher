from biocypher.create import BioCypherEdge, BioCypherNode
from biocypher.driver import Driver
import random
import cProfile, pstats, io
import timeit, pickle


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
    seq = (10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000)
    res = dict()

    for n in seq:
        gen = timeit.timeit(
            lambda: create_network_by_gen(n, int(n * 1.5)), number=1
        )
        lis = timeit.timeit(
            lambda: create_network_by_list(n, int(n * 1.5)), number=1
        )

        res.update({"gen%s" % n: gen, "lis%s" % n: lis})

    with open("benchmark.pickle", "wb") as f:
        pickle.dump(res, f)

    print(res)


def visualise_benchmark():
    import matplotlib.pyplot as plt

    with open("benchmark.pickle", "rb") as f:
        res = pickle.load(f)

    x = [key for key in res.keys() if "gen" in key]
    x = [int(e.replace("gen", "")) for e in x]
    gen = [value for key, value in res.items() if "gen" in key]
    lis = [value for key, value in res.items() if "lis" in key]

    plt.plot(x, gen, marker="o", label="Generator")
    plt.plot(x, lis, marker="o", label="List")
    plt.show()


if __name__ == "__main__":
    prof = False
    if prof:
        profile = cProfile.Profile()
        profile.enable()

    create_networks()

    if prof:
        profile.disable()

        s = io.StringIO()
        sortby = pstats.SortKey.CUMULATIVE
        ps = pstats.Stats(profile, stream=s).sort_stats(sortby)
        ps.print_stats()
        # print(s.getvalue())
        filename = "create_network.prof"
        ps.dump_stats(filename)
