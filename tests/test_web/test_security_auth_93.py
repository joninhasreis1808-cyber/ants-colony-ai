"""Prova das correções de segurança 9.3 (C-1 guarda de token · C-2 postura).

Reproduz, via TestClient, os mesmos ataques do kit do dono: o anônimo que se
concede nível 5, grava arquivo e concede escopo de device. Verifica que:
- LOCAL (padrão, sem ANTS_PUBLIC): tudo segue liberado — nada quebra.
- PÚBLICO (ANTS_PUBLIC=1): as rotas sensíveis exigem o token do dono (401).
- Com o token correto (Bearer ou X-Ants-Token): o dono passa (não-401).
- O token NUNCA aparece no /health, que só declara a postura.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)

SENSIVEIS = [
    ("/permissions/grant", {"user_id": "invasor", "level": 5}),
    ("/action/file", {"user_id": "invasor", "op": "create",
                      "path": "/tmp/via_teste.txt", "content": "x"}),
    ("/device/scopes/grant", {"scope": "write_files"}),
]


def test_local_padrao_segue_liberado():
    # Sem ANTS_PUBLIC, o loopback é de confiança — o app nativo e os testes
    # não mudam. As rotas sensíveis respondem normalmente (não 401).
    for rota, corpo in SENSIVEIS:
        r = client.post(rota, json=corpo)
        assert r.status_code != 401, f"{rota} deveria estar liberada em modo local"


def test_publico_sem_token_bloqueia_o_invasor(monkeypatch):
    # Exatamente o ataque do kit: exposto publicamente, o anônimo é barrado.
    monkeypatch.setenv("ANTS_PUBLIC", "1")
    monkeypatch.setenv("ANTS_API_TOKEN", "segredo-do-jonas")
    for rota, corpo in SENSIVEIS:
        r = client.post(rota, json=corpo)
        assert r.status_code == 401, f"{rota} deveria exigir token em modo público"
        assert "não autenticado" in r.json()["detail"]


def test_publico_com_token_bearer_o_dono_passa(monkeypatch):
    monkeypatch.setenv("ANTS_PUBLIC", "1")
    monkeypatch.setenv("ANTS_API_TOKEN", "segredo-do-jonas")
    h = {"Authorization": "Bearer segredo-do-jonas"}
    for rota, corpo in SENSIVEIS:
        r = client.post(rota, json=corpo, headers=h)
        assert r.status_code != 401, f"{rota}: o dono autenticado não pode levar 401"


def test_publico_com_header_x_ants_token(monkeypatch):
    monkeypatch.setenv("ANTS_PUBLIC", "1")
    monkeypatch.setenv("ANTS_API_TOKEN", "segredo-do-jonas")
    r = client.post("/permissions/grant", json={"user_id": "jonas", "level": 5},
                    headers={"X-Ants-Token": "segredo-do-jonas"})
    assert r.status_code == 200


def test_publico_com_token_errado_barra(monkeypatch):
    monkeypatch.setenv("ANTS_PUBLIC", "1")
    monkeypatch.setenv("ANTS_API_TOKEN", "segredo-do-jonas")
    r = client.post("/permissions/grant", json={"user_id": "x", "level": 5},
                    headers={"Authorization": "Bearer errado"})
    assert r.status_code == 401


def test_publico_sem_token_configurado_falha_fechado(monkeypatch):
    # Exposto sem token configurado: fail-closed (não há como autenticar ninguém).
    monkeypatch.setenv("ANTS_PUBLIC", "1")
    monkeypatch.delenv("ANTS_API_TOKEN", raising=False)
    r = client.post("/permissions/grant", json={"user_id": "x", "level": 5})
    assert r.status_code == 401


def test_2a_guarda_path_guard_barra_ate_o_dono(monkeypatch, tmp_path):
    # Defesa em profundidade: mesmo autenticado, o dono não escreve na árvore
    # de código (fora das pastas autorizadas). Depois de autorizar a pasta,
    # a escrita passa. Exatamente a contraprova do kit.
    monkeypatch.setenv("ANTS_PUBLIC", "1")
    monkeypatch.setenv("ANTS_API_TOKEN", "segredo-do-jonas")
    h = {"Authorization": "Bearer segredo-do-jonas"}
    alvo_proibido = "backend/api/PWNED.py"
    r = client.post("/action/file", headers=h, json={
        "user_id": "jonas", "op": "create", "path": alvo_proibido, "content": "x"})
    assert r.status_code == 403
    assert "fora das pastas autorizadas" in r.json()["detail"]

    # Autoriza uma pasta segura (com o token) e então a escrita é aceita.
    pasta = str(tmp_path)
    assert client.post("/device/paths/allow", headers=h,
                       json={"path": pasta}).json()["allowed"] is True
    alvo_ok = str(tmp_path / "nota.txt")
    r2 = client.post("/action/file", headers=h, json={
        "user_id": "jonas", "op": "create", "path": alvo_ok, "content": "oi"})
    assert r2.status_code == 200 and r2.json()["ok"] is True


def test_health_declara_postura_sem_vazar_token(monkeypatch):
    monkeypatch.setenv("ANTS_PUBLIC", "1")
    monkeypatch.setenv("ANTS_API_TOKEN", "segredo-do-jonas")
    body = client.get("/health").json()
    auth = body["auth"]
    assert auth == {"mode": "token", "token_configurado": True, "publico": True}
    # O segredo não pode aparecer em lugar nenhum da resposta.
    assert "segredo-do-jonas" not in client.get("/health").text


def test_health_postura_aberta_por_padrao(monkeypatch):
    monkeypatch.delenv("ANTS_PUBLIC", raising=False)
    monkeypatch.delenv("ANTS_API_TOKEN", raising=False)
    auth = client.get("/health").json()["auth"]
    assert auth == {"mode": "open", "token_configurado": False, "publico": False}
