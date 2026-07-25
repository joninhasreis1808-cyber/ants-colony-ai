"""Testes da Parte C — execução real de device (8.0), sob a Parte B.

Usa runtime nativo simulado (ANTS_RUNTIME=native) e pasta temporária na
whitelist. Sem device real: input degrada honestamente; arquivos executam de
verdade no tmp; verify_cycle prova sucesso/retry/pausa.
"""
from __future__ import annotations

import pytest

from backend.action.device_files import DeviceFiles
from backend.action.input_controller import InputController
from backend.action.verify_cycle import VerifyCycle
from backend.permissions.device_scopes import get_device_scopes
from backend.permissions.path_guard import get_path_guard


@pytest.fixture
def native(monkeypatch):
    monkeypatch.setenv("ANTS_RUNTIME", "native")
    yield


# ---- C.2 arquivos ----
def test_web_mode_apenas_declara(tmp_path):
    get_device_scopes().grant("write_files")
    get_path_guard().allow(str(tmp_path))
    out = DeviceFiles().create(str(tmp_path / "a.txt"), "oi")
    assert out["executed"] is False and out["declared"] is True   # modo web


def test_native_cria_move_e_apaga_de_verdade(native, tmp_path):
    get_device_scopes().grant("write_files")
    get_device_scopes().grant("read_files")
    get_path_guard().allow(str(tmp_path))
    df = DeviceFiles()
    f = tmp_path / "nota.txt"
    assert df.create(str(f), "conteudo")["executed"] is True
    assert f.exists()
    # apagar é destrutivo → exige confirmação
    r = df.delete(str(f))
    assert r.get("needs_confirmation") is True and f.exists()
    r2 = df.delete(str(f), confirmed=True)
    assert r2["executed"] is True and not f.exists()


def test_native_fora_da_whitelist_recusa(native, tmp_path):
    get_device_scopes().grant("write_files")
    # NÃO autoriza tmp_path → recusa honesta
    out = DeviceFiles().create(str(tmp_path / "x.txt"), "x")
    assert out.get("denied") is True


def test_dry_run_nao_altera(native, tmp_path):
    get_device_scopes().grant("write_files")
    get_path_guard().allow(str(tmp_path))
    f = tmp_path / "d.txt"
    f.write_text("orig")
    out = DeviceFiles().delete(str(f), confirmed=True, dry_run=True)
    assert out["dry_run"] is True and f.exists()   # dry-run não apaga


# ---- C.1 input (degradação honesta) ----
def test_input_declara_quando_indisponivel():
    ic = InputController()
    info = ic.get_platform()
    assert "os" in info and "backend" in info
    get_device_scopes().grant("control_input")
    out = ic.click(10, 10)
    # headless/sem backend → declarado, nunca falso sucesso silencioso
    assert out["executed"] is False
    assert out.get("declared") or out.get("denied")


# ---- C.5 verify cycle ----
def test_verify_cycle_sucesso_quando_muda():
    state = {"v": 0}
    vc = VerifyCycle()
    r = vc.run(lambda: dict(state),
               lambda: state.__setitem__("v", state["v"] + 1),
               expect_change=True, label="incrementa")
    assert r.success is True and r.attempts == 1 and r.changed is True
    assert "verified" in r.events


def test_verify_cycle_para_em_3_falhas_e_pausa_missao():
    vc = VerifyCycle()
    # ação que nunca muda o estado → falha após 3 tentativas
    r = vc.run(lambda: {"v": 1}, lambda: None, expect_change=True,
               mission="m1", label="acao1")
    assert r.success is False and r.attempts == 3
    # 3 ações diferentes falhas na mesma missão → pausa
    vc.run(lambda: {"v": 1}, lambda: None, expect_change=True, mission="m1", label="a2")
    vc.run(lambda: {"v": 1}, lambda: None, expect_change=True, mission="m1", label="a3")
    assert vc.mission_paused("m1") is True
