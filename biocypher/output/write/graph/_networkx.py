import pickle

import networkx as nx

from biocypher._logger import logger
from biocypher.output.write._writer import _Writer
from biocypher.output.write.relational._csv import _PandasCSVWriter


class _NetworkXWriter(_Writer):
    """
    Class for writing node and edges to a networkx DiGraph.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.csv_writer = _PandasCSVWriter(*args, write_to_file=False, **kwargs)
        self.G = nx.DiGraph()

    def _construct_import_call(self) -> str:
        """Function to construct the Python code to load all node and edge csv files again into Pandas dfs.

        Returns:
            str: Python code to load the csv files into Pandas dfs.
        """
        logger.info(
            f"Writing networkx {self.G} to pickle file networkx_graph.pkl."
        )
        with open(f"{self.output_directory}/networkx_graph.pkl", "wb") as f:
            pickle.dump(self.G, f)

        import_call = "import pickle\n"
        import_call += "with open('./networkx_graph.pkl', 'rb') as f:\n\tG_loaded = pickle.load(f)"
        return import_call

    def _get_import_script_name(self) -> str:
        """Function to return the name of the import script."""
        return "import_networkx.py"

    def _write_node_data(self, nodes) -> bool:
        passed = self.csv_writer._write_entities_to_file(nodes)
        self.add_to_networkx()
        return passed

    def _write_edge_data(self, edges) -> bool:
        passed = self.csv_writer._write_entities_to_file(edges)
        self.add_to_networkx()
        return passed

    def add_to_networkx(self) -> bool:
        all_dfs = self.csv_writer.stored_dfs
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
            self.G.add_nodes_from(nodes.items())
        for df in edge_dfs:
            edges = df.set_index(["source_id", "target_id"]).to_dict(
                orient="index"
            )
            self.G.add_edges_from(
                (
                    (source, target, attrs)
                    for (source, target), attrs in edges.items()
                )
            )
        return True
