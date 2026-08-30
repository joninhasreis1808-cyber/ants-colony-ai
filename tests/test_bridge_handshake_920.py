"""Handshake do segredo da ponte (9.20 · Tauri-prep).

Prova o lado Python do aperto de mão que o app Tauri faz: o `ANTS_BRIDGE_SECRET`
que o processo nativo entrega ao sidecar (a) semeia o Secret Vault como mestre
'bridge' e (b) é EXATAMENTE o segredo com que o capability_tokens assina/verifica
— então o grant assinado pelo cérebro é aceito pelo corpo. (O lado Rust
`ensure_bridge_secret` foi type-checado e executado em isolamento.)
"""
from __future__ import annotations

import backend.security.secret_vault as sv
from backend.api.sidecar import seed_secret_vault
from backend.local_agent import capability_tokens as CT


def test_sidecar_semeia_o_cofre_com_o_segredo_da_ponte(monkeypatch):
    monkeypatch.setenv("ANTS_BRIDGE_SECRET", "segredo-do-tauri")
    sv._INSTANCE = None                      # cofre novo, semeado do ambiente
    assert seed_secret_vault() is True
    assert sv.get_secret_vault().get("bridge", scope="local_agent") == b"segredo-do-tauri"


def test_grant_do_cerebro_verifica_com_o_mesmo_segredo(monkeypatch):
    # O mesmo ANTS_BRIDGE_SECRET usado pelos dois lados: assina e verifica.
    monkeypatch.setenv("ANTS_BRIDGE_SECRET", "aperto-de-mao-42")
    token = CT.sign_command("CAN_READ_FILES", "/tmp/nota.txt", ttl_seconds=60)
    ok, grant = CT.verify_command(token)
    assert ok is True
    assert grant.capability == "CAN_READ_FILES"


def test_segredo_diferente_rejeita_o_grant(monkeypatch):
    monkeypatch.setenv("ANTS_BRIDGE_SECRET", "segredo-A")
    token = CT.sign_command("CAN_READ_FILES", "/tmp/nota.txt", ttl_seconds=60)
    # corpo com outro segredo → assinatura não confere
    ok, _ = CT.verify_command(token, secret=b"segredo-B")
    assert ok is False


def test_derivacao_por_dispositivo_do_mestre_da_ponte(monkeypatch):
    monkeypatch.setenv("ANTS_BRIDGE_SECRET", "mestre-da-ponte")
    sv._INSTANCE = None
    seed_secret_vault()
    d1 = sv.derive_bridge_secret("notebook")
    d2 = sv.derive_bridge_secret("celular")
    assert d1 is not None and d2 is not None and d1 != d2   # 1 por dispositivo
