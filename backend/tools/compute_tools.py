"""Ferramenta de CÁLCULO exato (9.8 · FASE D) — a "mão" que calcula.

Cálculo puro, offline, sem tocar no dispositivo (por isso não exige escopo de
permissão — só a capacidade CAP_COMPUTE). Reusa o córtex determinístico (SymPy,
sem `eval`). Dá à colônia uma ferramenta uniforme de cálculo no ToolRegistry,
para o executor de missões e a autonomia (FASE E) chamarem como qualquer outra.
"""
from __future__ import annotations

from typing import Any


def compute(args: dict[str, Any]) -> dict[str, Any]:
    """Resolve uma expressão/pergunta aritmética exata (ou diz que não é cálculo)."""
    goal = str(args.get("expression") or args.get("question") or args.get("goal") or "")
    from backend.reasoning.deterministic import DeterministicCortex

    out = DeterministicCortex().solve(goal)
    if out is None:
        return {"input": goal, "ok": False,
                "reason": "não reconheci um cálculo exato aqui"}
    return {"input": goal, "ok": bool(out.ok), "answer": out.answer,
            "kind": out.kind, "steps": list(out.steps),
            "confidence": out.confidence}
