"""Calibrador VIVO (9.24 · integração): o hive alimenta o calibrador de confiança.

Prova que uma missão real registra (confiança, acerto auto-consistente) no
calibrador de processo, e que o endpoint /calibration expõe o estado vivo.
"""
from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

import backend.evaluation.confidence_calibration as CC
from backend.api.main import app
from backend.core import Task
from backend.hivemind.factory import build_hive

client = TestClient(app)


def _fresh_calibrator():
    CC._INSTANCE = None
    return CC.get_calibrator()


def test_missao_alimenta_o_calibrador_vivo():
    cal = _fresh_calibrator()
    assert cal.total == 0
    hive, _ = build_hive(db_path=":memory:")
    asyncio.run(hive.solve(Task(goal="quanto é 2+2")))
    # a missão registrou uma amostra (confiança prevista × acerto auto-consistente)
    assert cal.total >= 1


def test_calculo_exato_conta_como_acerto_ancorado():
    cal = _fresh_calibrator()
    hive, _ = build_hive(db_path=":memory:")
    asyncio.run(hive.solve(Task(goal="quanto é 7*6")))
    # cálculo exato → source=computation (ancorado), sem escalar → acerto
    assert any(row["observed"] > 0 for row in cal.reliability())


def test_endpoint_calibration_expoe_estado():
    _fresh_calibrator()
    hive, _ = build_hive(db_path=":memory:")
    asyncio.run(hive.solve(Task(goal="quanto é 1+1")))
    r = client.get("/calibration")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert "ece" in body and "note" in body


def test_feed_ignora_confianca_ausente():
    cal = _fresh_calibrator()
    from backend.hivemind.hive import Hivemind
    Hivemind._feed_calibrator(None, "computation", False)   # sem confiança → nada
    assert cal.total == 0
