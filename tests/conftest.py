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
    """Zera o estado global de aprendizado/segurança antes de cada teste."""
    from backend.memory.answer_cache import get_answer_cache

    def _reset_device():
        try:
            from backend.action.command_guard import get_command_guard
            from backend.monitoring.device_audit import get_device_audit
            from backend.permissions.device_scopes import get_device_scopes
            from backend.permissions.path_guard import get_path_guard
            from backend.security.panic import get_panic
            get_device_scopes().revoke_all()
            get_path_guard().clear()
            get_panic().reset()
            get_device_audit().clear()
            get_command_guard()  # garante singleton limpo
        except Exception:  # noqa: BLE001
            pass

    LearnerBot.reset()
    get_answer_cache().clear()   # isolamento: cache de respostas aprendidas
    _reset_device()              # isolamento: escopos/paths/pânico/auditoria
    yield
    LearnerBot.reset()
    get_answer_cache().clear()
    _reset_device()


@pytest.fixture
def fake_router():
    return ProviderRouter([FakeProvider()])


@pytest.fixture
def hive_and_memory(fake_router):
    hive, memory = build_hive(db_path=":memory:", router=fake_router)
    return hive, memory
