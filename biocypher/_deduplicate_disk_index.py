from __future__ import annotations

import contextlib
import shutil
import tempfile

from pathlib import Path

import lmdb
import xxhash

from rbloom import Bloom

from ._logger import logger

logger.debug(f"Loading module {__name__}.")


def _hash_id(raw: str) -> bytes:
    """Return the 16-byte xxh3_128 digest of *raw*."""
    return xxhash.xxh3_128(raw).digest()


class BloomAcceleratedDiskBackedIndex:
    """Bloom-accelerated LMDB index.

    Stores 16-byte xxh3_128 hashes. Not used directly — obtain a namespaced
    handle via `namespace` and interact through that.

    Three-layer lookup:

    1. **pending_set** – Python set for the current unflushed batch.
    2. **Bloom filter** – skips LMDB on definite misses.
    3. **LMDB** – authoritative on-disk store.
    """

    def __init__(
        self,
        *,
        bloom_capacity: int,
        bloom_error_rate: float,
        batch_size: int,
        lmdb_path: str | None,
        lmdb_map_size: int,
    ):
        if lmdb_path is None:
            self._tmp_dir: str | None = tempfile.mkdtemp(prefix="biocypher-dedup-")
            lmdb_path = self._tmp_dir
        else:
            self._tmp_dir = None
            Path(lmdb_path).mkdir(parents=True, exist_ok=True)

        self.batch_size = batch_size

        # LMDB configuration tuned for runtime performance at the cost of
        # durability guarantees, which are not needed here.
        self._lmdb_env = lmdb.open(
            lmdb_path,
            map_size=lmdb_map_size,
            subdir=True,
            readonly=False,
            metasync=False,
            sync=False,
            map_async=True,
            writemap=True,
            readahead=False,
        )
        self._bloom: Bloom = Bloom(bloom_capacity, bloom_error_rate)
        self._pending_set: set[bytes] = set()
        self._pending_keys: list[bytes] = []

    def _seen(self, hash_key: bytes) -> bool:
        if hash_key in self._pending_set:
            return True
        if hash_key not in self._bloom:
            return False
        with self._lmdb_env.begin(write=False) as txn:
            return txn.get(hash_key) is not None

    def _add(self, hash_key: bytes) -> None:
        self._pending_set.add(hash_key)
        self._pending_keys.append(hash_key)
        if len(self._pending_keys) >= self.batch_size:
            self.flush()

    def namespace(self, prefix: str) -> IndexHandle:
        """Return a handle that scopes all keys under *prefix*."""
        return IndexHandle(self, prefix)

    def flush(self) -> None:
        """Commit pending hashes to LMDB, update the Bloom filter, clear batch."""
        if not self._pending_keys:
            return
        with self._lmdb_env.begin(write=True) as txn:
            for key in self._pending_keys:
                txn.put(key, b"")
        for key in self._pending_keys:
            self._bloom.add(key)
        self._pending_set.clear()
        self._pending_keys.clear()

    def __del__(self) -> None:
        with contextlib.suppress(Exception):
            self.flush()
        with contextlib.suppress(Exception):
            self._lmdb_env.close()
        if self._tmp_dir:
            with contextlib.suppress(Exception):
                shutil.rmtree(self._tmp_dir, ignore_errors=True)


class IndexHandle:
    """Set-like handle into a `BloomAcceleratedDiskBasedIndex` namespace.

    All items are prefixed with `prefix` before hashing, keeping keys from
    different handles disjoint within the shared index.

    Supports ``item in handle`` and ``handle.add(item)``.
    """

    def __init__(self, index: BloomAcceleratedDiskBackedIndex, prefix: str) -> None:
        self._index = index
        self._prefix = prefix

    def __contains__(self, item: str) -> bool:
        return self._index._seen(_hash_id(f"{self._prefix}:{item}"))

    def add(self, item: str) -> None:
        self._index._add(_hash_id(f"{self._prefix}:{item}"))
