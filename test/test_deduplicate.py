import pytest

from biocypher._create import BioCypherEdge, BioCypherNode
from biocypher._deduplicate import Deduplicator, DiskBasedDeduplicator
from biocypher._deduplicate_disk_index import BloomAcceleratedDiskBackedIndex, _hash_id


@pytest.mark.parametrize(("length", "use_disk_index"), [(4, False), (4, True)], scope="module")
def test_duplicate_nodes(_get_nodes, use_disk_index):
    dedup = DiskBasedDeduplicator(batch_size=0) if use_disk_index else Deduplicator()
    nodes = _get_nodes
    nodes.append(
        BioCypherNode(
            node_id="p1",
            node_label="protein",
            properties={
                "name": "StringProperty1",
                "score": 4.32,
                "taxon": 9606,
                "genes": ["gene1", "gene2"],
            },
        ),
    )

    for node in nodes:
        dedup.node_seen(node)

    assert "protein" in dedup.duplicate_entity_types
    assert "p1" in dedup.duplicate_entity_ids


@pytest.mark.parametrize(("length", "use_disk_index"), [(4, False), (4, True)], scope="module")
def test_get_duplicate_nodes(_get_nodes, use_disk_index):
    dedup = DiskBasedDeduplicator(batch_size=0) if use_disk_index else Deduplicator()
    nodes = _get_nodes
    nodes.append(
        BioCypherNode(
            node_id="p1",
            node_label="protein",
            properties={
                "name": "StringProperty1",
                "score": 4.32,
                "taxon": 9606,
                "genes": ["gene1", "gene2"],
            },
        ),
    )

    for node in nodes:
        dedup.node_seen(node)

    duplicates = dedup.get_duplicate_nodes()
    types = duplicates[0]
    ids = duplicates[1]

    assert "protein" in types
    assert "p1" in ids


@pytest.mark.parametrize(("length", "use_disk_index"), [(4, False), (4, True)], scope="module")
def test_duplicate_edges(_get_edges, use_disk_index):
    dedup = DiskBasedDeduplicator(batch_size=0) if use_disk_index else Deduplicator()
    edges = _get_edges
    edges.append(
        BioCypherEdge(
            relationship_id="mrel2",
            source_id="m2",
            target_id="p3",
            relationship_label="Is_Mutated_In",
            properties={
                "score": 4.32,
                "taxon": 9606,
                "genes": ["gene1", "gene2"],
            },
        ),
    )
    # this will fail if we go beyond concatenation of ids

    for edge in edges:
        dedup.edge_seen(edge)

    assert "Is_Mutated_In" in dedup.duplicate_relationship_types
    assert ("mrel2") in dedup.duplicate_relationship_ids


@pytest.mark.parametrize(("length", "use_disk_index"), [(4, False), (4, True)], scope="module")
def test_get_duplicate_edges(_get_edges, use_disk_index):
    dedup = DiskBasedDeduplicator(batch_size=0) if use_disk_index else Deduplicator()
    edges = _get_edges
    edges.append(
        BioCypherEdge(
            relationship_id="mrel2",
            source_id="m2",
            target_id="p3",
            relationship_label="Is_Mutated_In",
            properties={
                "score": 4.32,
                "taxon": 9606,
                "genes": ["gene1", "gene2"],
            },
        ),
    )
    # this will fail if we go beyond concatenation of ids

    for edge in edges:
        dedup.edge_seen(edge)

    duplicates = dedup.get_duplicate_edges()
    types = duplicates[0]
    ids = duplicates[1]

    assert "Is_Mutated_In" in types
    assert ("mrel2") in ids


_SMALL = {
    "bloom_capacity": 10_000,
    "bloom_error_rate": 1e-5,
    "batch_size": 100,
    "lmdb_map_size": 10 * 1024 * 1024,  # 10 MiB
}


