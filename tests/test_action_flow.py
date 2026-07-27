"""Testes do fluxo de ação (8.1 · B) — comando → permissão → plano → execução."""
from __future__ import annotations

import pytest

from backend.action.action_flow import ActionFlow
from backend.action.action_interpreter import ActionInterpreter
from backend.permissions.device_scopes import get_device_scopes
from backend.permissions.path_guard import get_path_guard


def test_interpreta_comandos():
    ai = ActionInterpreter()
    assert ai.interpret("Abra o Spotify").verb == "open"
    assert ai.interpret("Liste os arquivos da pasta Downloads").target_type == "folder"
    assert ai.interpret("Apague o arquivo x.txt").scope == "write_files"
    assert ai.interpret("Abra o Spotify no navegador").target_type == "url"
    assert ai.interpret("uma frase qualquer") is None


def test_sem_permissao_pede_permissao_nao_diz_nao_sei(tmp_path):
    get_device_scopes().revoke_all()
    flow = ActionFlow()
    p = flow.plan(f"Liste os arquivos da pasta {tmp_path}")
    assert p["needs_permission"] is True
    assert p["grant_scope"] == "read_files"
    assert "permissão" in p["answer"] and "não sei" not in p["answer"].lower()


def test_com_permissao_gera_plano_e_executa_lista_real(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTS_RUNTIME", "native")
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "b.txt").write_text("y")
    get_device_scopes().grant("read_files")
    get_path_guard().allow(str(tmp_path))
    flow = ActionFlow()
    p = flow.plan(f"Liste os arquivos da pasta {tmp_path}")
    assert p["needs_approval"] is True and p["plan_id"]
    r = flow.execute(p["plan_id"])
    assert r["executed"] is True
    assert "2 item" in r["answer"]


def test_pasta_nao_autorizada_pede_autorizacao(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTS_RUNTIME", "native")
    get_device_scopes().grant("read_files")
    # escopo concedido mas pasta NÃO autorizada → pede para autorizar a pasta
    flow = ActionFlow()
    p = flow.plan(f"Liste os arquivos da pasta {tmp_path}")
    assert p["needs_permission"] is True
    assert p["grant_path"] == str(tmp_path)
    assert p.get("grant_scope") is None          # o escopo já estava concedido


def test_caminho_blacklist_recusado_de_saida():
    flow = ActionFlow()
    get_device_scopes().grant("read_files")
    p = flow.plan("Liste os arquivos da pasta /etc")
    assert "Recusado" in p["answer"] and "blacklist" in p["answer"]
    assert not p.get("needs_approval")


def test_abrir_url_resolve_conhecido(monkeypatch):
    monkeypatch.setenv("ANTS_RUNTIME", "native")
    get_device_scopes().grant("run_apps")
    from backend.action.device_apps import DeviceApps
    calls = {}
    monkeypatch.setattr("webbrowser.open", lambda u: calls.setdefault("u", u))
    r = DeviceApps().open_url("spotify")
    assert r["executed"] is True and "spotify.com" in calls["u"]


def test_plano_aprovacao_cancela():
    flow = ActionFlow()
    get_device_scopes().grant("run_apps")
    p = flow.plan("Abra o Spotify")
    assert flow.cancel(p["plan_id"])["ok"] is True
    # já cancelado → executar não encontra
    assert flow.execute(p["plan_id"])["ok"] is False


def test_execute_plano_inexistente_e_honesto():
    assert ActionFlow().execute("nao-existe")["ok"] is False
