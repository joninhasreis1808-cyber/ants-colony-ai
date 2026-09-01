"""Grafo causal VIVO (A2 · roteiro de maestria).

Expõe o que as missões reais demonstraram: quais causas levaram a quais efeitos,
com que força, em que contexto e com que confiança média. É memória causal, não
correlação decorativa — e o Learner a consulta antes de propor estratégia.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.evaluation.causal_graph import get_causal_graph

router = APIRouter(tags=["causal"])


@router.get("/causal")
async def causal() -> dict[str, Any]:
    """Estado do grafo causal vivo (nós + arestas observadas)."""
    data = get_causal_graph().to_dict()
    data["note"] = ("relações observadas em missões reais; sem observação, "
                    "o grafo fica vazio — nunca inventa causalidade")
    return data


@router.get("/causal/explain/{effect}")
async def explain(effect: str) -> dict[str, Any]:
    """Explica um efeito pelos contribuintes (mais forte primeiro)."""
    g = get_causal_graph()
    return {"effect": effect, "causes": g.explain(effect),
            "roots": g.root_causes(effect)}
