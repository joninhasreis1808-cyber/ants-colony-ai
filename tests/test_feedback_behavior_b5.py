"""B5 · Feedback que MUDA comportamento (roteiro de maestria).

O `FeedbackLearner` existia, guardava pesos e bloqueios com carinho, e era
consultado por **um lugar só**: `CognitiveOrchestrator.choose_strategy`, que só
roda pelas rotas `/mind`. O caminho que de fato executa as missões — Cartógrafa,
planejador, colmeia — nunca perguntava nada ao dono.

Na prática: o dono podia dizer "nunca use web_search" e as missões continuavam
usando web_search. Aqui provamos que a opinião dele passou a valer onde a rota é
escolhida — e que a colônia declara quando não consegue obedecer.
"""
from __future__ import annotations

import asyncio

from backend.cognition.cartographer import get_cartographer
from backend.cognition.epistemic_label import build
from backend.cognition.feedback_bias import (
    _MAX_BIAS, apply_to_routes, blocked_routes, route_bias,
)
from backend.cognition.planner import get_planner
from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.learning.feedback_store import (
    get_feedback_learner, reset_feedback_learner,
)
from backend.memory.long_term_memory import LongTermMemory
from backend.memory.schemas import MemoryInput

_GOAL = "comparar precos de telescopios amadores"


def _limpo():
    reset_feedback_learner()
    return get_feedback_learner()


class _Rota:
    def __init__(self, name, base, available=True):
        self.name, self._base, self.available, self.bias = name, base, available, 0.0

    def score(self):
        return 0.0 if not self.available else self._base + self.bias


# ===  sem opiniao, nada muda  ================================================

def test_sem_opiniao_o_vies_e_exatamente_zero():
    _limpo()
    assert route_bias("web_search") == 0.0
    assert blocked_routes(["web_search", "memory"]) == []


def test_sem_opiniao_a_rota_escolhida_e_a_de_hoje():
    _limpo()
    antes = get_planner().plan(_GOAL).route.name
    assert get_planner().plan(_GOAL).route.name == antes
    assert get_planner().plan(_GOAL).feedback["biased"] == {}


# ===  proibir e VETO, nao desempate  =========================================

def test_proibir_torna_a_rota_indisponivel():
    l = _limpo()
    escolhida = get_planner().plan(_GOAL).route.name
    l.forbid(escolhida)
    novo = get_planner().plan(_GOAL)
    assert novo.route.name != escolhida, "o veto tem que trocar a rota"
    assert novo.feedback["blocked"] == [escolhida]
    assert novo.feedback["honored"] is True


def test_o_veto_vence_ate_uma_rota_muito_melhor():
    """Veto não é peso: nenhum score derrota uma proibição explícita."""
    _limpo().forbid("otima")
    rotas = [_Rota("otima", 0.99), _Rota("mediana", 0.30)]
    rel = apply_to_routes(rotas)
    assert rel["blocked"] == ["otima"]
    assert rotas[0].name == "mediana"
    assert [r for r in rotas if r.name == "otima"][0].available is False


def test_aprovar_e_rejeitar_viram_vies_proporcional():
    l = _limpo()
    for _ in range(4):
        l.approve("memory")
    assert route_bias("memory") > 0
    l2 = _limpo()
    l2.reject("memory")
    assert route_bias("memory") < 0


def test_o_vies_da_opiniao_tem_teto_simetrico():
    """Opinião pesa e não atropela — e o "não" não vale menos que o "sim".

    O FeedbackLearner satura `approve` em 3.0 e `reject` em 0.0. Uma regra
    linear crua faria a rejeição máxima chegar a METADE da aprovação máxima, só
    por causa dessa assimetria de implementação. Os dois lados são normalizados
    pelo próprio alcance para que isso não aconteça.
    """
    l = _limpo()
    for _ in range(50):
        l.approve("memory")
    assert route_bias("memory") == _MAX_BIAS
    l2 = _limpo()
    for _ in range(50):
        l2.reject("memory")
    assert route_bias("memory") == -_MAX_BIAS


def test_rota_vetada_nao_recebe_vies_porque_nem_disputa():
    l = _limpo()
    l.approve("memory")
    l.forbid("memory")
    assert route_bias("memory") == 0.0


# ===  o caso incomodo: o dono proibiu tudo  ==================================

def test_proibir_tudo_nao_emudece_a_colonia_e_e_DECLARADO():
    """Desobedecer em silêncio seria pior que qualquer das saídas ruins."""
    l = _limpo()
    disponiveis = [r.name for r in get_cartographer().discover(_GOAL, None)
                   if r.available]
    for r in disponiveis:
        l.forbid(r)
    p = get_planner().plan(_GOAL)
    assert p.route is not None, "a colônia não pode ficar muda"
    assert p.feedback["honored"] is False
    assert p.feedback["blocked"] == [], "não fingiu ter honrado o veto"
    assert "não conseguiu obedecer" in p.feedback["note"]
    assert "silêncio seria pior" in p.feedback["note"]
    _limpo()


def test_a_proibicao_nao_honrada_vira_LIMITE_no_rotulo_epistemico():
    r = {"provenance": {"source": "web_search"}, "confidence": 0.8,
         "feedback": {"honored": False, "note": "o dono proibiu X, mas ..."}}
    assert any("o dono proibiu X" in l for l in build(r).limits)


def test_o_veto_honrado_tambem_aparece_no_rotulo():
    r = {"provenance": {"source": "web_search"}, "confidence": 0.8,
         "feedback": {"honored": True, "blocked": ["deep_research"]}}
    assert any("vetadas pelo dono" in l for l in build(r).limits)


# ===  o veto alcanca a memoria propria no caminho do chat  ==================

def _ltm(*c):
    ltm = LongTermMemory()
    for x in c:
        ltm.remember(MemoryInput(content=x, source="bot", tags=["task_outcome"],
                                 related_tasks=["t"], emotional_weight=0.4))
    return ltm


_CAFE = "Tarefa 'torra': o cafe da colonia e torrado a 210 graus por 12 minutos"


def test_sem_veto_a_missao_usa_a_memoria_propria():
    _limpo()
    hive, _ = build_hive(db_path=":memory:", ltm=_ltm(_CAFE))
    t = Task(goal="a que temperatura o cafe da colonia e torrado")
    asyncio.run(hive.solve(t))
    assert t.result["provenance"]["source"] == "own_memory"


def test_vetar_own_memory_tira_a_memoria_propria_da_missao():
    _limpo().forbid("own_memory")
    hive, _ = build_hive(db_path=":memory:", ltm=_ltm(_CAFE))
    t = Task(goal="a que temperatura o cafe da colonia e torrado")
    asyncio.run(hive.solve(t))
    assert t.result["provenance"]["source"] != "own_memory"
    assert "grounding" not in t.result
    _limpo()


# ===  a missao carrega o relatorio  ==========================================

def test_o_desfecho_da_missao_carrega_o_que_o_feedback_fez():
    from backend.hivemind.mission_runner import run_mission
    from backend.memory.shared_memory import SharedMemory
    l = _limpo()
    l.forbid("computation")
    out = asyncio.run(run_mission("quanto é 9 * 9", SharedMemory(":memory:")))
    assert "feedback" in out
    assert out["feedback"]["blocked"] == ["computation"]
    assert out["route"]["name"] != "computation"
    _limpo()


def test_o_feedback_nunca_derruba_o_plano():
    _limpo()
    assert get_planner().plan("qualquer objetivo").route is not None
