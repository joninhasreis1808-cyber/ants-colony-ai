"""Runtime do corpo local (9.18 · FASE 5) — servidor (ponte) × dispositivo (nativo).

A Mente Colmeia mora no servidor (Render); o corpo mora no dispositivo (app Tauri).
As capacidades de **dispositivo** (tela, app, comando) só têm sentido — e só podem
executar — no runtime NATIVO. No servidor, o executor apenas VALIDA a segurança e
delega ao agente nativo; nunca age no dispositivo.

`ANTS_LOCAL_AGENT=native` marca o processo como o Local Agent nativo. Sem isso, é o
servidor/ponte de referência (padrão) — honesto e seguro.
"""
from __future__ import annotations

import os

_NATIVE = {"native", "tauri", "local", "1", "true", "sim"}


def is_native() -> bool:
    """Este processo é o Local Agent NATIVO (pode agir no dispositivo)?"""
    return (os.environ.get("ANTS_LOCAL_AGENT") or "").strip().lower() in _NATIVE


def runtime_name() -> str:
    return "native" if is_native() else "server"
