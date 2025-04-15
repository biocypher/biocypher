import pytest
import scanpy as sc

def test_anndata(in_memory_anndata_kg):
    assert in_memory_anndata_kg.entities_by_type == {}