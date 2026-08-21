"""Chaos das ferramentas gated (9.10 · FASE G · G2) — resiliência sob abuso.

Diagnóstico: mãos que modificam precisam aguentar entradas hostis — conteúdo
gigante, travessia de caminho (..), argumentos malformados, escopo revogado no
meio. Se qualquer um derrubasse o processo ou escapasse da trava, seria falha de
segurança.
Prova: cada abuso recebe uma RECUSA/erro honesto, sem crash e sem tocar em nada
fora das pastas autorizadas.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from backend.permissions.device_scopes import get_device_scopes
from backend.permissions.path_guard import get_path_guard
from backend.tools.registry import get_tool_registry


@pytest.fixture()
def sandbox(tmp_path):
    pg, sc = get_path_guard(), get_device_scopes()
    pg.allow(str(tmp_path))
    sc.grant("write_files")
    yield tmp_path
    sc.revoke("write_files")
    pg.disallow(str(tmp_path))


def test_conteudo_gigante_e_recusado_sem_crash(sandbox):
    reg = get_tool_registry()
    huge = "x" * (300_000)
    r = reg.run("write_file", {"path": str(sandbox / "big.txt"),
                               "content": huge, "confirm": True})
    assert r["ok"] and r["result"]["ok"] is False
    assert "excede" in r["result"]["error"]
    assert not (sandbox / "big.txt").exists()


def test_travessia_de_caminho_e_bloqueada(sandbox):
    reg = get_tool_registry()
    escape = str(sandbox / ".." / ".." / "etc" / "passwd_falso")
    r = reg.run("write_file", {"path": escape, "content": "x", "confirm": True})
    assert r["allowed"] is False                          # path_guard barrou


def test_delete_travessia_bloqueada(sandbox):
    reg = get_tool_registry()
    r = reg.run("delete_path", {"path": "/etc", "confirm": True})
    assert r["allowed"] is False


def test_args_malformados_nao_derrubam(sandbox):
    reg = get_tool_registry()
    # path ausente → string vazia → fora das pastas autorizadas → recusa
    r = reg.run("write_file", {"content": "x", "confirm": True})
    assert r["allowed"] is False
    # compute com entrada sem cálculo → erro honesto, não crash
    r2 = reg.run("compute", {"expression": "isto não é conta"})
    assert r2["ok"] and r2["result"]["ok"] is False


def test_ferramenta_desconhecida_e_recusada():
    r = get_tool_registry().run("ferramenta_que_nao_existe", {})
    assert r["allowed"] is False and "desconhecida" in r["reason"]


def test_escopo_revogado_no_meio_bloqueia_a_proxima(sandbox):
    reg = get_tool_registry()
    fp = sandbox / "a.txt"
    assert reg.run("write_file", {"path": str(fp), "content": "1",
                                  "confirm": True})["ok"]
    get_device_scopes().revoke("write_files")             # dono revoga
    r = reg.run("write_file", {"path": str(fp), "content": "2", "confirm": True})
    assert r["allowed"] is False                          # recusa imediata
    assert fp.read_text() == "1"                          # 2ª escrita não ocorreu


def test_compute_permanece_disponivel_sob_qualquer_escopo():
    # compute é puro: revogar escopos de device não o afeta
    get_device_scopes().revoke_all()
    r = get_tool_registry().run("compute", {"expression": "40 + 2"})
    assert r["ok"] and r["result"]["answer"] == "42"
