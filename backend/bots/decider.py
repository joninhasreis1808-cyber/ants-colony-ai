"""DeciderBot — decide a resposta final com base em todo o contexto.

Lê a interpretação e as fontes acumuladas na memória compartilhada e
monta uma conclusão com um nível de confiança. A confiança deriva da
quantidade e da consistência das evidências coletadas pela colmeia.
"""
from __future__ import annotations

from typing import Any

from backend.bots.base import Bot


class DeciderBot(Bot):
    """Sintetiza a decisão/resposta final da colmeia."""

    name = "decider"
    skills = ("decide", "synthesize")

    async def plan(
        self, task_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "goal": payload.get("goal", ""),
            "interpretation": self.memory.get_context(
                task_id, "interpretation"
            )
            or {},
            "sources": self.memory.get_context(task_id, "sources") or [],
        }

    async def do(self, task_id: str, plan: dict[str, Any]) -> dict[str, Any]:
        interp = plan["interpretation"]
        sources = plan["sources"]
        summary = interp.get("summary", "")
        confidence = self._confidence(interp, sources)
        answer = summary or "Sem evidências suficientes para concluir."
        return {
            "goal": plan["goal"],
            "answer": answer,
            "confidence": confidence,
            "n_sources": len(sources),
            "equations_found": interp.get("equations", []),
        }

    def _confidence(
        self, interp: dict[str, Any], sources: list[Any]
    ) -> float:
        """Confiança em [0, 1] a partir de sinais de evidência."""
        score = 0.0
        if sources:
            score += min(len(sources) / 5.0, 0.5)  # até 0.5 por cobertura
        if interp.get("summary"):
            score += 0.3
        if interp.get("numeric_signals"):
            score += 0.2
        return round(min(score, 1.0), 2)

    async def act(
        self, task_id: str, output: dict[str, Any], ok: bool
    ) -> dict[str, Any]:
        self.memory.set_context(task_id, "decision", output)
        return output
