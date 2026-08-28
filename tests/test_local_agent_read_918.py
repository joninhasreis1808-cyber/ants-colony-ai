"""FASE 5 · 1ª capacidade real: LEITURA de arquivos, ponta a ponta e gated (9.18).

Prova a defesa em profundidade: grant assinado + escopo do dono + path_guard +
capacidade aberta. Sem os quatro, recusa honesta e auditada. Só leitura; nenhuma
escrita/execução.
"""
from __future__ import annotations

import pytest

from backend.local_agent import capability_tokens as CT
from backend.local_agent import executor as EX
from backend.permissions.device_scopes import get_device_scopes
from backend.permissions.path_guard import get_path_guard

SECRET = b"segredo-ponte-read-918"


@pytest.fixture()
def limpa():
    get_device_scopes().revoke_all()
    yield
    get_device_scopes().revoke_all()


def test_leitura_ponta_a_ponta_com_todas_as_travas(tmp_path, limpa):
    alvo = tmp_path / "nota.txt"
    alvo.write_text("conteúdo autorizado", encoding="utf-8")
    get_device_scopes().grant("read_files")
    get_path_guard().allow(str(tmp_path))
    tok = CT.sign_command("CAN_READ_FILES", str(alvo), secret=SECRET)
    out = EX.execute_local(tok, secret=SECRET, seen=set())
    assert out["ok"] and out["capability"] == "CAN_READ_FILES"
    assert "conteúdo autorizado" in str(out["result"])


def test_sem_escopo_recusa_honesta(tmp_path, limpa):
    alvo = tmp_path / "x.txt"; alvo.write_text("x", encoding="utf-8")
    get_path_guard().allow(str(tmp_path))          # caminho ok, mas SEM escopo
    tok = CT.sign_command("CAN_READ_FILES", str(alvo), secret=SECRET)
    out = EX.execute_local(tok, secret=SECRET, seen=set())
    assert out["ok"] is False and out["allowed"] is False


def test_grant_invalido_negado(limpa):
    out = EX.execute_local("lixo.token", secret=SECRET, seen=set())
    assert out["ok"] is False and out["allowed"] is False


def test_capacidade_nao_aberta_recusa(limpa):
    # navegador ainda NÃO foi aberto — mesmo com grant válido, recusa.
    tok = CT.sign_command("CAN_BROWSER", "https://x", secret=SECRET)
    out = EX.execute_local(tok, secret=SECRET, seen=set())
    assert out["ok"] is False and "ainda não aberta" in out["reason"]


def test_auditoria_registra_tentativas(tmp_path, limpa):
    antes = len(EX.audit_log())
    tok = CT.sign_command("CAN_READ_FILES", str(tmp_path / "z.txt"), secret=SECRET)
    EX.execute_local(tok, secret=SECRET, seen=set())   # sem escopo → recusado
    depois = EX.audit_log()
    assert len(depois) > antes
    assert depois[-1]["capability"] == "CAN_READ_FILES"
