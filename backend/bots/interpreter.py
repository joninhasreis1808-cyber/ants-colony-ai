"""InterpreterBot — dá sentido ao material bruto.

Interpreta o texto e os números extraídos: resume, detecta equações e
sinaliza padrões (gráficos, tabelas). Na Fase 1 a interpretação é
heurística e determinística (sem LLM externo), o que a torna testável e
gratuita. A porta para um modelo de linguagem fica aberta na Fase 2.
"""
from __future__ import annotations

import re
from typing import Any

from backend.bots.base import Bot

_EQUATION_RE = re.compile(r"[\w.]+\s*[=<>]\s*[\w.]+")


class InterpreterBot(Bot):
    """Transforma dados brutos em insights legíveis."""

    name = "interpreter"
    skills = ("interpret_text", "interpret_equations", "interpret_charts")

    async def plan(
        self, task_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        extracted = self.memory.get_context(task_id, "extracted") or {}
        return {"extracted": extracted}

    async def do(self, task_id: str, plan: dict[str, Any]) -> dict[str, Any]:
        data = plan["extracted"]
        text: str = data.get("text", "")
        numbers: list[str] = data.get("numbers", [])
        equations = _EQUATION_RE.findall(text)
        summary = self._summarize(text)
        return {
            "summary": summary,
            "equations": equations,
            "numeric_signals": len(numbers),
            "has_chart_hint": "gráfico" in text.lower()
            or "chart" in text.lower(),
        }

    def _summarize(self, text: str, max_sentences: int = 3) -> str:
        """Resumo extrativo simples: primeiras frases significativas."""
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", text) if s.strip()]
        return ". ".join(sentences[:max_sentences])

    async def act(
        self, task_id: str, output: dict[str, Any], ok: bool
    ) -> dict[str, Any]:
        self.memory.set_context(task_id, "interpretation", output)
        return output
