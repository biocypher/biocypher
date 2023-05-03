import pandas as pd
from ._create import BioCypherNode, BioCypherEdge

class Pandas:
    def __init__(self, ontology, translator, deduplicator):
        self.ontology = ontology
        self.translator = translator
        self.deduplicator = deduplicator

        self.dfs = {}

    def _separate_entity_types(self, entities):
        """
        Given mixed iterable of BioCypher objects, separate them into lists by
        type. Also deduplicates using the `Deduplicator` instance.
        """
        lists = {}
        for entity in entities:
            if not isinstance(entity, BioCypherNode) and not isinstance(entity, BioCypherEdge):
                raise TypeError(f"Expected a BioCypherNode or BioCypherEdge, got {type(entity)}.")
            
            if isinstance(entity, BioCypherNode):
                seen = self.deduplicator.node_seen(entity)
            elif isinstance(entity, BioCypherEdge):
                seen = self.deduplicator.edge_seen(entity)

            if seen:
                continue
            
            _type = entity.get_label()
            if not _type in lists:
                lists[_type] = []
            lists[_type].append(entity)

        return lists

    def add_tables(self, entities):
        """
        Add Pandas dataframes for each node and edge type in the input.
        """

        lists = self._separate_entity_types(entities)

        for _type, _entities in lists.items():
            self._add_entity_df(_type, _entities)

    def _add_entity_df(self, _type, _entities):
        df = pd.DataFrame(pd.json_normalize([node.get_dict() for node in _entities]))
        #replace "properties." with "" in column names
        df.columns = [col.replace("properties.", "") for col in df.columns]
        if _type not in self.dfs:
            self.dfs[_type] = df
        else:
            self.dfs[_type] = pd.concat([self.dfs[_type], df], ignore_index=True)
