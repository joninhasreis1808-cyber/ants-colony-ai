"""A1 · Deliberação com simulação N-vezes (roteiro de maestria).

Prova que o modo define QUANTOS cenários são simulados (FAST=1, DELIBERATE=3,
CRITICAL=5) e que a agregação usa a MEDIANA — não a média, que um único cenário
extremo sequestraria.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.cognitive.deliberation import (
    aggregate, choose, deliberate, simulate_scenarios,
)
from backend.cognitive.deliberation_mode import DeliberationMode, decide


@dataclass
class _Sim:
    plan: str
    expected_score: float
    risk: float


class FakeSimulator:
    """Simulador injetado: score varia por horizonte, para expor a mediana."""

    def __init__(self, scores):
        self.scores = scores
        self.calls = []

    def simulate(self, plan, steps=3):
        self.calls.append((plan, steps))
        s = self.scores[(steps - 1) % len(self.scores)]
        return _Sim(plan, s, round(1.0 - s, 3))


def test_modo_define_quantos_cenarios():
    assert decide("low", confidence=0.9).simulations == 1        # FAST
    assert decide("medium").simulations == 3                     # DELIBERATE
    assert decide("high").simulations == 5                       # CRITICAL
    assert decide("low", sensitive=True).simulations == 5         # sensível → CRITICAL


def test_simula_n_horizontes_diferentes():
    fake = FakeSimulator([0.5])
    sims = simulate_scenarios("plano", 3, fake)
    assert len(sims) == 3
    assert [c[1] for c in fake.calls] == [1, 2, 3]   # steps 1..n, não repetição


def test_agrega_por_mediana_e_nao_media():
    # scores 0.1, 0.2, 0.9 → mediana 0.2 (média seria 0.4)
    fake = FakeSimulator([0.1, 0.2, 0.9])
    out = deliberate("p", decide("medium"), fake)     # DELIBERATE = 3 cenários
    assert out["runs"] == 3
    assert out["score"] == 0.2                        # mediana, não 0.4


def test_um_cenario_catastrofico_nao_sequestra_a_decisao():
    # 5 cenários, um deles péssimo: a mediana ignora o extremo
    fake = FakeSimulator([0.8, 0.8, 0.8, 0.8, 0.0])
    out = deliberate("p", decide("high"), fake)       # CRITICAL = 5 cenários
    assert out["runs"] == 5
    assert out["score"] == 0.8


def test_fast_roda_um_unico_cenario():
    fake = FakeSimulator([0.7, 0.1, 0.1])
    out = deliberate("p", decide("low", confidence=0.9), fake)
    assert out["runs"] == 1 and out["score"] == 0.7


def test_choose_usa_a_mediana_para_eleger_o_plano():
    class PorPlano:
        def simulate(self, plan, steps=3):
            # plano A: 0.9,0.1,0.1 (mediana 0.1) | plano B: 0.5,0.5,0.5 (0.5)
            tabela = {"A": [0.9, 0.1, 0.1], "B": [0.5, 0.5, 0.5]}
            s = tabela[plan][(steps - 1) % 3]
            return _Sim(plan, s, round(1.0 - s, 3))
    out = choose(["A", "B"], decide("medium"), PorPlano())
    # pela média A venceria (0.366 vs 0.5 → não); pela mediana B vence claramente
    assert out["chosen"] == "B" and out["score"] == 0.5
    assert out["runs_por_plano"] == 3 and len(out["candidatos"]) == 2


def test_agregacao_vazia_e_honesta():
    assert aggregate([]) == {"score": 0.0, "risk": 1.0, "runs": 0}
    assert choose([], decide("medium")) is None


def test_simulador_real_funciona_sem_injecao():
    out = deliberate("fazer um backup simples", decide("high"))
    assert out["runs"] == 5 and 0.0 <= out["score"] <= 1.0
    assert out["mode"] == DeliberationMode.CRITICAL.value
