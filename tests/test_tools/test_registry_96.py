"""ToolRegistry + Capability System (9.6 · FASE A).

Prova a separação capacidade ("sei fazer") ≠ permissão ("posso fazer") e o
Scope Guard: a colônia só executa uma ferramenta com o escopo concedido E o
caminho autorizado (path_guard). Ferramentas READ-ONLY, seguras.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.permissions.device_scopes import get_device_scopes
from backend.permissions.path_guard import get_path_guard
from backend.tools.registry import get_tool_registry

client = TestClient(app)


@pytest.fixture()
def clean_perms():
    """Isola o estado de permissões/pastas por teste."""
    get_device_scopes().revoke("read_files")
    yield
    get_device_scopes().revoke("read_files")


def test_catalogo_lista_ferramentas():
    reg = get_tool_registry()
    names = {t["name"] for t in reg.list()}
    assert {"list_dir", "read_file"} <= names
    tool = next(t for t in reg.list() if t["name"] == "list_dir")
    assert tool["capability"] == "filesystem.read"
    assert tool["scope"] == "read_files" and tool["risk"] == "low"


def test_capacidade_sem_permissao_e_recusada(clean_perms):
    # SABE fazer (filesystem.read), mas NÃO PODE (escopo read_files não concedido)
    out = get_tool_registry().run("list_dir", {"path": "/tmp"})
    assert out["allowed"] is False and out["ok"] is False
    assert "escopo 'read_files'" in out["reason"]


def test_com_escopo_mas_caminho_nao_autorizado_recusa(clean_perms):
    get_device_scopes().grant("read_files")
    # escopo concedido, mas a pasta não está na whitelist do path_guard
    out = get_tool_registry().run("list_dir", {"path": "/etc"})
    assert out["allowed"] is False
    assert "fora das pastas autorizadas" in out["reason"]


def test_execucao_valida_lista_e_le(clean_perms, tmp_path):
    (tmp_path / "a.txt").write_text("conteúdo de teste", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    get_device_scopes().grant("read_files")
    get_path_guard().allow(str(tmp_path))
    try:
        ls = get_tool_registry().run("list_dir", {"path": str(tmp_path)})
        assert ls["ok"] is True
        names = {e["name"] for e in ls["result"]["entries"]}
        assert {"a.txt", "sub"} <= names
        rd = get_tool_registry().run("read_file", {"path": str(tmp_path / "a.txt")})
        assert rd["ok"] is True and "conteúdo de teste" in rd["result"]["text"]
    finally:
        get_path_guard().disallow(str(tmp_path))


def test_ferramenta_desconhecida_recusa():
    out = get_tool_registry().run("rm_rf_tudo", {})
    assert out["allowed"] is False and "desconhecida" in out["reason"]


def test_endpoint_lista_e_roda(clean_perms):
    r = client.get("/tools").json()
    assert any(t["name"] == "list_dir" for t in r["tools"])
    # run sem escopo → recusa honesta (200 com allowed:false)
    run = client.post("/tools/run", json={"name": "list_dir", "args": {"path": "/tmp"}})
    assert run.status_code == 200 and run.json()["allowed"] is False
