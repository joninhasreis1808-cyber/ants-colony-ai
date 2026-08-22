"""Prova do Passo 3 (9.12) — console de Missão Autônoma + Evolução na PWA.

Diagnóstico: /mission/auto e /evolution existiam, mas não tinham rosto na
interface — o dono não podia lançar uma missão autônoma nem revisar/aprovar
propostas de evolução visualmente.
Correção: web/js/mission_console.js (aditivo) desenha os dois consoles usando
AntAPI. NÃO toca nos 4 JS legados.
Prova: o JS existe e fala com as rotas certas; index.html inclui o script e o
container; as rotas respondem; os 4 JS legados seguem intactos (MD5).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.main import app

WEB = Path(__file__).resolve().parents[2] / "web"
client = TestClient(app)

_LEGACY_MD5 = {
    "chat.js": "e1cc6df5be37d6e0502b1063767601bd",
    "bots.js": "ed95b37ebbf0b926daa685dfe09419c1",
    "memory.js": "de5d8499d12efd869baa138497996e10",
    "factory.js": "18b0d5a834fda16f613633a250db053d",
}


def test_js_fala_com_as_rotas_certas():
    js = (WEB / "js" / "mission_console.js").read_text(encoding="utf-8")
    assert "/mission/auto" in js and "/evolution" in js
    assert "/evolution/mine" in js
    assert "AntAPI" in js                       # usa a ponte, sem fetch próprio
    assert "approve" in js and "reject" in js and "apply" in js


def test_index_inclui_o_console_e_o_container():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "/js/mission_console.js" in html
    assert 'id="mission-console"' in html


def test_rotas_do_console_respondem():
    # /mission/auto determinístico (offline) e /evolution listável
    r = client.post("/mission/auto", json={"goal": "quanto é 6 * 7", "online": False})
    assert r.status_code == 200 and "cycles" in r.json()
    assert client.get("/evolution").status_code == 200


def test_legado_intacto():
    for name, md5 in _LEGACY_MD5.items():
        data = (WEB / "js" / name).read_bytes()
        assert hashlib.md5(data).hexdigest() == md5, f"{name} foi alterado!"
