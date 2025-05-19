import pytest

from biocypher.output.in_memory._networkx import NetworkxKG
from biocypher.output.in_memory._pandas import PandasKG
from biocypher.output.in_memory._airr import AirrKG


@pytest.fixture(scope="function")
def in_memory_pandas_kg(deduplicator):
    in_memory_kg = PandasKG(
        deduplicator=deduplicator,
    )

    yield in_memory_kg


@pytest.fixture(scope="function")
def in_memory_networkx_kg(deduplicator):
    in_memory_kg = NetworkxKG(
        deduplicator=deduplicator,
    )

    yield in_memory_kg


@pytest.fixture(scope="function")
def in_memory_airr_kg(deduplicator):
    in_memory_kg = AirrKG(
        deduplicator=deduplicator,
    )

    yield in_memory_kg
