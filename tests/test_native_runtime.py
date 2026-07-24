"""Testes do runtime nativo, persistência e índice vetorial opcional (8.0 · A/F)."""
from __future__ import annotations

from backend.action.runtime import display_server, is_native, runtime_info
from backend.memory.lancedb_store import LanceDBStore


def test_runtime_web_por_padrao(monkeypatch):
    monkeypatch.delenv("ANTS_RUNTIME", raising=False)
    assert is_native() is False
    info = runtime_info()
    assert info["mode"] == "web"
    assert info["can_execute_device_actions"] is False
    assert "display_server" in info


def test_runtime_nativo_quando_env(monkeypatch):
    monkeypatch.setenv("ANTS_RUNTIME", "native")
    assert is_native() is True
    assert runtime_info()["mode"] == "native"


def test_display_server_detecta_headless(monkeypatch):
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("DISPLAY", raising=False)
    import platform
    if platform.system() == "Linux":
        assert display_server() == "headless"


def test_sidecar_prepara_dir_persistente(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTS_DATA_DIR", str(tmp_path))
    for k in ("ANTS_DB", "ANTS_SCOPES", "ANTS_AUDIT_LOG"):
        monkeypatch.delenv(k, raising=False)
    from backend.api.sidecar import _prepare_native_data_dir
    _prepare_native_data_dir()
    import os
    assert os.environ["ANTS_DB"].startswith(str(tmp_path))
    assert os.environ["ANTS_SCOPES"].endswith("scopes.json")


def test_lancedb_opcional_degrada_sem_quebrar():
    store = LanceDBStore()
    # lib ausente no ambiente padrão → indisponível, nunca quebra
    if not store.available:
        assert store.add("x", [0.1, 0.2]) is False
        assert store.search([0.1, 0.2]) == []
