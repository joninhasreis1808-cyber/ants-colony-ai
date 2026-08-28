"""Modos de deliberação (9.19 · FASE 2): FAST / DELIBERATE / CRITICAL.

Prova o mapa risco→modo, que a severidade nunca é rebaixada por confiança alta,
e que o gate de ações carimba o modo real na decisão.
"""
from __future__ import annotations

from backend.action.action_gate import get_action_gate
from backend.cognitive.deliberation_mode import DeliberationMode, decide
from backend.permissions.device_scopes import get_device_scopes


def test_baixo_risco_alta_confianca_e_fast():
    p = decide("low", sensitive=False, confidence=0.9)
    assert p.mode is DeliberationMode.FAST
    assert p.simulate is False and p.require_confirmation is False


def test_risco_medio_e_deliberate():
    p = decide("medium")
    assert p.mode is DeliberationMode.DELIBERATE
    assert p.simulate is True and p.require_confirmation is False


def test_baixo_risco_mas_confianca_baixa_puxa_deliberate():
    p = decide("low", confidence=0.2)
    assert p.mode is DeliberationMode.DELIBERATE


def test_risco_alto_e_critical_com_confirmacao():
    p = decide("high")
    assert p.mode is DeliberationMode.CRITICAL
    assert p.require_confirmation is True and p.simulate is True


def test_sensivel_e_critical_mesmo_com_confianca_alta():
    # Segurança acima de pressa: sensível nunca vira FAST.
    p = decide("low", sensitive=True, confidence=0.99)
    assert p.mode is DeliberationMode.CRITICAL


def test_gate_carimba_fast_em_leitura():
    scopes = get_device_scopes()
    scopes.grant("read_files")
    try:
        pg = __import__("backend.permissions.path_guard", fromlist=["get_path_guard"])
        pg.get_path_guard().allow("/tmp")
        d = get_action_gate().evaluate("read", "/tmp/nota.txt")
        assert d.allowed and d.mode == "fast"
    finally:
        scopes.revoke("read_files")


def test_gate_carimba_critical_em_acao_destrutiva():
    scopes = get_device_scopes()
    scopes.grant("write_files")
    try:
        import backend.permissions.path_guard as pgmod
        pgmod.get_path_guard().allow("/tmp")
        d = get_action_gate().evaluate("delete", "/tmp/alvo.txt")
        # destrutiva → sensível → CRITICAL + precisa de confirmação
        assert d.mode == "critical"
        assert d.needs_confirmation is True
    finally:
        scopes.revoke("write_files")
