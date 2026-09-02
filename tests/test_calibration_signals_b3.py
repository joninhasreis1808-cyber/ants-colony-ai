"""B3 · Calibração com sinais REAIS (roteiro de maestria).

Dois defeitos existiam ao mesmo tempo: o calibrador era alimentado por um único
sinal — o mais fraco de todos, a colônia conferindo a si mesma — e o
`calibrate()` **nunca era chamado por ninguém**. Ele aprendia e o aprendizado
não chegava a lugar nenhum.

Aqui provamos as três camadas de sinal, o peso de cada uma, e que a confiança
exibida passa de fato pela correção — só onde há amostra para sustentá-la.
"""
from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

import backend.evaluation.confidence_calibration as CC
import backend.evaluation.human_feedback as HF
from backend.api.main import app
from backend.core import Task
from backend.evaluation.confidence_calibration import ConfidenceCalibrator
from backend.evaluation.correctness_signal import WEIGHTS, best_signal
from backend.hivemind.factory import build_hive
from backend.hivemind.hive import Hivemind

client = TestClient(app)


def _fresh():
    CC._INSTANCE = None
    HF._INSTANCE = None
    return CC.get_calibrator()


# ===  as tres camadas de sinal  ==============================================

def test_confirmacao_humana_e_o_sinal_mais_forte():
    s = best_signal(human=True, cross_verdict="divergente", grounded=False)
    assert s.correct is True and s.strength == "forte"
    assert s.weight == WEIGHTS["forte"] == 3.0
    assert "humana" in s.basis


def test_o_humano_pode_dizer_que_errou_mesmo_com_tudo_indicando_acerto():
    s = best_signal(human=False, cross_verdict="confirmado", grounded=True)
    assert s.correct is False and s.strength == "forte"


def test_verificacao_cruzada_vem_depois_do_humano_e_antes_da_auto_consistencia():
    s = best_signal(cross_verdict="confirmado", grounded=False)
    assert s.correct is True and s.strength == "medio"
    assert WEIGHTS["fraco"] < s.weight < WEIGHTS["forte"]


def test_divergencia_e_sinal_NEGATIVO_nao_ausencia_de_sinal():
    """Contradição ensina tanto quanto confirmação — e com o mesmo peso."""
    s = best_signal(cross_verdict="divergente", grounded=True)
    assert s.correct is False and s.strength == "medio"
    assert "alta demais" in s.basis


def test_sem_nada_melhor_sobra_a_auto_consistencia_declarada_como_fraca():
    s = best_signal(grounded=True, escalate_human=False)
    assert s.correct is True and s.strength == "fraco"
    assert "conferindo a si mesma" in s.basis
    assert best_signal(grounded=True, escalate_human=True).correct is False
    assert best_signal(grounded=False).correct is False


def test_a_colonia_usa_o_melhor_sinal_nunca_a_soma():
    """Somar as camadas contaria a mesma missão três vezes."""
    s = best_signal(human=True, cross_verdict="confirmado", grounded=True)
    assert s.weight == WEIGHTS["forte"], "um peso só, o do melhor sinal"


# ===  o calibrador ponderado  ================================================

def test_o_peso_move_a_calibracao_de_verdade():
    forte = ConfidenceCalibrator(bins=2, min_samples=1)
    forte.record(0.9, correct=False, weight=3.0)
    forte.record(0.9, correct=True, weight=1.0)
    # 1 acerto de peso 1 contra 1 erro de peso 3 -> taxa 0.25, nao 0.5
    assert forte.observed_rate(0.9) == 0.25


def test_peso_padrao_reproduz_o_comportamento_antigo():
    c = ConfidenceCalibrator(bins=2, min_samples=1)
    c.record(0.9, correct=True)
    c.record(0.9, correct=False)
    assert c.observed_rate(0.9) == 0.5
    assert c.total == 2 and c.mass == 2.0


def test_total_conta_missoes_e_massa_conta_influencia():
    c = ConfidenceCalibrator(bins=2, min_samples=1)
    c.record(0.9, correct=True, weight=3.0)
    assert c.total == 1, "uma missão é uma missão"
    assert c.mass == 3.0, "mas pesa três na calibração"


def test_amostra_insuficiente_conta_MISSOES_nao_peso():
    """Uma confirmação humana não pode fingir ser cinco observações."""
    c = ConfidenceCalibrator(bins=2, min_samples=5)
    c.record(0.9, correct=True, weight=3.0)
    assert c.observed_rate(0.9) is None, "peso 3 nao vale por 3 missoes"


