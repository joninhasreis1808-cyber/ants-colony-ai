"""Endpoints do superorganismo: cognição, raciocínio e conhecimento.

Expõe o pipeline cognitivo, o motor de raciocínio próprio, o grafo de
conhecimento e a consciência de limitações. Instâncias vivas no processo.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.cognitive.orchestrator import CognitiveOrchestrator
from backend.intelligence.limitations import Limitations
from backend.reasoning.engine import ReasoningEngine
from backend.reasoning.inference import InferenceEngine

router = APIRouter(prefix="/mind", tags=["superorganism"])

COGNITIVE = CognitiveOrchestrator()
REASONER = ReasoningEngine()
INFERENCE = InferenceEngine()
LIMITS = Limitations()


class ThinkIn(BaseModel):
    question: str
    knowledge: list[str] = []


class ReasonIn(BaseModel):
    question: str
    context: list[str] = []


class InferIn(BaseModel):
    facts: list[str]
    goal: str | None = None


@router.post("/think")
async def think(body: ThinkIn) -> dict[str, Any]:
    """Pipeline cognitivo completo (9 camadas) sobre a pergunta."""
    r = COGNITIVE.think(body.question, body.knowledge)
    return {"answer": r.answer, "confidence": r.confidence,
            "domain": r.domain, "hypotheses": r.hypotheses,
            "gaps": r.gaps, "critique_ok": r.critique_ok}


@router.post("/reason")
async def reason(body: ReasonIn) -> dict[str, Any]:
    """Raciocínio próprio, offline, com passos rastreáveis."""
    ans = REASONER.reason(body.question, body.context)
    return {"answer": ans.text, "confidence": ans.confidence,
            "steps": [{"kind": s.kind, "content": s.content}
                      for s in ans.steps]}


@router.post("/infer")
async def infer(body: InferIn) -> dict[str, Any]:
    """Inferência lógica sobre fatos (forward/backward chaining)."""
    derived = INFERENCE.infer(body.facts)
    result: dict[str, Any] = {"derived": derived}
    if body.goal:
        result["can_derive"] = INFERENCE.can_derive(body.goal, body.facts)
    return result


@router.post("/assess")
async def assess(body: ReasonIn) -> dict[str, Any]:
    """Consciência das limitações: o que a colônia consegue fazer."""
    a = LIMITS.assess_capability(body.question)
    return {"capable": a.capable, "missing": a.missing,
            "explanation": a.explanation}
