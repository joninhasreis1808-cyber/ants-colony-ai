"""Autoexplicação de decisões (≤50 linhas, leve).

Toda decisão importante gera uma explicação legível com os motivos
ordenados — transparência real para a interface.
"""
from __future__ import annotations


class Explainer:
    def explain(self, decision: str, reasons: list[str]) -> dict:
        reasons = [r for r in (reasons or []) if r][:5]
        return {"decision": decision, "reasons": reasons,
                "text": self._format(decision, reasons)}

    def _format(self, decision: str, reasons: list[str]) -> str:
        if not reasons:
            return f"Escolhi {decision}."
        lines = [f"Escolhi {decision} porque:"]
        for i, r in enumerate(reasons, 1):
            lines.append(f"  {i}. {r}")
        return "\n".join(lines)
