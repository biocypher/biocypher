from biocypher.create import BioCypherEdge, BioCypherNode
from biocypher.driver import Driver
import random
import cProfile, pstats, io
import timeit, pickle


def create_network_by_gen(num_nodes, num_edges, profile=False):
    d = Driver(version=False)

    def node_gen(num_nodes):
        for i in range(num_nodes):
            yield BioCypherNode(i, "test")

    def edge_gen(num_edges):
        for _ in range(num_edges):
            src = random.randint(1, num_nodes)
            tar = random.randint(1, num_nodes)

            yield BioCypherEdge(src, tar, "test")

    node_profile = d.add_biocypher_nodes(node_gen(num_nodes), profile=profile)
    edge_profile = d.add_biocypher_edges(edge_gen(num_edges), profile=profile)

    if profile:
        return node_profile, edge_profile

    d.close()


def create_network_by_list(num_nodes, num_edges):
    d = Driver(version=False)

    def node_list(num_nodes):
        ls = []
        for i in range(num_nodes):
            ls.append(BioCypherNode(i, "test"))

        return ls

    def edge_list(num_edges):
        ls = []
        for _ in range(num_edges):
            src = random.randint(1, num_nodes)
            tar = random.randint(1, num_nodes)
            ls.append(BioCypherEdge(src, tar, "test"))

        return ls

    d.add_biocypher_nodes(node_list(num_nodes))
    d.add_biocypher_edges(edge_list(num_edges))

    d.close()


def delete_test_network():
    d = Driver(version=False)
    d.query("MATCH (n)-[:test]-() DETACH DELETE n")
    d.query("MATCH (n:test) DETACH DELETE n")
    d.close()


def create_networks():
    seq = (10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000)
    res = dict()

    for n in seq:
        gen = timeit.timeit(
            lambda: create_network_by_gen(n, int(n * 1.5)), number=1
        )
        delete_test_network()
        lis = timeit.timeit(
            lambda: create_network_by_list(n, int(n * 1.5)), number=1
        )
        delete_test_network()

        res.update({"gen%s" % n: gen, "lis%s" % n: lis})

    with open("benchmark.pickle", "wb") as f:
        pickle.dump(res, f)

    print(res)


def visualise_benchmark():
    import matplotlib.pyplot as plt
    import pickle

    with open("benchmark.pickle", "rb") as f:
        res = pickle.load(f)

    x = [key for key in res.keys() if "gen" in key]
    x = [int(e.replace("gen", "")) for e in x]
    gen = [value for key, value in res.items() if "gen" in key]
    lis = [value for key, value in res.items() if "lis" in key]

    plt.plot(x, gen, marker="o", label="Generator")
    plt.plot(x, lis, marker="o", label="List")
    plt.xlabel("Network size (nodes)")
    plt.ylabel("Time (s)")
    plt.legend()
    plt.show()


def profile_neo4j(num_nodes, num_edges):

    np, ep = create_network_by_gen(num_nodes, num_edges, profile=True)
    return np, ep


if __name__ == "__main__":
    python_prof = False
    neo4j_prof = True
    run = False
    viz = False

    if python_prof:
        profile = cProfile.Profile()
        profile.enable()

    if run:
        create_networks()

    if python_prof:
        profile.disable()

        s = io.StringIO()
        sortby = pstats.SortKey.CUMULATIVE
        ps = pstats.Stats(profile, stream=s).sort_stats(sortby)
        ps.print_stats()
        # print(s.getvalue())
        filename = "create_network.prof"
        ps.dump_stats(filename)

    if viz:
        visualise_benchmark()

    if neo4j_prof:
        node_profile, edge_profile = profile_neo4j(
            num_nodes=1000, num_edges=1500
        )
        print("### NODE PROFILE ###")
        for p in node_profile:
            print("Step: " + p[0])
            print("Args: " + str(p[1]))
        print("### EDGE PROFILE ###")
        for e in edge_profile:
            print("Step: " + e[0])
            print("Args: " + str(e[1]))

        """
        Eager execution of the apoc.merge.relationships is the primary 
        holdup for this function. More info about Eager here: 
        https://community.neo4j.com/t/cypher-sleuthing-the-eager-operator/10730
        and here:
        https://neo4j.com/docs/cypher-manual/current/execution-plans/operators/#query-plan-eager

        She says: "In order to get around the eager operator, we need to 
        ensure Cypher isn’t worried about conflicting operations. The 
        best way to do this is to divide our query into single 
        operations so that Cypher won’t invoke eager as a safeguard. 
        Let’s profile this as two queries to see that."

        Should we MERGE the nodes and edges in separate queries?
        """

    # cleanup
    delete_test_network()
