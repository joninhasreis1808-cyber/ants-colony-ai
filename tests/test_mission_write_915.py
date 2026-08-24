"""Prova do poder de ação (9.15) — a missão ESCREVE arquivo, gated e honesta.

Novo poder Manus: quando o objetivo pede escrita ("escreva … no arquivo …"), a
rota device_action leva o passo 'agir' a chamar a ferramenta write_file de
verdade — sempre pela porta gated. Dupla trava do dono:
  • sem o escopo `write_files` → recusa honesta (não grava, não inventa);
  • com escopo mas sem confirm → PRÉVIA (dry-run): diz o que faria, não grava;
  • com escopo + confirm + caminho autorizado → grava de verdade.
O path_guard barra caminhos proibidos mesmo autorizado (testado alhures).
"""
from __future__ import annotations

import asyncio

import pytest

from backend.hivemind.mission_runner import run_mission
from backend.hivemind.tool_executor import make_tool_executor, parse_write_request
from backend.memory.shared_memory import SharedMemory
from backend.permissions.device_scopes import get_device_scopes
from backend.permissions.path_guard import get_path_guard


def _mem():
    return SharedMemory(":memory:")


@pytest.fixture()
def limpa_permissoes():
    """Começa e termina sem o escopo de escrita (o gate precisa estar fechado)."""
    get_device_scopes().revoke_all()
    yield
    get_device_scopes().revoke_all()


def test_parse_write_request():
    p = parse_write_request('escreva "olá mundo" no arquivo /tmp/saida.txt')
    assert p and p["path"] == "/tmp/saida.txt" and p["content"] == "olá mundo"
    assert parse_write_request("qual a capital da França") is None


def test_escrita_sem_escopo_recusa_honesta(limpa_permissoes):
    goal = 'escreva "oi" no arquivo /tmp/ants_teste_915.txt'
    out = asyncio.run(run_mission(goal, _mem(),
                                  executor=make_tool_executor("", False, False)))
    assert out["route"]["name"] == "device_action"
    tu = out["tools_used"]
    assert any(t["tool"] == "write_file" and t["allowed"] is False for t in tu), tu
    assert out["state"] == "done"          # recusa é honesta, não quebra a missão


def test_escrita_dry_run_com_escopo_sem_confirm(tmp_path, limpa_permissoes):
    get_device_scopes().grant("write_files")
    get_path_guard().allow(str(tmp_path))
    alvo = tmp_path / "nota.txt"
    goal = f'escreva "conteudo real" no arquivo {alvo}'
    out = asyncio.run(run_mission(goal, _mem(),
                                  executor=make_tool_executor("", False, False)))
    tu = out["tools_used"]
    assert any(t["tool"] == "write_file" and t["allowed"] for t in tu), tu
    assert not alvo.exists(), "dry-run não pode gravar"


def test_escrita_grava_de_verdade_com_confirm(tmp_path, limpa_permissoes):
    get_device_scopes().grant("write_files")
    get_path_guard().allow(str(tmp_path))
    alvo = tmp_path / "nota.txt"
    goal = f'escreva "conteudo real" no arquivo {alvo}'
    out = asyncio.run(run_mission(goal, _mem(),
                                  executor=make_tool_executor("", False, False, True)))
    assert alvo.exists() and alvo.read_text(encoding="utf-8") == "conteudo real"
    assert any(t["tool"] == "write_file" and t["ok"] for t in out["tools_used"])
