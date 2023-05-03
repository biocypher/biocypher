from biocypher._pandas import Pandas
from biocypher._create import BioCypherNode, BioCypherEdge, BioCypherRelAsNode
import pytest

def _get_pd():
    return Pandas(
        ontology=None,
        translator=None,
    )

def test_pandas():
    _pd = _get_pd()
    assert _pd.dfs == {}

@pytest.mark.parametrize('l', [4], scope='module')
def test_nodes(_get_nodes):
    _pd = _get_pd()
    _pd.add_tables(_get_nodes)
    assert "protein" in _pd.dfs.keys()
    assert "microRNA" in _pd.dfs.keys()
    assert "score" in _pd.dfs["protein"].columns
    assert "p3" in _pd.dfs["protein"]["node_id"].values
    assert "taxon" in _pd.dfs["microRNA"].columns
    assert "m2" in _pd.dfs["microRNA"]["node_id"].values

    def node_gen():
        for node in _get_nodes:
            yield node

    _pd = _get_pd()

    _pd.add_tables(node_gen())
    assert "protein" in _pd.dfs.keys()

@pytest.mark.parametrize('l', [4], scope='module')
def test_duplicates(_get_nodes):
    _pd = _get_pd()
    nodes = _get_nodes + _get_nodes
    _pd.add_tables(nodes)
    assert len(_pd.dfs["protein"].node_id) == 4

@pytest.mark.parametrize('l', [8], scope='module')
def test_two_step_add(_get_nodes):
    _pd = _get_pd()
    _pd.add_tables(_get_nodes[:4])
    _pd.add_tables(_get_nodes[4:])
    assert len(_pd.dfs["protein"].node_id) == 8

@pytest.mark.parametrize('l', [4], scope='module')
def test_edges(_get_edges):
    _pd = _get_pd()
    _pd.add_tables(_get_edges)
    assert "PERTURBED_IN_DISEASE" in _pd.dfs.keys()
    assert "Is_Mutated_In" in _pd.dfs.keys()
    assert "source_id" in _pd.dfs["PERTURBED_IN_DISEASE"].columns
    assert "p3" in _pd.dfs["PERTURBED_IN_DISEASE"]["source_id"].values
    assert "target_id" in _pd.dfs["Is_Mutated_In"].columns
    assert "p1" in _pd.dfs["Is_Mutated_In"]["target_id"].values

    def edge_gen():
        for edge in _get_edges:
            yield edge

    _pd = _get_pd()

    _pd.add_tables(edge_gen())
    assert "PERTURBED_IN_DISEASE" in _pd.dfs.keys()