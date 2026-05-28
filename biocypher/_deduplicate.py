from ._create import BioCypherEdge, BioCypherNode, BioCypherRelAsNode
from ._logger import logger

logger.debug(f"Loading module {__name__}.")


class Deduplicator:
    """Singleton class responsible of deduplicating BioCypher inputs. Maintains
    sets/dictionaries of node and edge types and their unique identifiers.

    Nodes identifiers should be globally unique (represented as a set), while
    edge identifiers are only unique per edge type (represented as a dict of
    sets, keyed by edge type).

    Stores collection of duplicate node and edge identifiers and types for
    troubleshooting and to avoid overloading the log.
    """

    def __init__(self):
        self.seen_entity_fingerprints = set()
        self.seen_entity_types = set()
        self.duplicate_entity_ids = set()
        self.duplicate_entity_types = set()

        self.seen_relationship_fingerprints = set()
        self.seen_relationship_types = set()
        self.duplicate_relationship_ids = set()
        self.duplicate_relationship_types = set()

    def node_seen(self, entity: BioCypherNode) -> bool:
        """Adds a node to the instance and checks if it has been seen before.

        Args:
            node: BioCypherNode to be added.

        Returns:
            True if the node has been seen before, False otherwise.

        """
        entity_id = entity.get_id()
        entity_type = entity.get_label()
        self.seen_entity_types.add(entity_type)

        if entity_id in self.seen_entity_fingerprints:
            self.duplicate_entity_ids.add(entity_id)
            if entity_type not in self.duplicate_entity_types:
                logger.warning(f"Duplicate node type {entity_type} found. ")
                self.duplicate_entity_types.add(entity_type)
            return True

        self.seen_entity_fingerprints.add(entity_id)
        return False

    def edge_seen(self, relationship: BioCypherEdge) -> bool:
        """Adds an edge to the instance and checks if it has been seen before.

        Args:
            edge: BioCypherEdge to be added.

        Returns:
            True if the edge has been seen before, False otherwise.

        """
        # concatenate source and target if no id is present
        relationship_id = relationship.get_id() or f"{relationship.get_source_id()}_{relationship.get_target_id()}"
        relationship_type = relationship.get_type()
        relationship_fingerprint = f"{relationship_type}_{relationship_id}"
        self.seen_relationship_types.add(relationship_type)

        if relationship_fingerprint in self.seen_relationship_fingerprints:
            self.duplicate_relationship_ids.add(relationship_id)
            if relationship_type not in self.duplicate_relationship_types:
                logger.warning(f"Duplicate edge type {relationship_type} found. ")
                self.duplicate_relationship_types.add(relationship_type)
            return True

        self.seen_relationship_fingerprints.add(relationship_fingerprint)
        return False

    def rel_as_node_seen(self, rel_as_node: BioCypherRelAsNode) -> bool:
        """Adds a rel_as_node to the instance (one entity and two relationships)
        and checks if it has been seen before. Only the node is relevant for
        identifying the rel_as_node as a duplicate.

        Args:
            rel_as_node: BioCypherRelAsNode to be added.

        Returns:
            True if the rel_as_node has been seen before, False otherwise.

        """
        node = rel_as_node.get_node()
        # rel as node always has an id
        relationship_id = node.get_id()
        relationship_type = node.get_label()
        self.seen_relationship_types.add(relationship_type)

        if relationship_id in self.seen_relationship_fingerprints:
            self.duplicate_relationship_ids.add(relationship_id)
            if relationship_type not in self.duplicate_relationship_types:
                logger.warning(f"Duplicate edge type {relationship_type} found. ")
                self.duplicate_relationship_types.add(relationship_type)
            return True

        self.seen_relationship_fingerprints.add(relationship_id)
        return False

    def get_duplicate_nodes(self):
        """Function to return duplicate node types and IDs.

        Returns:
            tuple[set, set]: tuple of sets containing duplicate node types and IDs

        """
        return (
            self.duplicate_entity_types,
            self.duplicate_entity_ids,
        )

    def get_duplicate_edges(self):
        """Function to return duplicate edge types and IDs.

        Returns:
            tuple[set, set]: tuple of sets containing duplicate edge types and IDs

        """
        return (
            self.duplicate_relationship_types,
            self.duplicate_relationship_ids,
        )


class DiskBasedDeduplicator(Deduplicator):
    """Deduplicator that uses a disk-based index to track seen entities and relationships.

    This class is designed to handle large datasets that even storing IDs in memory would be impractical.
    It uses a Bloom filter to quickly check for potential duplicates and an LMDB database
    to store the actual fingerprints of seen entities and relationships.
    """

    def __init__(
        self,
        bloom_capacity: int = 1_000_000_000,
        bloom_error_rate: float = 1e-5,
        batch_size: int = 100_000,
        lmdb_path: str = None,
        lmdb_map_size: int = 1 << 40,
    ):
        """Initialise disk-backed deduplication indexes.

        Bloom RAM sizing:
        m = -(n * ln(p)) / (ln(2)^2) [bits]
        For n=1_000_000_000 and p=1e-5:
        m ~= 23_962_645_910 bits ~= 2_995_330_739 bytes ~= 2.79 GiB RAM.

        LMDB map size is configured in the backend as 1 TB virtual address space
        (sparse on disk; actual usage grows with written data).
        """
        super().__init__()
        from ._deduplicate_disk_index import BloomAcceleratedDiskBackedIndex

        _index = BloomAcceleratedDiskBackedIndex(
            bloom_capacity=bloom_capacity,
            bloom_error_rate=bloom_error_rate,
            batch_size=batch_size,
            lmdb_path=lmdb_path,
            lmdb_map_size=lmdb_map_size,
        )
        self.seen_entity_fingerprints = _index.namespace("entity")
        self.seen_relationship_fingerprints = _index.namespace("relationship")
