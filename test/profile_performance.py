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
        delete_test_network()
        d.add_biocypher_nodes(node_gen(num_nodes), profile=False)
        edge_profile_mod = d.add_biocypher_edges_mod(
            edge_gen(num_edges), profile=profile
        )
        return node_profile, edge_profile, edge_profile_mod

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


def setup_constraint():
    d = Driver(version=False)
    d.query(
        "CREATE CONSTRAINT test_id "
        "IF NOT EXISTS ON (n:test) "
        "ASSERT n.id IS UNIQUE "
    )
    d.close()


def remove_constraint():
    d = Driver(version=False)
    d.query("DROP CONSTRAINT test_id")
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
    # for number formatting
    import locale
    import statistics

    locale.setlocale(locale.LC_ALL, "")
    setup_constraint()

    node_profile, edge_profile, edge_profile_mod = create_network_by_gen(
        num_nodes, num_edges, profile=True
    )
    print("")
    print(f"{bcolors.HEADER}### NODE PROFILE ###{bcolors.ENDC}")
    med_np = statistics.mean(n[2] for n in node_profile)
    for p in node_profile:
        print(f"{bcolors.OKBLUE}> Step: {p[0]}{bcolors.ENDC}")
        print(f"Args: {p[1]}")
        if p[2] > med_np:
            print(f"{bcolors.WARNING}Time: {p[2]:n}{bcolors.ENDC}")
        else:
            print(f"Time: {p[2]:n}")

    print("")
    print(f"{bcolors.HEADER}### EDGE PROFILE ###{bcolors.ENDC}")
    med_ep = statistics.mean(e[2] for e in edge_profile)
    for ep in edge_profile:
        print(f"{bcolors.OKBLUE}> Step: {ep[0]}{bcolors.ENDC}")
        print(f"Args: {ep[1]}")
        if ep[2] > med_ep:
            print(f"{bcolors.WARNING}Time: {ep[2]:n}{bcolors.ENDC}")
        else:
            print(f"Time: {ep[2]:n}")

    print("")
    print(f"{bcolors.HEADER}### MODIFIED EDGE PROFILE ###{bcolors.ENDC}")
    med_em = statistics.mean(e[2] for e in edge_profile_mod)
    for em in edge_profile_mod:
        print(f"{bcolors.OKBLUE}> Step: {em[0]}{bcolors.ENDC}")
        print(f"Args: {em[1]}")
        if em[2] > med_em:
            print(f"{bcolors.WARNING}Time: {em[2]:n}{bcolors.ENDC}")
        else:
            print(f"Time: {em[2]:n}")


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


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
        profile_neo4j(num_nodes=10, num_edges=15)
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

        Updated to MERGE the nodes and edges in separate queries; the 
        function `create_biocypher_edges_mod()` returns only the results
        of the edge query, not the node merge. This makes the query much
        slower for some reason (though Eager was successfully removed). 
        The culprit ProcedureCall performs many PageCacheHits; why?
        Additionally, the "Apply" step now also consumes time.
        """

    # cleanup
    delete_test_network()
    remove_constraint()
