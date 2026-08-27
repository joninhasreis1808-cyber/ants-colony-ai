"""FASE 5 · 2ª capacidade real: ESCRITA de arquivos, gated (9.18).

Mesma defesa em profundidade da leitura + a trava extra da escrita: dry-run por
padrão, gravação real só com confirm:true. Grant assinado + escopo write_files +
path_guard + capacidade aberta. Nenhuma execução de comando/tela.
"""
from __future__ import annotations

import pytest

from backend.local_agent import capability_tokens as CT
from backend.local_agent import executor as EX
from backend.permissions.device_scopes import get_device_scopes
from backend.permissions.path_guard import get_path_guard

SECRET = b"segredo-ponte-write-918"


@pytest.fixture()
def limpa():
    get_device_scopes().revoke_all()
    yield
    get_device_scopes().revoke_all()


def test_escrita_dry_run_por_padrao_nao_grava(tmp_path, limpa):
    alvo = tmp_path / "nota.txt"
    get_device_scopes().grant("write_files")
    get_path_guard().allow(str(tmp_path))
    tok = CT.sign_command("CAN_WRITE_FILES", str(alvo), secret=SECRET)
    out = EX.execute_local(tok, args={"content": "oi"}, secret=SECRET, seen=set())
    assert out["ok"] and not alvo.exists()          # dry-run: não gravou
    assert out["result"].get("dry_run") is True


def test_escrita_real_com_confirm(tmp_path, limpa):
    alvo = tmp_path / "nota.txt"
    get_device_scopes().grant("write_files")
    get_path_guard().allow(str(tmp_path))
    tok = CT.sign_command("CAN_WRITE_FILES", str(alvo), secret=SECRET)
    out = EX.execute_local(tok, args={"content": "conteúdo real", "confirm": True},
                           secret=SECRET, seen=set())
    assert out["ok"] and alvo.read_text(encoding="utf-8") == "conteúdo real"


def test_escrita_sem_escopo_recusa(tmp_path, limpa):
    alvo = tmp_path / "x.txt"
    get_path_guard().allow(str(tmp_path))           # caminho ok, SEM escopo
    tok = CT.sign_command("CAN_WRITE_FILES", str(alvo), secret=SECRET)
    out = EX.execute_local(tok, args={"content": "x", "confirm": True},
                           secret=SECRET, seen=set())
    assert out["ok"] is False and out["allowed"] is False and not alvo.exists()


def test_escrita_fora_da_whitelist_barra(tmp_path, limpa):
    # escopo concedido, mas caminho NÃO autorizado → path_guard barra.
    get_device_scopes().grant("write_files")
    tok = CT.sign_command("CAN_WRITE_FILES", "/etc/ants_hack.txt", secret=SECRET)
    out = EX.execute_local(tok, args={"content": "x", "confirm": True},
                           secret=SECRET, seen=set())
    assert out["ok"] is False
