"""Prova do painel "Mente da Colônia" (9.9 · FASE F · interface reativa).

Diagnóstico: toda a inteligência das FASES B–E (rotas, ferramentas, decisão
coletiva, atenção, autonomia) existia no backend mas era INVISÍVEL na interface —
o usuário não via a mente que a colônia ganhou.
Correção: web/js/mind_panel.js renderiza, ao vivo e honestamente, o bloco
intelligence do /health (fonte única: evento ants:health). Aditivo — não toca nos
4 JS legados (MD5 imutável).
Prova: o JS existe e lê a fonte certa; o index.html o inclui e tem o container; o
/health entrega os campos que o painel consome; os 4 JS legados seguem intactos.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.main import app

WEB = Path(__file__).resolve().parents[2] / "web"
client = TestClient(app)

# MD5 dos 4 JS legados (imutáveis) — o painel NÃO pode alterá-los.
_LEGACY_MD5 = {
    "chat.js": "e1cc6df5be37d6e0502b1063767601bd",
    "bots.js": "ed95b37ebbf0b926daa685dfe09419c1",
    "memory.js": "de5d8499d12efd869baa138497996e10",
    "factory.js": "18b0d5a834fda16f613633a250db053d",
}


def test_js_existe_e_le_a_fonte_unica():
    js = (WEB / "js" / "mind_panel.js").read_text(encoding="utf-8")
    assert "ants:health" in js               # fonte única (T6), sem fetch próprio
    assert "intelligence" in js and "cartographer" in js
    assert "autonomous_loop" in js and "mind-tool" in js
    # honestidade: mostra risco e disponibilidade das ferramentas
    assert "available" in js and "risk" in js


def test_index_inclui_o_painel_e_o_container():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "/js/mind_panel.js" in html
    assert 'id="mind-panel"' in html


def test_health_entrega_o_que_o_painel_consome():
    intel = client.get("/health").json()["intelligence"]
    assert "cartographer" in intel and "tools" in intel
    assert intel["autonomous_loop"] is True
    assert intel["collective_decision"] and intel["adaptive_labor"]
    for t in intel["tools"]:
        assert "name" in t and "risk" in t and "available" in t


def test_legado_intacto():
    for name, md5 in _LEGACY_MD5.items():
        data = (WEB / "js" / name).read_bytes()
        assert hashlib.md5(data).hexdigest() == md5, f"{name} foi alterado!"
