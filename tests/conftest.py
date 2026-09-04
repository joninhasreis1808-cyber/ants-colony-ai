"""Fixtures compartilhadas e dublês de teste da colmeia."""
from __future__ import annotations

import os
import tempfile

# DNA, cultura, confiança, feedback e LTM caem em SQLite real (`ants.db` no
# cwd) sempre que ANTS_DB não está definida — os singletons de processo que os
# guardam (`get_dna()`, `get_feedback_learner()`, `get_ltm()`, ...) são
# construídos na PRIMEIRA chamada e ficam presos a esse caminho até serem
# resetados. Sem isto, rodar a suíte duas vezes (ou só em ordem diferente)
# lia estado real deixado por uma execução anterior, no arquivo do próprio
# repositório. Setado antes de qualquer import de `backend.*` abrir um desses
# singletons — `setdefault` não atropela quem já exportou ANTS_DB de propósito.
os.environ.setdefault(
    "ANTS_DB", os.path.join(tempfile.mkdtemp(prefix="ants-test-db-"), "ants.db")
)

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
            import backend.action.action_flow as _af
            _af._PENDING.clear()
            from backend.action.verify_cycle import reset_verify_cycle
            reset_verify_cycle()  # isolamento: contador de falhas por missão
            from backend.hivemind.colony_state import reset_colony_state_machine
            reset_colony_state_machine()  # isolamento: última atividade real
            from backend.security.site_safety import reset_site_safety_checker
            reset_site_safety_checker()  # isolamento: assinaturas aprendidas
        except Exception:  # noqa: BLE001
            pass

    def _reset_ab_experiments():
        # backend.evaluation.ab_experiment._INSTANCE é global de processo e não
        # tem dono natural em nenhum outro reset — sem isto, um experimento
        # deixado ATIVO por um teste (ex.: test_ab_experiment_a4.py) vaza para
        # qualquer missão real de outro arquivo com a mesma `signature(goal)`
        # (ex.: toda pergunta "quanto é N * M" cai na mesma assinatura "quanto"),
        # trocando a rota escolhida por um teste que nem sabe que o A/B existe.
        try:
            from backend.evaluation.ab_experiment import get_ab_registry
            get_ab_registry().reset()
        except Exception:  # noqa: BLE001
            pass

    def _reset_calibrator():
        # get_calibrator() (B3) acumula (confiança prevista, acertou?) de TODA
        # missão real da suíte — um teste que devolve uma resposta exata com
        # confiança 1.0 podia sair com confiança corrigida para baixo por
        # missões de outros arquivos, sem relação nenhuma com este cálculo.
        # get_route_calibrator() (Precisão Offline v1 · item 3) tem o mesmo
        # risco, só que por ROTA: um teste que força várias respostas erradas
        # via "computation" mudaria o success_probability dessa rota para
        # QUALQUER outro teste que rode a Cartógrafa depois, em outro arquivo.
        try:
            from backend.evaluation.confidence_calibration import (
                get_calibrator, get_route_calibrator,
            )
            get_calibrator().reset()
            get_route_calibrator().reset()
        except Exception:  # noqa: BLE001
            pass

    def _reset_permissions():
        # backend.api.deps.PERMISSIONS é outro singleton de processo, com nível
        # por usuário nunca zerado — um teste que concede nível 5 a "jonas"
        # (ex.: test_security_auth_93.py) deixava isso vazar para QUALQUER
        # outro teste que usasse o mesmo user_id, inclusive fora do arquivo.
        try:
            from backend.api.deps import PERMISSIONS
            PERMISSIONS.reset()
        except Exception:  # noqa: BLE001
            pass

    def _reset_observer():
        # backend.api.routes.organism.OBSERVER é um singleton de módulo criado
        # na importação — achados de um teste (POST /organism/observer/analyze)
        # ficavam visíveis para qualquer teste depois, inclusive o que prova
        # que "sem snapshot, nenhum achado" (interface nunca inventa).
        try:
            from backend.api.routes.organism import OBSERVER
            OBSERVER.clear()
        except Exception:  # noqa: BLE001
            pass

    def _reset_experience():
        # ErrorMemory/StrategyMemory (B3) também são singletons de processo, e
        # `_similar()` usa Jaccard ≥ 0.5 nas palavras do objetivo — com filtro
        # de tokens ≥ 3 letras, TODO "quanto é N * M" vira só o token "quanto",
        # então um sucesso/fracasso registrado por um teste vira bônus/castigo
        # para a rota escolhida por outro teste, em outro arquivo, sem relação
        # nenhuma. Mesma classe de defeito do A/B acima.
        try:
            from backend.cognition.experience import (
                get_error_memory, get_strategy_memory,
            )
            get_error_memory().clear()
            get_strategy_memory().clear()
        except Exception:  # noqa: BLE001
            pass

    def _reset_durable_singletons():
        # DNA, cultura, confiança, feedback e LTM já tinham `reset_X()` prontos
        # — construídos exatamente para isto — mas nenhum estava plugado aqui.
        # Ligado a um fluxo (o teste próprio de cada um) ≠ o fluxo receber o
        # que a peça precisa (isolamento em TODO teste da suíte); mesma lição
        # do defeito #92, agora na infraestrutura de teste em vez do produto.
        try:
            from backend.hivemind.culture_store import reset_culture
            from backend.hivemind.dna_store import reset_dna
            from backend.learning.feedback_store import reset_feedback_learner
            from backend.memory.ltm_store import reset_ltm
            from backend.permissions.trust_store import reset_trust
            reset_dna()
            reset_culture()
            reset_trust()
            reset_feedback_learner()
            reset_ltm()
        except Exception:  # noqa: BLE001
            pass

    LearnerBot.reset()
    get_answer_cache().clear()   # isolamento: cache de respostas aprendidas
    _reset_device()              # isolamento: escopos/paths/pânico/auditoria
    _reset_ab_experiments()      # isolamento: experimentos A/B entre testes
    _reset_calibrator()          # isolamento: calibração de confiança (B3)
    _reset_experience()          # isolamento: memória de estratégia/erro (B3)
    _reset_permissions()         # isolamento: níveis/revogações por usuário
    _reset_observer()            # isolamento: achados do Observador
    _reset_durable_singletons()  # isolamento: DNA/cultura/confiança/feedback/LTM
    yield
    LearnerBot.reset()
    get_answer_cache().clear()
    _reset_device()
    _reset_ab_experiments()
    _reset_calibrator()
    _reset_experience()
    _reset_permissions()
    _reset_observer()
    _reset_durable_singletons()


@pytest.fixture
def fake_router():
    return ProviderRouter([FakeProvider()])


@pytest.fixture
def hive_and_memory(fake_router):
    hive, memory = build_hive(db_path=":memory:", router=fake_router)
    return hive, memory
