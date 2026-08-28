"""Secret Vault dedicado (9.20 · Passo 1): cofre com escopo, rotação, derivação.

Prova que o cofre guarda/lê/gira/revoga com escopo e prazo, deriva segredos
por-contexto de um mestre (a base para a ponte por-dispositivo), verifica em
tempo constante e NUNCA registra o valor do segredo na auditoria.
"""
from __future__ import annotations

import time

import pytest

from backend.security.secret_vault import SecretVault, derive_bridge_secret, get_secret_vault


def test_put_get_e_escopo():
    v = SecretVault()
    v.put("api_token", "segredo-123", scope="api")
    # escopo certo (ou nenhum) → lê; escopo errado → recusa
    assert v.get("api_token", scope="api") == b"segredo-123"
    assert v.get("api_token") == b"segredo-123"
    assert v.get("api_token", scope="local_agent") is None


def test_rotacao_invalida_o_antigo_na_hora():
    v = SecretVault()
    v.put("k", "velho")
    ver = v.rotate("k", "novo")
    assert ver == 2
    assert v.get("k") == b"novo"
    assert v.verify("k", "velho") is False
    assert v.verify("k", "novo") is True


def test_revogar_remove():
    v = SecretVault()
    v.put("k", "x")
    v.revoke("k")
    assert v.exists("k") is False and v.get("k") is None


def test_ttl_expira():
    v = SecretVault()
    v.put("efemero", "x", ttl_seconds=-1)   # já nasce expirado
    assert v.get("efemero") is None
    assert "efemero" not in v.names()


def test_derivacao_deterministica_e_por_contexto():
    v = SecretVault()
    v.put("bridge", "mestre", scope="local_agent")
    d1 = v.derive("bridge", "device:notebook", scope="local_agent")
    d2 = v.derive("bridge", "device:notebook", scope="local_agent")
    d3 = v.derive("bridge", "device:celular", scope="local_agent")
    assert d1 == d2                 # determinístico
    assert d1 != d3                 # contexto diferente → segredo diferente
    assert len(d1) == 32


def test_derivar_gira_com_o_mestre():
    v = SecretVault()
    v.put("bridge", "mestre-A", scope="local_agent")
    antes = v.derive("bridge", "device:x", scope="local_agent")
    v.rotate("bridge", "mestre-B")
    depois = v.derive("bridge", "device:x", scope="local_agent")
    assert antes != depois          # girar o mestre derruba todos os derivados


def test_verify_tempo_constante():
    v = SecretVault()
    v.put("k", "abcxyz")
    assert v.verify("k", "abcxyz") is True
    assert v.verify("k", "errado") is False


def test_auditoria_nunca_grava_o_valor():
    v = SecretVault()
    v.put("k", "super-secreto-42")
    v.get("k")
    v.verify("k", "super-secreto-42")
    dump = str(v.audit())
    assert "super-secreto-42" not in dump          # valor jamais vaza no log
    assert any(a["action"] == "put" and a["name"] == "k" for a in v.audit())


def test_info_expõe_metadados_sem_valor():
    v = SecretVault()
    v.put("k", "x", scope="api")
    info = v.info("k")
    assert info["scope"] == "api" and info["version"] == 1
    assert "value" not in info


def test_seed_from_env_idempotente(monkeypatch):
    monkeypatch.setenv("ANTS_BRIDGE_SECRET", "do-ambiente")
    v = SecretVault()
    n1 = v.seed_from_env()
    n2 = v.seed_from_env()          # 2ª vez não recarrega
    assert n1 >= 1 and n2 == 0
    assert v.get("bridge", scope="local_agent") == b"do-ambiente"


def test_derive_bridge_secret_singleton(monkeypatch):
    monkeypatch.setenv("ANTS_BRIDGE_SECRET", "mestre-proc")
    # força um singleton novo que semeia do ambiente
    import backend.security.secret_vault as sv
    sv._INSTANCE = None
    d = derive_bridge_secret("notebook-do-dono")
    assert d is not None and len(d) == 32
