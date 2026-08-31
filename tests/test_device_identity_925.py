"""Identidade de dispositivo + ponte remota (9.25 · etapa 3).

Prova que cada dispositivo tem um segredo DERIVADO (por dispositivo), que um
grant assinado para A é recusado por B, que o pareamento entrega o segredo uma
vez e o registro nunca guarda segredo, e que /local-agent/grant liga o grant a
um dispositivo pareado.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

import backend.security.secret_vault as SV
from backend.api.main import app
from backend.local_agent import capability_tokens as CT
from backend.local_agent.device_identity import DeviceRegistry, device_secret

client = TestClient(app)


def _fresh_vault(monkeypatch):
    monkeypatch.setenv("ANTS_BRIDGE_SECRET", "mestre-de-teste")
    SV._INSTANCE = None


def test_segredo_e_por_dispositivo(monkeypatch):
    _fresh_vault(monkeypatch)
    a = device_secret("notebook")
    b = device_secret("celular")
    assert a and b and a != b               # derivados distintos
    assert device_secret("notebook") == a   # determinístico


def test_grant_do_dispositivo_A_recusado_por_B(monkeypatch):
    _fresh_vault(monkeypatch)
    token = CT.sign_for_device("CAN_READ_FILES", "/tmp/x.txt", "A", ttl_seconds=60)
    ok_a, grant = CT.verify_for_device(token, "A")
    ok_b, _ = CT.verify_for_device(token, "B")
    assert ok_a and grant.capability == "CAN_READ_FILES"
    assert ok_b is False                    # B tem outro segredo → recusa


def test_registro_entrega_segredo_uma_vez_e_nao_guarda(monkeypatch):
    _fresh_vault(monkeypatch)
    reg = DeviceRegistry()
    out = reg.register("notebook-do-dono", "Notebook")
    assert out["secret"] and out["device_id"] == "notebook-do-dono"
    # o registro guarda metadados, jamais o segredo
    info = reg.info("notebook-do-dono")
    assert "secret" not in info
    assert all("secret" not in d for d in reg.list())


def test_revogar_desparea(monkeypatch):
    _fresh_vault(monkeypatch)
    reg = DeviceRegistry()
    reg.register("d1")
    assert reg.is_registered("d1")
    assert reg.revoke("d1") is True
    assert not reg.is_registered("d1")


def test_endpoint_registra_e_grant_liga_ao_dispositivo(monkeypatch):
    _fresh_vault(monkeypatch)
    # pareia
    r = client.post("/device-identity/register",
                    json={"device_id": "meu-note", "name": "Note"})
    assert r.status_code == 200 and r.json()["secret"]
    # grant ligado ao dispositivo
    g = client.post("/local-agent/grant",
                    json={"capability": "CAN_READ_FILES", "resource": "/tmp/x",
                          "device_id": "meu-note"})
    assert g.status_code == 200 and g.json()["device_id"] == "meu-note"
    # o corpo do dispositivo verifica com o segredo derivado
    ok, _ = CT.verify_for_device(g.json()["token"], "meu-note")
    assert ok is True


def test_grant_para_dispositivo_nao_pareado_recusado(monkeypatch):
    _fresh_vault(monkeypatch)
    g = client.post("/local-agent/grant",
                    json={"capability": "CAN_READ_FILES", "resource": "/tmp/x",
                          "device_id": "fantasma"})
    assert g.status_code == 400
    assert "não pareado" in g.json()["detail"]


def test_lista_de_dispositivos_nao_vaza_segredo(monkeypatch):
    _fresh_vault(monkeypatch)
    client.post("/device-identity/register", json={"device_id": "d-lista"})
    r = client.get("/device-identity")
    assert r.status_code == 200
    assert "secret" not in str(r.json())
