import pandas as pd

from biocypher.output.in_memory._in_memory_kg import _InMemoryKG


class PandasKG(_InMemoryKG):
    def __init__(self, deduplicator):
        super().__init__()  # keeping in spite of ABC not having __init__
        self.deduplicator = deduplicator

        self.dfs = {}

    def get_kg(self):
        return self.dfs

    def add_nodes(self, nodes):
        self.add_tables(nodes)

    def add_edges(self, edges):
        self.add_tables(edges)

    def add_tables(self, entities):
        """Add Pandas dataframes for each node and edge type in the input."""
        lists = self._separate_entity_types(entities)

        for _type, _entities in lists.items():
            self._add_entity_df(_type, _entities)

    def _add_entity_df(self, _type, _entities):
        df = pd.DataFrame(pd.json_normalize([node.get_dict() for node in _entities]))
        # replace "properties." with "" in column names
        df.columns = [col.replace("properties.", "") for col in df.columns]
        if _type not in self.dfs:
            self.dfs[_type] = df
        else:
            self.dfs[_type] = pd.concat([self.dfs[_type], df], ignore_index=True)
        return self.dfs[_type]
