import networkx as nx

from biocypher._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode
from biocypher.output.in_memory._in_memory_kg import _InMemoryKG


class NetworkxKG(_InMemoryKG):
    def __init__(self, deduplicator):
        super().__init__()
        self.deduplicator = deduplicator
        self._KG = nx.DiGraph()

    def get_kg(self):
        return self._KG

    def add_edges(self, edges):
        """
        Add muliples edges to the networkx graph.

        Args:
            edges(Iterable): A collection of BiocypherEdge to add to the graph.

        """
        self._KG.add_edges_from(
            (
                edge.get_source_id(),
                edge.get_target_id(),
                {
                    **{
                        "relationship_id": edge.get_id(),
                        "relationship_label": edge.get_label(),
                    },
                    **edge.get_properties(),
                },
            )
            for edge in edges
            if self.deduplicator.edge_seen(edge) is False
        )

    def add_nodes(self, nodes):
        """
        Add multiple nodes to the networkx graph.
        If nodes contains BiocypherRelAsNode, also add associated edges to the networkx graph.
        Args:
            nodes: A collection of BiocypherNode or a collection of BiocypherNode and BiocypherRelasNode.

        """
        edges_to_add = []
        nodes_to_add = []
        for node in nodes:
            if isinstance(node, BioCypherNode):
                if self.deduplicator.node_seen(node) is False:
                    nodes_to_add.append(
                        (
                            node.get_id(),
                            {
                                **{"node_label": node.get_label()},
                                **node.get_properties(),
                            },
                        )
                    )
            else:
                if self.deduplicator.rel_as_node_seen(node) is False:
                    nodes_to_add.append(
                        (
                            node.get_node().get_id(),
                            {
                                **{"node_label": node.get_node().get_label()},
                                **(node.get_node().get_properties()),
                            },
                        )
                    )
                    edges_to_add.extend(
                        [node.get_source_edge(), node.get_target_edge()]
                    )

        if nodes_to_add:
            self._KG.add_nodes_from(nodes_to_add)
        if edges_to_add:
            self.add_edges(edges_to_add)
