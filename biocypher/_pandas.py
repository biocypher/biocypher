import pandas as pd
from ._create import BioCypherNode, BioCypherEdge, BioCypherRelAsNode

class Pandas:
    def __init__(self, ontology, translator):
        self.ontology = ontology
        self.translator = translator

        self.lists = {}
        self.dfs = {}

    def _separate_entity_types(self, entities):
        """
        Given mixed iterable of BioCypher objects, separate them into lists by
        type.
        """
        for entity in entities:
            if not isinstance(entity, BioCypherNode) and not isinstance(entity, BioCypherEdge):
                raise TypeError(f"Expected a BioCypherNode or BioCypherEdge, got {type(entity)}.")
            
            _type = entity.get_label()
            if not _type in self.lists:
                self.lists[_type] = []
            self.lists[_type].append(entity)

    def add_tables(self, entities):
        """
        Add Pandas dataframes for each node and edge type in the input.
        """

        self._separate_entity_types(entities)

        for _type, _entities in self.lists.items():
            self._add_entity_df(_type, _entities)

    def _add_entity_df(self, _type, _entities):
        df = pd.DataFrame(pd.json_normalize([node.get_dict() for node in _entities]))
            #replace "properties." with "" in column names
        df.columns = [col.replace("properties.", "") for col in df.columns]
        self.dfs[_type] = df
