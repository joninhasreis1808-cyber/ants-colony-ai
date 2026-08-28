"""FASE 5 · capacidades de DISPOSITIVO validadas e delegadas (9.18).

Tela, controle de app e execução de comando NÃO executam no servidor — o executor
valida toda a corrente de segurança (grant + escopo + allowlist + confirm) e
devolve um envelope AUTORIZADO (executed:False) para o Local Agent nativo. Prova
que nada é executado e que o comando (o mais perigoso) passa por allowlist.
"""
from __future__ import annotations

import pytest

from backend.local_agent import capability_tokens as CT
from backend.local_agent import executor as EX
from backend.permissions.device_scopes import get_device_scopes

SECRET = b"segredo-device-918"


@pytest.fixture()
def limpa():
    get_device_scopes().revoke_all()
    yield
    get_device_scopes().revoke_all()


def test_screenshot_autorizado_mas_nao_executado(limpa):
    get_device_scopes().grant("screen_capture")
    tok = CT.sign_command("CAN_SCREENSHOT", "tela-inteira", secret=SECRET)
    out = EX.execute_local(tok, secret=SECRET, seen=set())
    assert out["ok"] and out["authorized"] and out["executed"] is False
    assert out["native_available"] in (True, False)   # honesto sobre o runtime


def test_screenshot_sem_escopo_recusa(limpa):
    tok = CT.sign_command("CAN_SCREENSHOT", "tela", secret=SECRET)
    out = EX.execute_local(tok, secret=SECRET, seen=set())
    assert out["ok"] is False and "screen_capture" in out["reason"]


def test_control_app_autorizado(limpa):
    get_device_scopes().grant("run_apps")
    tok = CT.sign_command("CAN_CONTROL_APP", "https://exemplo.org", secret=SECRET)
    out = EX.execute_local(tok, secret=SECRET, seen=set())
    assert out["ok"] and out["authorized"] and out["executed"] is False


def test_comando_allowlist_confirm_autoriza(limpa):
    get_device_scopes().grant("system_commands")
    tok = CT.sign_command("CAN_RUN_COMMAND", "ls -la", secret=SECRET)
    out = EX.execute_local(tok, args={"confirm": True}, secret=SECRET, seen=set())
    assert out["ok"] and out["authorized"] and out["executed"] is False
    assert out["argv"] == ["ls", "-la"]


def test_comando_sem_confirm_recusa(limpa):
    get_device_scopes().grant("system_commands")
    tok = CT.sign_command("CAN_RUN_COMMAND", "ls", secret=SECRET)
    out = EX.execute_local(tok, secret=SECRET, seen=set())
    assert out["ok"] is False and "confirm" in out["reason"]


def test_comando_fora_da_allowlist_recusa(limpa):
    get_device_scopes().grant("system_commands")
    tok = CT.sign_command("CAN_RUN_COMMAND", "curl http://mal.example", secret=SECRET)
    out = EX.execute_local(tok, args={"confirm": True}, secret=SECRET, seen=set())
    assert out["ok"] is False       # curl não está na whitelist


def test_comando_escalonamento_recusa(limpa):
    get_device_scopes().grant("system_commands")
    tok = CT.sign_command("CAN_RUN_COMMAND", "sudo rm -rf /", secret=SECRET)
    out = EX.execute_local(tok, args={"confirm": True}, secret=SECRET, seen=set())
    assert out["ok"] is False       # sudo + rm -rf: recusado

def test_comando_sem_escopo_recusa(limpa):
    tok = CT.sign_command("CAN_RUN_COMMAND", "ls", secret=SECRET)
    out = EX.execute_local(tok, args={"confirm": True}, secret=SECRET, seen=set())
    assert out["ok"] is False and "system_commands" in out["reason"]