class TestBloomAcceleratedDiskBasedIndex:
    def test_layer1_pending_set_found_before_flush(self, tmp_path):
        idx = BloomAcceleratedDiskBackedIndex(lmdb_path=str(tmp_path), **_SMALL)
        handle = idx.namespace("entity")

        handle.add("node1")

        key = _hash_id("entity:node1")
        assert key in idx._pending_set, "key must be in pending_set"
        assert "node1" in handle, "__contains__ must return True via pending_set"

    def test_layer1_pending_set_not_in_bloom_before_flush(self, tmp_path):
        idx = BloomAcceleratedDiskBackedIndex(lmdb_path=str(tmp_path), **_SMALL)
        handle = idx.namespace("entity")

        handle.add("node1")

        key = _hash_id("entity:node1")
        assert key not in idx._bloom, "Bloom must not be updated before flush"

    def test_layer2_bloom_updated_after_flush(self, tmp_path):
        idx = BloomAcceleratedDiskBackedIndex(lmdb_path=str(tmp_path), **_SMALL)
        handle = idx.namespace("entity")

        handle.add("node1")
        idx.flush()

        key = _hash_id("entity:node1")
        assert key in idx._bloom, "Bloom must contain key after flush"
        assert len(idx._pending_keys) == 0, "pending_keys must be empty after flush"

    def test_layer2_item_found_via_bloom_after_flush(self, tmp_path):
        idx = BloomAcceleratedDiskBackedIndex(lmdb_path=str(tmp_path), **_SMALL)
        handle = idx.namespace("entity")

        handle.add("node1")
        idx.flush()

        assert "node1" in handle

    def test_layer3_lmdb_written_after_flush(self, tmp_path):
        idx = BloomAcceleratedDiskBackedIndex(lmdb_path=str(tmp_path), **_SMALL)
        handle = idx.namespace("entity")

        handle.add("node1")
        idx.flush()

        key = _hash_id("entity:node1")
        with idx._lmdb_env.begin(write=False) as txn:
            assert txn.get(key) is not None, "key must be committed to LMDB"

    def test_layer3_lmdb_resolves_bloom_false_positive(self, tmp_path):
        idx = BloomAcceleratedDiskBackedIndex(lmdb_path=str(tmp_path), **_SMALL)

        phantom_key = _hash_id("entity:phantom")
        idx._bloom.add(phantom_key)  # inject into Bloom only, bypassing LMDB

        assert not idx._seen(phantom_key), "LMDB must correct the Bloom false positive"

    def test_layer3_lmdb_not_queried_on_bloom_miss(self, tmp_path):
        idx = BloomAcceleratedDiskBackedIndex(lmdb_path=str(tmp_path), **_SMALL)
        handle = idx.namespace("entity")

        class _FailIfUsedEnv:
            def begin(self, *args, **kwargs):
                raise AssertionError("LMDB should not be queried on Bloom miss")

            def close(self):
                pass

        idx._lmdb_env = _FailIfUsedEnv()

        assert "never_added" not in handle

    def test_namespace_isolation(self, tmp_path):
        idx = BloomAcceleratedDiskBackedIndex(lmdb_path=str(tmp_path), **_SMALL)
        h_entity = idx.namespace("entity")
        h_rel = idx.namespace("relationship")

        h_entity.add("id1")

        assert "id1" in h_entity
        assert "id1" not in h_rel, "relationship namespace must not see entity keys"

    def test_auto_flush_at_batch_size(self, tmp_path):
        idx = BloomAcceleratedDiskBackedIndex(
            lmdb_path=str(tmp_path),
            bloom_capacity=10_000,
            bloom_error_rate=1e-5,
            batch_size=5,
            lmdb_map_size=10 * 1024 * 1024,
        )
        handle = idx.namespace("entity")

        for i in range(5):
            handle.add(f"node{i}")

        assert len(idx._pending_keys) == 0, "auto-flush must clear pending_keys"
        key = _hash_id("entity:node0")
        assert key in idx._bloom, "Bloom must be updated after auto-flush"
        with idx._lmdb_env.begin(write=False) as txn:
            assert txn.get(key) is not None, "LMDB must contain key after auto-flush"
