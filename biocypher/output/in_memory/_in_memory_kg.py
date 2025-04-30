from abc import ABC, abstractmethod

from biocypher._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode


class _InMemoryKG(ABC):
    """Abstract class for handling the in-memory Knowledge Graph instance.
    Specifics of the different in-memory implementations (e.g. csv, networkx)
    are implemented in the child classes. Any concrete in-memory implementation
    needs to implement at least:
    - add_nodes
    - add_edges
    - get_kg
    - _separate_entity_types

    Raises:
        NotImplementedError: InMemoryKG implementation must override 'add_nodes'
        NotImplementedError: InMemoryKG implementation must override 'add_edges'
        NotImplementedError: InMemoryKG implementation must override 'get_kg'
    """

    @abstractmethod
    def add_nodes(self, nodes):
        """Add nodes to the in-memory knowledge graph.

        Args:
            nodes (Iterable[BioCypherNode]): Iterable of BioCypherNode objects.
        """
        raise NotImplementedError("InMemoryKG implementation must override 'add_nodes'")

    @abstractmethod
    def add_edges(self, edges):
        """Add edges to the in-memory knowledge graph.

        Args:
            edges (Iterable[BioCypherEdge]): Iterable of BioCypherEdge objects.
        """
        raise NotImplementedError("InMemoryKG implementation must override 'add_edges'")

    @abstractmethod
    def get_kg(self):
        """Return the in-memory knowledge graph."""
        raise NotImplementedError("InMemoryKG implementation must override 'get_kg'")

    def _separate_entity_types(self, entities):
        """
        Given mixed iterable of BioCypher objects, separate them into lists by
        type. Also deduplicates using the `Deduplicator` instance.
        """
        lists = {}
        for entity in entities:
            if (
                not isinstance(entity, BioCypherNode)
                and not isinstance(entity, BioCypherEdge)
                and not isinstance(entity, BioCypherRelAsNode)
            ):
                raise TypeError(
                    "Expected a BioCypherNode / BioCypherEdge / " f"BioCypherRelAsNode, got {type(entity)}."
                )

            if isinstance(entity, BioCypherNode):
                seen = self.deduplicator.node_seen(entity)
            elif isinstance(entity, BioCypherEdge):
                seen = self.deduplicator.edge_seen(entity)
            elif isinstance(entity, BioCypherRelAsNode):
                seen = self.deduplicator.rel_as_node_seen(entity)

            if seen:
                continue

            if isinstance(entity, BioCypherRelAsNode):
                node = entity.get_node()
                source_edge = entity.get_source_edge()
                target_edge = entity.get_target_edge()

                _type = node.get_type()
                if _type not in lists:
                    lists[_type] = []
                lists[_type].append(node)

                _source_type = source_edge.get_type()
                if _source_type not in lists:
                    lists[_source_type] = []
                lists[_source_type].append(source_edge)

                _target_type = target_edge.get_type()
                if _target_type not in lists:
                    lists[_target_type] = []
                lists[_target_type].append(target_edge)
                continue

            _type = entity.get_type()
            if _type not in lists:
                lists[_type] = []
            lists[_type].append(entity)

        return lists
