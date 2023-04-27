import pandas as pd
from ._create import BioCypherNode, BioCypherEdge, BioCypherRelAsNode

class Pandas:
    def __init__(self, ontology, translator):
        self.ontology = ontology
        self.translator = translator

        self.singleton_dfs = {}
        self.doublet_dfs = {}

    def node_table(self, nodes):
        """
        Return a pandas dataframe for one node type.
        """

        # TODO maybe cast to list first for efficiency

        for node in nodes:
            if not isinstance(node, BioCypherNode):
                raise TypeError(f"Expected a BioCypherNode, got {type(node)}.")
            
            _id = node.get_id()
            _type = node.get_label()
            _props = node.get_properties()

            if not _type in self.singleton_dfs:
                col_names = [_type]
                for prop in _props:
                    col_names.append(prop)
                self.singleton_dfs[_type] = pd.DataFrame(columns=col_names)
            else:
                col_names = self.singleton_dfs[_type].columns

            # create a row assigning properties to columns
            row = [_id]
            for col_name in col_names:
                if col_name == _type:
                    continue
                if col_name in _props:
                    row.append(_props[col_name])
                else:
                    row.append(None)

            self.singleton_dfs[_type].loc[len(self.singleton_dfs[_type])] = row

        return self.singleton_dfs

    def edge_table(self, edges):
        
        for edge in edges:
            if not isinstance(edge, BioCypherEdge):
                raise TypeError(f"Expected a BioCypherEdge, got {type(edge)}.")
            
            if isinstance(edge, BioCypherRelAsNode):
                raise NotImplementedError(
                    "Currently, only BioCypherEdge is supported as "
                    "relationship class in pandas.")
            
            _id = edge.get_id()
            _from = edge.get_source_id()
            _to = edge.get_target_id()
            _type = edge.get_label()
            _props = edge.get_properties()

            if not _type in self.doublet_dfs:
                col_names = [_type, "_from", "_to"]
                for prop in _props:
                    col_names.append(prop)
                self.doublet_dfs[_type] = pd.DataFrame(columns=col_names)
            else:
                col_names = self.doublet_dfs[_type].columns

            # create a row assigning properties to columns
            row = [_id, _from, _to]
            for col_name in col_names:
                if col_name in [_type, "_from", "_to"]:
                    continue
                if col_name in _props:
                    row.append(_props[col_name])
                else:
                    row.append(None)

            self.doublet_dfs[_type].loc[len(self.doublet_dfs[_type])] = row

        return self.doublet_dfs

