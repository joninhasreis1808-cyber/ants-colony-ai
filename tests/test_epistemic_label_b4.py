"""B4 · Rótulo epistêmico ampliado (roteiro de maestria).

A colônia já dizia muita coisa sobre o próprio conhecimento — proveniência,
degrau de fallback, verificação cruzada, calibração, lastro, confiança — mas
espalhada em SEIS campos. Para saber que tipo de conhecimento uma resposta era,
alguém tinha de ler os seis e cruzá-los na cabeça.

Aqui provamos que o rótulo reúne os sinais que já existem (sem inventar nenhum),
que a manchete `contestado` — que não existia — aparece quando deve, e que todo
eixo sem sinal diz "não medido" em vez de um valor plausível.
"""
from __future__ import annotations

import asyncio

from backend.cognition.epistemic_label import HEADLINES, build
from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.memory.long_term_memory import LongTermMemory
from backend.memory.schemas import MemoryInput


def _res(**kw):
    base = {"provenance": {"source": "computation"}, "confidence": 0.9}
    base.update(kw)
    return base


def _ltm(*conteudos):
    ltm = LongTermMemory()
    for c in conteudos:
        ltm.remember(MemoryInput(content=c, source="bot", tags=["task_outcome"],
                                 related_tasks=["t"], emotional_weight=0.4))
    return ltm


# ===  a manchete  ============================================================

def test_evidencia_dura_confirmada_e_verificado():
    r = _res(cross_check={"verdict": "confirmado", "agreeing": ["own_memory"]})
    assert build(r).headline == "verificado"


def test_a_manchete_que_faltava_contestado():
    """Antes, resposta com rotas se contradizendo tinha a mesma cara de uma
    resposta tranquila."""
    r = _res(cross_check={"verdict": "divergente",
                          "reason": "citam grandezas diferentes"})
    rot = build(r)
    assert rot.headline == "contestado"
    assert "em vez de resolvida em silêncio" in rot.explanation


def test_contestado_ganha_de_verificado():
    """Divergência não é detalhe de rodapé."""
    r = _res(cross_check={"verdict": "divergente", "reason": "x"},
             grounding={"sufficient": True})
    assert build(r).headline == "contestado"


def test_sem_base_ganha_de_tudo():
    r = _res(provenance={"source": "none"},
             cross_check={"verdict": "divergente", "reason": "x"})
    assert build(r).headline == "sem_base"
    r2 = _res(fallback={"escalate_human": True})
    assert build(r2).headline == "sem_base"


def test_ancorado_sem_confirmacao_e_fundamentado():
    assert build(_res()).headline == "fundamentado"
    r = _res(provenance={"source": "own_memory"}, grounding={"sufficient": True})
    assert build(r).headline == "fundamentado"


def test_registro_sem_lastro_novo_e_recordado():
    r = _res(provenance={"source": "seed_knowledge"})
    assert build(r).headline == "recordado"


def test_raciocinio_sem_fatos_e_inferido():
    r = _res(provenance={"source": "reasoning"})
    rot = build(r)
    assert rot.headline == "inferido"
    assert "mais frágil" in rot.explanation


def test_toda_manchete_produzida_esta_no_vocabulario_declarado():
    fontes = ["computation", "web_search", "own_memory", "seed_knowledge",
              "reasoning", "none"]
    for f in fontes:
        for cc in (None, {"verdict": "confirmado", "agreeing": ["x"]},
                   {"verdict": "divergente", "reason": "r"}):
            assert build(_res(provenance={"source": f},
                              cross_check=cc)).headline in HEADLINES


# ===  os eixos, e o "nao medido"  ============================================

def test_sem_verificacao_o_eixo_declara_a_ausencia_como_limite():
    rot = build(_res())
    assert "não conferido" in rot.verification
    assert any("nenhuma rota independente" in l for l in rot.limits)


def test_sem_calibracao_o_eixo_diz_nao_medido():
    assert "não medido" in build(_res()).calibration


def test_calibracao_aplicada_mostra_os_dois_numeros():
    r = _res(calibration={"applied": True, "raw": 0.9, "calibrated": 0.4})
    assert "90% declarado" in build(r).calibration
    assert "40% observado" in build(r).calibration


def test_calibracao_que_ja_batia_nao_finge_correcao():
    r = _res(calibration={"applied": True, "raw": 0.9, "calibrated": 0.9})
    assert "já batia com a realidade" in build(r).calibration


def test_recencia_so_vale_para_resposta_vinda_de_registro():
    assert "não se aplica" in build(_res()).recency
    r = _res(provenance={"source": "own_memory"},
             grounding={"sufficient": True, "age_days": 0.2})
    assert build(r).recency == "registro de hoje"


def test_registro_antigo_e_declarado_como_antigo():
    r = _res(provenance={"source": "own_memory"},
             grounding={"sufficient": True, "age_days": 180.0})
    assert "180 dias atrás" in build(r).recency


def test_registro_sem_data_diz_nao_medido_e_nao_finge_ser_recente():
    r = _res(provenance={"source": "own_memory"},
             grounding={"sufficient": True, "age_days": None})
    assert "não medido" in build(r).recency


# ===  os limites  ============================================================

def test_o_que_o_detector_nao_ve_entra_como_limite():
    r = _res(cross_check={"verdict": "confirmado", "agreeing": ["x"],
                          "undetectable": "contradição semântica não é detectada"})
    assert any("semântica" in l for l in build(r).limits)


def test_web_bloqueada_entra_como_limite():
    r = _res(provenance={"source": "own_memory", "web": "bloqueado (403)"})
    assert any("busca externa não estava disponível" in l for l in build(r).limits)


def test_lacunas_da_proveniencia_viram_limites():
    r = _res(provenance={"source": "reasoning", "gaps": ["faltou fonte primária"]})
    assert "faltou fonte primária" in build(r).limits


# ===  o laco fechado  ========================================================

def test_missao_real_produz_o_rotulo_completo():
    hive, _ = build_hive(db_path=":memory:")
    t = Task(goal="quanto é 7*6")
    asyncio.run(hive.solve(t))
    rot = t.result["epistemic"]
    assert rot["headline"] in HEADLINES
    assert rot["origin"] == "computation"
    assert rot["explanation"]
    for eixo in ("verification", "calibration", "recency"):
        assert rot[eixo], f"o eixo {eixo} nunca pode vir vazio"


def test_missao_com_memoria_que_discorda_sai_rotulada_como_contestada():
    hive, _ = build_hive(
        db_path=":memory:", ltm=_ltm("Tarefa 'soma': quanto e 2+2, a resposta e 5"))
    t = Task(goal="quanto é 2+2")
    asyncio.run(hive.solve(t))
    rot = t.result["epistemic"]
    assert rot["headline"] == "contestado"
    assert "4" in t.result["answer"], "e a resposta certa continua sendo dada"
    assert rot["limits"], "a contradição tem que aparecer nos limites"


def test_o_rotulo_nao_inventa_sinal_que_o_resultado_nao_tem():
    """Um resultado pelado produz rótulo pelado, não rótulo bonito."""
    rot = build({})
    assert rot.headline == "sem_base"
    assert rot.confidence is None
    assert "não medido" in rot.calibration


def test_o_rotulo_nunca_derruba_a_missao():
    hive, _ = build_hive(db_path=":memory:")
    t = Task(goal="quanto é 5+5")
    asyncio.run(hive.solve(t))
    assert t.result["answer"]
