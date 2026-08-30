"""Local Agent grant endpoint (9.21 · último fio): o fio UI -> corpo nativo.

Prova que o backend assina um grant que o corpo verificaria (verify_command),
que só capacidades executáveis pelo corpo são emitidas, que o recurso é exigido,
e que o TTL respeita o teto.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.local_agent import capability_tokens as CT

client = TestClient(app)


def test_status_reporta_capacidades_nativas():
    r = client.get("/local-agent/status")
    assert r.status_code == 200
    body = r.json()
    assert "CAN_READ_FILES" in body["native_capabilities"]
    assert "runtime" in body


def test_grant_assina_token_que_o_corpo_verifica():
    r = client.post("/local-agent/grant",
                    json={"capability": "CAN_READ_FILES", "resource": "/tmp/nota.txt"})
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    # o corpo (mesmo segredo do processo) verificaria este grant:
    ok, grant = CT.verify_command(token)
    assert ok is True
    assert grant.capability == "CAN_READ_FILES"
    assert grant.resource == "/tmp/nota.txt"


def test_grant_recusa_capacidade_sem_executor_nativo():
    # CAN_BROWSER é capacidade de servidor, não do corpo → não emite grant.
    r = client.post("/local-agent/grant",
                    json={"capability": "CAN_BROWSER", "resource": "-"})
    assert r.status_code == 400
    assert "não executável" in r.json()["detail"]


def test_grant_emite_tela_e_app():
    # 100% do corpo: tela e app agora são emitidas e verificáveis.
    for cap, res in (("CAN_SCREENSHOT", "/home/dono/Imagens/t.png"),
                     ("CAN_CONTROL_APP", "firefox")):
        r = client.post("/local-agent/grant", json={"capability": cap, "resource": res})
        assert r.status_code == 200, r.text
        ok, grant = CT.verify_command(r.json()["token"])
        assert ok and grant.capability == cap


def test_grant_exige_recurso():
    r = client.post("/local-agent/grant",
                    json={"capability": "CAN_RUN_COMMAND", "resource": "  "})
    assert r.status_code == 400


def test_grant_clampa_ttl_no_teto():
    r = client.post("/local-agent/grant",
                    json={"capability": "CAN_WRITE_FILES", "resource": "/tmp/x.txt",
                          "ttl_seconds": 99999})
    assert r.status_code == 200
    assert r.json()["expires_in"] == 300.0        # teto de 5 min


def test_grant_de_comando_verifica():
    r = client.post("/local-agent/grant",
                    json={"capability": "CAN_RUN_COMMAND", "resource": "echo oi"})
    assert r.status_code == 200
    ok, grant = CT.verify_command(r.json()["token"])
    assert ok and grant.capability == "CAN_RUN_COMMAND" and grant.resource == "echo oi"


def test_fio_completo_grant_do_endpoint_executa_sob_as_travas(tmp_path):
    # Prova o fio inteiro com um token REAL do endpoint, passando pela validacao
    # e execucao REAIS (o executor espelha as travas que o corpo nativo aplica):
    # o corpo nativo (Rust) faz o mesmo caminho, provado em native_flow.rs.
    from backend.local_agent.executor import execute_local
    from backend.permissions.device_scopes import get_device_scopes
    from backend.permissions.path_guard import get_path_guard

    alvo = tmp_path / "nota.txt"
    alvo.write_text("colonia viva", encoding="utf-8")

    # dono abre a capacidade: escopo + pasta autorizada
    get_device_scopes().grant("read_files")
    get_path_guard().allow(str(tmp_path))
    try:
        token = client.post("/local-agent/grant",
                            json={"capability": "CAN_READ_FILES",
                                  "resource": str(alvo)}).json()["token"]
        res = execute_local(token)          # verifica + autoriza + le de verdade
        assert res["ok"] is True and res["allowed"] is True
        assert res["result"]["text"].startswith("colonia viva")
    finally:
        get_device_scopes().revoke("read_files")
        get_path_guard().disallow(str(tmp_path))
