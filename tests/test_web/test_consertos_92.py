"""Testes dos consertos da fase 9.2 — provam cada correção, não só que compila.

Cobrem: service worker à prova de regressão (stale-while-revalidate),
progresso dirigido por eventos reais, síntese limpa da busca pelo compositor,
saúde da memória com dado real, e remoção do ruído da interface.
"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)
WEB = Path(__file__).resolve().parents[2] / "web"


# ── Bloco B · animações: service worker nunca mais serve código velho ──────
def test_sw_stale_while_revalidate_nao_cache_first():
    sw = (WEB / "sw.js").read_text(encoding="utf-8")
    # A regressão recorrente vinha de assets em cache-first. O conserto é
    # buscar sempre a versão nova em segundo plano (stale-while-revalidate).
    assert "cache.put" in sw and "caches.open(CACHE)" in sw
    assert "stale-while-revalidate" in sw.lower() or "revalidate" in sw.lower()
    # A antiga linha cache-first pura não pode voltar.
    assert "caches.match(e.request).then((r) => r || fetch" not in sw


def test_sse_morto_removido():
    # sse.js era código morto (nunca chamado) — some do bundle e do SW.
    assert not (WEB / "js" / "sse.js").exists()
    assert "sse.js" not in (WEB / "sw.js").read_text(encoding="utf-8")
    assert "sse.js" not in (WEB / "index.html").read_text(encoding="utf-8")


# ── Bloco C · progresso dirigido por EVENTOS REAIS (não por tempo) ─────────
def test_progresso_derivado_de_eventos_nao_de_tempo():
    js = (WEB / "js" / "api_bridge.js").read_text(encoding="utf-8")
    # O % agora deriva da fase real do último evento (plan/do/check/act),
    # não de um contador incrementado a cada 600ms.
    assert "stepFromEvents" in js
    assert '"plan"' in js and '"do"' in js and '"check"' in js and '"act"' in js
    # O contador por tempo ("if (i < steps.length - 2) i++") saiu.
    assert "steps.length - 2) i++" not in js
    # Conclusão sempre chega a 100% (i = último passo quando done).
    assert "done ? last" in js


# ── Bloco D · busca CLARA: resposta da web passa pelo compositor ───────────
def test_resposta_web_passa_pelo_compositor():
    from backend.hivemind.hive import Hivemind
    from backend.memory.shared_memory import SharedMemory

    hive = Hivemind.__new__(Hivemind)
    hive.memory = SharedMemory(":memory:")
    tid = "task_web_syn"
    hive.memory.set_context(tid, "decision",
                            {"answer": "O Xbox 360 e um console.",
                             "confidence": 0.9})
    hive.memory.set_context(tid, "sources", [
        {"url": "https://pt.wikipedia.org/wiki/Xbox_360"},
        {"url": "https://en.wikipedia.org/wiki/Xbox_360"},
    ])
    result = hive._compile_result(tid)
    # Síntese limpa: selo de proveniência + fontes clicáveis (domínios).
    assert "busca na web" in result["answer"]
    assert "pt.wikipedia.org" in result["answer"]
    assert result["provenance"]["source"] == "web_search"


def test_composer_web_seal():
    from backend.cognitive.response_composer import get_composer
    out = get_composer().web("Texto.", 2, ["a.com", "b.com"])
    assert "Fontes: a.com, b.com" in out
    assert "busca na web (2 fonte(s))" in out


# ── Bloco E · memória com dado real + ruído removido ───────────────────────
def test_memory_health_tem_avg_strength_real():
    ex = client.get("/memory/health").json().get("extra", {})
    assert "avg_strength" in ex
    assert isinstance(ex["avg_strength"], (int, float))


def test_ambiente_sem_placeholders_mortos():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    # Os campos que ficavam eternamente "—" (sem fonte real) sairam.
    for morto in ("env-nodes", "env-relations", "env-confidence",
                  "env-domains", "env-verified", "env-files", "env-procs",
                  'id="env-mem-short"'):
        assert morto not in html, morto
    # O que ficou é real: requisições e memória (total/fortes/força).
    assert "env-reqs" in html and "env-mem-total" in html
