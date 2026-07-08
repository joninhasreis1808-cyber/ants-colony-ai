"""Fixtures compartilhadas e dublês de teste da colmeia."""
from __future__ import annotations

import pytest

from backend.bots.learner import LearnerBot
from backend.core import SearchResult
from backend.hivemind.factory import build_hive
from backend.providers.base import SearchProvider
from backend.providers.router import ProviderRouter


class FakeProvider(SearchProvider):
    """Provider determinístico para testes (sem rede)."""

    name = "fake"

    def __init__(self, results=None, available=True, fail=False):
        self._results = results
        self._available = available
        self._fail = fail

    @property
    def available(self) -> bool:
        return self._available

    async def search(self, query: str, limit: int = 5):
        if self._fail:
            raise RuntimeError("provider falhou de propósito")
        if self._results is not None:
            return self._results[:limit]
        return [
            SearchResult(
                title=f"Resultado sobre {query}",
                url="https://exemplo.com/1",
                snippet=(
                    f"O tema {query} tem valor 42 e a relação x = 10 "
                    "aparece no gráfico principal."
                ),
                source=self.name,
            )
        ]


@pytest.fixture(autouse=True)
def reset_learner():
    """Zera o estado global de aprendizado antes de cada teste."""
    LearnerBot.reset()
    yield
    LearnerBot.reset()


@pytest.fixture
def fake_router():
    return ProviderRouter([FakeProvider()])


@pytest.fixture
def hive_and_memory(fake_router):
    hive, memory = build_hive(db_path=":memory:", router=fake_router)
    return hive, memory
