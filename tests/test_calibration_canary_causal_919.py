"""FASE 6 (9.19): calibração de confiança + canary interno + causal graph.

Prova, com números, que a colônia mede se sua confiança bate com a realidade,
que uma mudança sobe em degraus e volta atrás se falha, e que ela registra e
explica relações causa→efeito.
"""
from __future__ import annotations

from backend.evaluation.canary import STAGES, CanaryController
from backend.evaluation.causal_graph import CausalGraph
from backend.evaluation.confidence_calibration import ConfidenceCalibrator


# --- Calibração de confiança ------------------------------------------------

def test_calibrador_detecta_excesso_de_confianca():
    cal = ConfidenceCalibrator(bins=10, min_samples=5)
    # Dizia 0.9 mas só acerta 50% → mal calibrado (ECE alto).
    for i in range(10):
        cal.record(0.9, correct=(i % 2 == 0))
    assert cal.observed_rate(0.9) == 0.5
    assert cal.ece() > 0.3            # |0.9 - 0.5| domina


def test_calibrate_corrige_com_dado_e_passa_intacto_sem_dado():
    cal = ConfidenceCalibrator(min_samples=5)
    for _ in range(8):
        cal.record(0.8, correct=True)   # 0.8 sempre acerta → faixa confiável
    assert cal.calibrate(0.82) == 1.0   # corrigido para a taxa real (1.0)
    # Faixa sem amostra suficiente → devolve a confiança original.
    assert cal.calibrate(0.1) == 0.1


def test_calibrador_perfeito_tem_ece_baixo():
    cal = ConfidenceCalibrator(bins=2, min_samples=1)
    # faixa alta: acerta sempre; faixa baixa: erra sempre → bem calibrado
    for _ in range(10):
        cal.record(0.9, correct=True)
        cal.record(0.1, correct=False)
    assert cal.ece() < 0.15


# --- Canary interno ---------------------------------------------------------

def test_canary_comeca_em_5_por_cento():
    c = CanaryController()
    assert c.percentage == 5 and c.stage == 0 and not c.is_full


def test_canary_promove_por_degraus_com_sucesso():
    c = CanaryController(min_samples=10, success_threshold=0.9)
    for stage in STAGES[1:]:
        for _ in range(10):
            c.record(True)
        assert c.evaluate() == "promote"
        assert c.percentage == stage
    assert c.is_full


def test_canary_faz_rollback_quando_falha():
    c = CanaryController(min_samples=10, success_threshold=0.9)
    for _ in range(10):
        c.record(True)
    c.evaluate()                     # promove para 10%
    assert c.percentage == 10
    for _ in range(10):
        c.record(False)              # fatia se sai mal
    assert c.evaluate() == "rollback"
    assert c.percentage == 5 and c.rolled_back


def test_canary_hold_sem_amostra():
    c = CanaryController(min_samples=20)
    c.record(True)
    assert c.evaluate() == "hold"


def test_in_canary_e_estavel_para_a_mesma_chave():
    c = CanaryController()
    a = c.in_canary("missao-42")
    assert a == c.in_canary("missao-42")     # determinístico
    # 100% inclui todo mundo.
    while not c.is_full:
        c._promote()
    assert c.in_canary("qualquer") is True


# --- Causal graph -----------------------------------------------------------

def test_causal_registra_e_explica():
    g = CausalGraph()
    for _ in range(3):
        g.observe("web_bloqueada", "usou_memoria")
    g.observe("confianca_baixa", "usou_memoria")
    explic = g.explain("usou_memoria")
    assert explic[0]["cause"] == "web_bloqueada"      # mais forte primeiro
    assert explic[0]["observations"] == 3
    assert g.strength("web_bloqueada", "usou_memoria") > 0


def test_causal_recusa_autolaco():
    g = CausalGraph()
    try:
        g.observe("x", "x")
        assert False, "deveria recusar auto-laço"
    except ValueError:
        pass


def test_causal_sobe_ate_a_raiz():
    g = CausalGraph()
    g.observe("rede_caiu", "web_bloqueada")
    g.observe("web_bloqueada", "usou_memoria")
    assert g.root_causes("usou_memoria") == ["rede_caiu"]
