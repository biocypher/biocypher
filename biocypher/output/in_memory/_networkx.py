import networkx as nx

from biocypher.output.in_memory._pandas import PandasKG


class NetworkxKG:
    def __init__(self, translator, deduplicator):
        self.translator = translator
        self.deduplicator = deduplicator
        self._pd = PandasKG(
            translator=self.translator,
            deduplicator=self.deduplicator,
        )
        self.KG = None

    def get_kg(self):
        if not self.KG:
            self.KG = self._create_networkx_kg()
        return self.KG

    def add_biocypher_nodes(self, nodes):
        self._pd.add_biocypher_nodes(nodes)
        return True

    def add_biocypher_edges(self, edges):
        self._pd.add_biocypher_edges(edges)
        return True

    def _create_networkx_kg(self) -> nx.DiGraph:
        self.KG = nx.DiGraph()
        all_dfs = self._pd.dfs
        node_dfs = [
            df
            for df in all_dfs.values()
            if df.columns.str.contains("node_id").any()
        ]
        edge_dfs = [
            df
            for df in all_dfs.values()
            if df.columns.str.contains("source_id").any()
            and df.columns.str.contains("target_id").any()
        ]
        for df in node_dfs:
            nodes = df.set_index("node_id").to_dict(orient="index")
            self.KG.add_nodes_from(nodes.items())
        for df in edge_dfs:
            edges = df.set_index(["source_id", "target_id"]).to_dict(
                orient="index"
            )
            self.KG.add_edges_from(
                (
                    (source, target, attrs)
                    for (source, target), attrs in edges.items()
                )
            )
        return self.KG
