"""FASE 1 · Invariante do esquema de eventos (9.18) — mantém o contrato honesto.

Se alguém adicionar/remover um EventType ou uma Phase sem atualizar
`docs/visao/ESQUEMA_DE_EVENTOS.md`, este teste falha — forçando doc e código a
andarem juntos (a "voz" da colônia é um contrato, não um detalhe solto).
"""
from __future__ import annotations

from backend.core import Phase, TaskStatus
from backend.events.event_bus import EventType

# Conjunto canônico documentado (Camada 1). Deve espelhar o EventType do código.
_CANONICO = {
    "TASK_CREATED", "PLAN_CREATED", "RESEARCH_STARTED", "RESEARCH_COMPLETED",
    "HYPOTHESIS_CREATED", "HYPOTHESIS_REJECTED", "VERIFICATION_COMPLETED",
    "DECISION_TAKEN", "ACTION_STARTED", "ACTION_COMPLETED", "ACTION_FAILED",
    "ACTION_PLANNED", "ACTION_APPROVED", "ACTION_EXECUTED", "ACTION_VERIFIED",
    "BOT_RECRUITED", "BOT_RELEASED", "FEROMONE_DEPOSITED", "HORMONE_RELEASED",
    "MEMORY_STORED", "MEMORY_RECALLED", "CACHE_HIT", "CACHE_MISS",
    "ERROR_OCCURRED", "THREAT_DETECTED", "COLONY_STATE_CHANGED",
    "FEEDBACK_RECEIVED", "LEARNING_REGISTERED", "ALL",
}


def _event_constants() -> set[str]:
    return {n for n in vars(EventType)
            if n.isupper() and isinstance(getattr(EventType, n), str)}


def test_eventtype_bate_com_o_documentado():
    atual = _event_constants()
    faltando = _CANONICO - atual
    novos = atual - _CANONICO
    assert not faltando, f"documentados mas ausentes no código: {faltando}"
    assert not novos, (f"novos no código, faltam no ESQUEMA_DE_EVENTOS.md: {novos}")


def test_fases_pdca_estaveis():
    assert [p.value for p in Phase] == ["plan", "do", "check", "act"]


def test_task_status_estavel():
    vals = {s.value for s in TaskStatus}
    assert {"pending", "planning", "running", "done", "failed"} <= vals


def test_documento_existe_e_cita_camadas():
    from pathlib import Path
    doc = Path(__file__).resolve().parents[1] / "docs/visao/ESQUEMA_DE_EVENTOS.md"
    txt = doc.read_text(encoding="utf-8")
    assert "ColonyState" in txt
    assert "ants:task-done" in txt and "COLONY_STATE_CHANGED" in txt
