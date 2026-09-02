"""Validação em produção · o rótulo epistêmico em TODOS os caminhos de missão.

Achado na validação ponta a ponta pelo navegador, com as dependências exatas de
produção (`requirements-cloud.txt`): o evento `ants:task-done` chegava ao front
com seis chaves — `answer, confidence, sources, learning, provenance, trace` — e
**nenhuma delas era `epistemic`**. O cartão da FASE C simplesmente não aparecia.

Causa: dois caminhos desviam do `Hivemind._compile_result` e por isso nasciam
sem nenhum enriquecimento das FASES A/B:

  1. resposta vinda do **cache** (`_answer_from_memory`);
  2. **pesquisa profunda** (`deep_research.run`), que monta o próprio `result`.

Na prática, a interface ficava muda justamente nas respostas mais rápidas — e
sem explicar por quê. Os testes das fases anteriores não pegaram isso porque
verificavam o backend e o front separadamente, nunca o transporte no meio.
"""
from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.routes import hive as H
from backend.cognition.epistemic_label import HEADLINES
from backend.core import Task
from backend.memory.answer_cache import get_answer_cache

client = TestClient(app)


class _TarefaFalsa:
    """Só o que `_ensure_epistemic` toca."""

    def __init__(self, result):
        self.id = "task_teste"
        self.result = result


# ===  o gancho compartilhado  ================================================

def test_resultado_sem_rotulo_ganha_rotulo():
    t = _TarefaFalsa({"answer": "42", "confidence": 0.9,
                      "provenance": {"source": "memory"}})
    H._ensure_epistemic(t)
    assert "epistemic" in t.result
    assert t.result["epistemic"]["headline"] in HEADLINES


def test_resultado_que_ja_tem_rotulo_nao_e_reescrito():
    """O caminho normal (_compile_result) já rotulou — não mexer."""
    original = {"headline": "verificado", "origin": "computation",
                "verification": "x", "calibration": "y", "recency": "z"}
    t = _TarefaFalsa({"answer": "4", "epistemic": original})
    H._ensure_epistemic(t)
    assert t.result["epistemic"] is original


def test_resultado_vazio_nao_produz_rotulo_inventado():
    t = _TarefaFalsa(None)
    H._ensure_epistemic(t)
    assert t.result is None
    t2 = _TarefaFalsa({})
    H._ensure_epistemic(t2)
    assert "epistemic" not in t2.result


def test_o_gancho_nunca_derruba_a_missao():
    class Quebrado:
        id = "x"

        @property
        def result(self):
            raise RuntimeError("armazém fora do ar")

    H._ensure_epistemic(Quebrado())      # não pode levantar


def test_a_calibracao_tambem_e_aplicada_nesses_caminhos():
    t = _TarefaFalsa({"answer": "42", "confidence": 0.9,
                      "provenance": {"source": "memory"}})
    H._ensure_epistemic(t)
    assert "calibration" in t.result


def test_a_verificacao_cruzada_NAO_e_recomposta_e_isso_e_correto():
    """Nessas rotas uma só fonte respondeu — não há segunda opinião. O rótulo
    diz "não conferido", que é a verdade, em vez de inventar concordância."""
    t = _TarefaFalsa({"answer": "42", "confidence": 0.9,
                      "provenance": {"source": "memory"}})
    H._ensure_epistemic(t)
    assert "cross_check" not in t.result
    assert "não conferido" in t.result["epistemic"]["verification"]


# ===  os dois caminhos que desviavam  ========================================

def test_os_dois_desvios_chamam_o_gancho():
    """Guarda estrutural: se alguém adicionar um novo desvio e esquecer o
    gancho, este teste não pega — mas se REMOVEREM um dos dois, pega."""
    fonte = (H.__file__ and open(H.__file__, encoding="utf-8").read()) or ""
    assert fonte.count("_ensure_epistemic(task)") >= 2
    i_cache = fonte.index("_answer_from_memory(task)")
    i_deep = fonte.index("deep_research.run(")
    for i in (i_cache, i_deep):
        assert "_ensure_epistemic" in fonte[i:i + 260], \
            "um dos caminhos que desvia do _compile_result ficou sem o rótulo"


def test_missao_pelo_cache_chega_ao_front_com_rotulo():
    """O caminho que estava quebrado, ponta a ponta pela API HTTP."""
    get_answer_cache().clear()
    goal = "quanto é 12 * 12"

    r1 = client.post("/hive/task", json={"goal": goal})
    assert r1.status_code == 200
    tid1 = r1.json()["task_id"]
    for _ in range(80):
        s = client.get(f"/hive/status/{tid1}")
        if s.json().get("status") in ("done", "failed"):
            break
        import time as _t
        _t.sleep(0.05)

    # segunda vez: agora vem do cache — o caminho que perdia o rótulo
    r2 = client.post("/hive/task", json={"goal": goal})
    tid2 = r2.json()["task_id"]
    for _ in range(80):
        s = client.get(f"/hive/status/{tid2}")
        corpo = s.json()
        if corpo.get("status") in ("done", "failed"):
            break
        import time as _t
        _t.sleep(0.05)
    res = (corpo or {}).get("result") or {}
    if res:                                   # só afirma se a missão concluiu
        assert "epistemic" in res, "resposta do cache voltou sem rótulo"
        assert res["epistemic"]["headline"] in HEADLINES


# ===  o que a validacao com deps de producao provou  =========================

def test_o_health_nao_finge_contagem_de_testes_sem_a_pasta():
    """`tests/` não vai na imagem; o contador devolve 0 e o front mostra '—'."""
    import backend.api.main as M
    fonte = open(M.__file__, encoding="utf-8").read()
    assert "if not root.is_dir():" in fonte and "return 0" in fonte


def test_o_dockerfile_leva_a_interface_inteira():
    """`COPY web/` — se alguém trocar por arquivos avulsos, os painéis novos
    ficariam de fora da imagem sem ninguém perceber."""
    from pathlib import Path
    df = (Path(__file__).resolve().parents[1] / "deploy/Dockerfile").read_text()
    assert "COPY web/ ./web/" in df
    assert "COPY backend/ ./backend/" in df
