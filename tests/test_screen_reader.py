"""Testes das ferramentas de leitura/visão de tela (7.2 · adição do dono).

Ler, ver, compreender e planejar ação sobre o que está na tela — real e
offline pelo DOM; OCR quando o Tesseract existe; execução declarada.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.perception.screen_reader import ScreenReader

client = TestClient(app)

_HTML = (
    "<html><head><title>ignorar</title></head><body>"
    "<h1>Painel da Colônia</h1><p>Bem-vindo.</p>"
    "<button id='send'>Enviar objetivo</button>"
    "<input name='q' placeholder='Descreva um objetivo' type='text'>"
    "<a href='/ajuda'>Ajuda</a></body></html>"
)


def test_read_dom_localiza_elementos_interativos():
    r = ScreenReader().read_dom(_HTML)
    tags = [(e.tag, e.action) for e in r.elements]
    assert ("button", "click") in tags
    assert ("input", "type") in tags
    assert ("a", "click") in tags
    assert r.headings == ["Painel da Colônia"]
    assert "ignorar" not in r.text          # <title> não polui o texto
    assert "/ajuda" in r.links


def test_plan_actions_prioriza_pelo_objetivo():
    sr = ScreenReader()
    r = sr.read_dom(_HTML)
    plan = sr.plan_actions(r, "enviar um objetivo para a colônia")
    assert plan[0]["target"] == "Enviar objetivo"
    assert plan[0]["action"] == "click"
    # honestidade: execução não roda aqui, é capacidade declarada
    assert plan[0]["executable_here"] is False
    assert plan[0]["capability"] == "declared"


def test_endpoint_screen_dom():
    r = client.post("/perceive/screen/dom",
                    json={"html": _HTML, "goal": "enviar objetivo"})
    assert r.status_code == 200
    d = r.json()
    assert d["element_count"] >= 3
    assert d["action_plan"][0]["action"] == "click"
    assert "comprehension" in d


def test_endpoint_capabilities_honesto():
    r = client.get("/organism/capabilities")
    assert r.status_code == 200
    d = r.json()
    names = [c["name"] for c in d["offline"]]
    assert any("cálculo" in n for n in names)
    # dados atuais declarados como dependentes de web e indisponíveis
    assert d["needs_web"][0]["available"] is False
    # ação no dispositivo é capacidade declarada do app nativo
    assert d["declared_native"][0]["where"] == "native"
