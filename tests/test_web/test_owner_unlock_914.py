"""Prova do desbloqueio do dono (9.14) — o único serviço público, funcional e seguro.

Num deploy público (ANTS_PUBLIC=1 + ANTS_API_TOKEN), as rotas sensíveis exigem o
token do dono. O front (api_bridge) passa a mandar a chave do dono como
X-Ants-Token, então o dono DESBLOQUEIA a Evolução/Ferramentas sem abrir a porta
para anônimos. As rotas de missão seguem abertas (a PWA funciona para visitantes).

Prova:
- anônimo → /evolution 401 (barrado);
- dono com X-Ants-Token → /evolution 200 (desbloqueado);
- /mission (histórico) segue aberto (não-401) — visitante usa a colônia.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)
TOKEN = "segredo-do-jonas-914"


def test_publico_evolucao_barra_anonimo(monkeypatch):
    monkeypatch.setenv("ANTS_PUBLIC", "1")
    monkeypatch.setenv("ANTS_API_TOKEN", TOKEN)
    assert client.get("/evolution").status_code == 401
    assert client.post("/evolution/mine").status_code == 401


def test_publico_evolucao_desbloqueia_com_x_ants_token(monkeypatch):
    monkeypatch.setenv("ANTS_PUBLIC", "1")
    monkeypatch.setenv("ANTS_API_TOKEN", TOKEN)
    h = {"X-Ants-Token": TOKEN}
    assert client.get("/evolution", headers=h).status_code == 200
    assert client.post("/evolution/mine", headers=h).status_code == 200


def test_publico_missao_segue_aberta_para_visitante(monkeypatch):
    # A PWA (perguntas/missão/histórico) funciona para o visitante sem token.
    monkeypatch.setenv("ANTS_PUBLIC", "1")
    monkeypatch.setenv("ANTS_API_TOKEN", TOKEN)
    assert client.get("/mission").status_code == 200


def test_ferramentas_gated_desbloqueiam_com_token(monkeypatch):
    monkeypatch.setenv("ANTS_PUBLIC", "1")
    monkeypatch.setenv("ANTS_API_TOKEN", TOKEN)
    r0 = client.post("/tools/run",
                     json={"name": "compute", "args": {"expression": "2+2"}})
    assert r0.status_code == 401                       # anônimo barrado
    r1 = client.post("/tools/run",
                     json={"name": "compute", "args": {"expression": "2+2"}},
                     headers={"X-Ants-Token": TOKEN})
    assert r1.status_code == 200 and str(r1.json()["result"]["answer"]) == "4"
