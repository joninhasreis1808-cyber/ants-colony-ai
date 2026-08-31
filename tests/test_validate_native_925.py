"""Kit de validação do corpo local (9.25 · etapa 4).

Espelha, via TestClient, a sequência que o `scripts/validate_native.sh` faz contra
o backend rodando — prova a camada HTTP de ponta a ponta — e trava o script à API
real (se um endpoint mudar de nome, o teste quebra junto).
"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)
SCRIPT = (Path(__file__).resolve().parents[1] / "scripts" / "validate_native.sh").read_text(encoding="utf-8")


def test_sequencia_de_validacao_ponta_a_ponta():
    assert client.get("/health").json()["status"] == "healthy"
    assert len(client.get("/local-agent/status").json()["native_capabilities"]) >= 6
    reg = client.post("/device-identity/register",
                      json={"device_id": "validador", "name": "kit"})
    assert reg.status_code == 200 and reg.json()["secret"]
    g = client.post("/local-agent/grant",
                    json={"capability": "CAN_READ_FILES", "resource": "/tmp/x",
                          "device_id": "validador"})
    assert g.status_code == 200 and g.json()["token"]
    assert "ece" in client.get("/calibration").json()
    assert client.post("/device-identity/revoke",
                       json={"device_id": "validador"}).json()["revoked"] is True


def test_script_referencia_os_endpoints_reais():
    for ep in ("/health", "/local-agent/status", "/device-identity/register",
               "/local-agent/grant", "/calibration"):
        assert ep in SCRIPT, f"o validador não referencia {ep}"


def test_script_tem_checklist_das_6_capacidades():
    for acao in ("Ler arquivo", "Escrever", "Rodar comando", "Capturar tela",
                 "Abrir app", "Controle"):
        assert acao in SCRIPT
