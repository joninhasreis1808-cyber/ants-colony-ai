"""Prova das ferramentas da FASE D (9.8) — mãos que modificam e calculam, gated.

Diagnóstico: a colônia só tinha "mãos" de LEITURA (FASE A). Para agir como um
Manus, precisa escrever, criar, apagar e calcular — mas isso não pode ser um
cheque em branco: escrita/apagar são irreversíveis.
Correção: write_file/make_dir/delete_path (dry-run por padrão, confirm:true para
agir, sempre atrás do path_guard + escopo write_files/write_files/delete) e
compute (cálculo puro, sem escopo). Tudo pelo ToolRegistry, que valida
capacidade+permissão ANTES de executar.
Prova: sem escopo → recusa honesta; dry-run não toca no disco; confirm grava/apaga
de verdade; pasta não vazia é recusada mesmo com confirm; caminho fora das pastas
autorizadas é bloqueado; compute funciona sem escopo nenhum.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from backend.permissions.device_scopes import get_device_scopes
from backend.permissions.path_guard import get_path_guard
from backend.tools.registry import get_tool_registry


@pytest.fixture()
def sandbox(tmp_path):
    """Autoriza um diretório temporário e concede o escopo de escrita."""
    pg, sc = get_path_guard(), get_device_scopes()
    pg.allow(str(tmp_path))
    sc.grant("write_files")
    yield tmp_path
    sc.revoke("write_files")
    pg.disallow(str(tmp_path))


def test_compute_nao_exige_escopo_e_calcula():
    reg = get_tool_registry()
    assert reg.can_use("compute")                       # puro: sempre disponível
    r = reg.run("compute", {"expression": "12 * 12"})
    assert r["ok"] and r["result"]["answer"] == "144"


def test_write_sem_escopo_e_recusado(tmp_path):
    sc = get_path_guard()
    sc.allow(str(tmp_path))
    get_device_scopes().revoke("write_files")           # garante ausência
    reg = get_tool_registry()
    r = reg.run("write_file", {"path": str(tmp_path / "x.txt"), "content": "oi",
                               "confirm": True})
    assert r["allowed"] is False and r["ok"] is False
    assert "write_files" in r["reason"]
    assert not (tmp_path / "x.txt").exists()            # nada foi escrito
    get_path_guard().disallow(str(tmp_path))


def test_write_dry_run_nao_toca_no_disco(sandbox):
    reg = get_tool_registry()
    fp = sandbox / "nota.txt"
    r = reg.run("write_file", {"path": str(fp), "content": "prévia"})
    assert r["ok"] and r["result"]["dry_run"] and r["result"]["would_write"]
    assert not fp.exists()                              # dry-run: não gravou


def test_write_confirm_grava_de_verdade(sandbox):
    reg = get_tool_registry()
    fp = sandbox / "nota.txt"
    r = reg.run("write_file", {"path": str(fp), "content": "conteúdo real",
                               "confirm": True})
    assert r["ok"] and r["result"]["written"]
    assert fp.read_text(encoding="utf-8") == "conteúdo real"


def test_delete_recusa_pasta_nao_vazia_mesmo_com_confirm(sandbox):
    reg = get_tool_registry()
    d = sandbox / "cheia"
    d.mkdir()
    (d / "f.txt").write_text("x")
    r = reg.run("delete_path", {"path": str(d), "confirm": True})
    assert r["ok"] and r["result"]["ok"] is False
    assert d.exists()                                   # árvore intacta


def test_delete_confirm_apaga_arquivo(sandbox):
    reg = get_tool_registry()
    fp = sandbox / "apagar.txt"
    fp.write_text("tchau")
    r = reg.run("delete_path", {"path": str(fp), "confirm": True})
    assert r["ok"] and r["result"]["deleted"]
    assert not fp.exists()


def test_make_dir_dry_run_e_confirm(sandbox):
    reg = get_tool_registry()
    d = sandbox / "nova"
    assert reg.run("make_dir", {"path": str(d)})["result"]["dry_run"]
    assert not d.exists()
    reg.run("make_dir", {"path": str(d), "confirm": True})
    assert d.is_dir()


def test_caminho_fora_das_pastas_autorizadas_e_bloqueado():
    get_device_scopes().grant("write_files")
    reg = get_tool_registry()
    r = reg.run("write_file", {"path": "/tmp/ants_nao_autorizado_zzz.txt",
                               "content": "x", "confirm": True})
    assert r["allowed"] is False and "autorizadas" in r["reason"]
    assert not Path("/tmp/ants_nao_autorizado_zzz.txt").exists()
    get_device_scopes().revoke("write_files")


def test_catalogo_lista_as_novas_ferramentas():
    names = {t["name"] for t in get_tool_registry().list()}
    assert {"write_file", "make_dir", "delete_path", "compute"} <= names
