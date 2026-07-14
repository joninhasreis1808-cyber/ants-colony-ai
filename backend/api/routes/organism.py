"""Endpoints do organismo — Ant's 5.0/6.0 (Parte A).

Expõe o metabolismo, hormônios, sistema imunológico, autonomia graduada,
missões permanentes, o observador, o DNA e o aprendizado por feedback.
Instâncias vivas no processo, para a interface refletir o organismo real.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.hivemind.circadian import Circadian
from backend.hivemind.colony_dna import ColonyDNA
from backend.hivemind.hormones import Hormone, HormoneSystem
from backend.intelligence.observer import Observer
from backend.intelligence.permanent_missions import PermanentMissions
from backend.learning.feedback_learner import FeedbackLearner
from backend.security.immune_system import ImmuneSystem

router = APIRouter(prefix="/organism", tags=["organism"])

HORMONES = HormoneSystem()
IMMUNE = ImmuneSystem()
MISSIONS = PermanentMissions()
OBSERVER = Observer()
DNA = ColonyDNA()
FEEDBACK = FeedbackLearner()
CIRCADIAN = Circadian()


class ThreatIn(BaseModel):
    action: str


class FeedbackIn(BaseModel):
    strategy: str
    kind: str          # approve / reject / teach / default / forbid
    text: str = ""


class MissionIn(BaseModel):
    description: str
    frequency: float = 3600.0


@router.get("/vitals")
async def vitals(hour: int = 12) -> dict[str, Any]:
    """Sinais do organismo: hormônios, fase circadiana e imunidade."""
    return {
        "hormones": {h.value: HORMONES.get_hormone_level(h) for h in Hormone},
        "risk_appetite": HORMONES.risk_appetite(),
        "circadian_phase": CIRCADIAN.get_current_phase(hour).value,
        "immune_signatures": IMMUNE.signature_count(),
    }


@router.post("/immune/analyze")
async def immune_analyze(body: ThreatIn) -> dict[str, Any]:
    """Analisa uma ação quanto a ameaça (aprendendo assinaturas)."""
    level = IMMUNE.analyze_threat(body.action)
    return {"level": level.value, "known": IMMUNE.is_known_threat(body.action)}


@router.post("/feedback")
async def feedback(body: FeedbackIn) -> dict[str, Any]:
    """Aplica o feedback do usuário a uma estratégia (ajusta pesos)."""
    kind = body.kind
    if kind == "approve":
        FEEDBACK.approve(body.strategy)
    elif kind == "reject":
        FEEDBACK.reject(body.strategy)
    elif kind == "teach":
        FEEDBACK.teach(body.text)
    elif kind == "default":
        FEEDBACK.make_default(body.strategy)
    elif kind == "forbid":
        FEEDBACK.forbid(body.strategy)
    return {"strategy": body.strategy,
            "weight": FEEDBACK.weight_of(body.strategy),
            "blocked": FEEDBACK.is_blocked(body.strategy)}


@router.get("/missions")
async def missions() -> dict[str, Any]:
    """Missões permanentes ativas."""
    return {"missions": MISSIONS.get_active_missions()}


@router.post("/missions")
async def add_mission(body: MissionIn) -> dict[str, Any]:
    """Registra uma missão permanente."""
    try:
        mid = MISSIONS.register_mission(body.description, body.frequency)
        return {"id": mid, "description": body.description}
    except ValueError as exc:
        return {"error": str(exc)}


@router.get("/dna")
async def dna() -> dict[str, Any]:
    """Genoma atual da colônia (traços herdáveis)."""
    return {"genome_size": DNA.genome_size(), "traits": DNA.inherit()}