# ===  a calibracao chega ao numero exibido  ==================================

def test_sem_amostra_a_confianca_passa_intacta_e_declara_isso():
    _fresh()
    r = {"confidence": 0.8}
    Hivemind._apply_calibration(r)
    assert r["confidence"] == 0.8
    assert r["calibration"]["applied"] is False
    assert "sem amostra suficiente" in r["calibration"]["reason"]


def test_com_amostra_a_confianca_e_corrigida_pela_realidade():
    cal = _fresh()
    for _ in range(6):
        cal.record(0.9, correct=False)      # declarou 90% e errou sempre
    r = {"confidence": 0.9}
    Hivemind._apply_calibration(r)
    assert r["confidence"] == 0.0, "a realidade daquela faixa era 0% de acerto"
    assert r["calibration"]["applied"] is True
    assert r["calibration"]["raw"] == 0.9
    assert "e não os 90%" in r["calibration"]["reason"]


def test_quando_o_declarado_bate_com_o_real_a_frase_nao_fica_absurda():
    """9 acertos em 10 -> taxa real 0.9, igual à declarada."""
    cal = _fresh()
    for i in range(10):
        cal.record(0.9, correct=(i < 9))
    r = {"confidence": 0.9}
    Hivemind._apply_calibration(r)
    assert r["confidence"] == 0.9
    assert "nada a corrigir" in r["calibration"]["reason"]
    assert "não os" not in r["calibration"]["reason"]


def test_confianca_ausente_nao_produz_secao_de_calibracao():
    _fresh()
    r = {"confidence": None}
    Hivemind._apply_calibration(r)
    assert "calibration" not in r


# ===  o laco fechado  ========================================================

def test_missoes_reais_alimentam_e_depois_corrigem():
    _fresh()
    hive, _ = build_hive(db_path=":memory:")
    for i in range(6):
        asyncio.run(hive.solve(Task(goal=f"quanto é {i}+{i}")))
    t = Task(goal="quanto é 9+9")
    asyncio.run(hive.solve(t))
    assert t.result["calibration"]["applied"] is True
    assert CC.get_calibrator().total >= 6


def test_o_calibrador_aprende_com_a_confianca_CRUA_nao_com_a_corrigida():
    """Alimentar com o valor já calibrado fecharia um laço sobre si mesmo."""
    cal = _fresh()
    for _ in range(6):
        cal.record(0.9, correct=False)
    r = {"confidence": 0.9}
    Hivemind._apply_calibration(r)
    assert r["calibration"]["raw"] == 0.9 and r["confidence"] == 0.0
    # a próxima observação tem de usar 0.9 (a crua), não 0.0
    antes = cal.reliability()
    Hivemind._feed_calibrator(0.9, "computation", False)
    depois = cal.reliability()
    assert len(depois) == len(antes), "continuou no mesmo bin, o da confianca crua"


# ===  observabilidade e feedback humano  =====================================

def test_endpoint_declara_as_camadas_e_os_pesos():
    body = client.get("/calibration/signals").json()
    assert body["weights"] == {"forte": 3.0, "medio": 2.0, "fraco": 1.0}
    assert set(body["layers"]) == {"forte", "medio", "fraco"}
    assert "nunca a soma" in body["note"]


def test_o_dono_registra_o_veredito_e_ele_vale_peso_maximo():
    _fresh()
    r = client.post("/calibration/feedback",
                    json={"task_id": "t_abc", "correct": False})
    assert r.status_code == 200
    body = r.json()
    assert body["strength"] == "forte" and body["weight"] == 3.0
    assert body["human_feedback"] == {"total": 1, "approved": 0, "rejected": 1}
    assert HF.get_human_feedback().verdict("t_abc") is False


def test_missao_sem_veredito_humano_nao_inventa_um():
    _fresh()
    assert HF.get_human_feedback().verdict("nunca_avaliada") is None
    assert Hivemind._human_verdict("nunca_avaliada") is None


def test_o_dono_pode_corrigir_o_proprio_veredito():
    _fresh()
    hf = HF.get_human_feedback()
    hf.record("t1", True)
    hf.record("t1", False)
    assert hf.verdict("t1") is False and hf.total == 1
