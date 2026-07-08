"""PerceptorBot — leva a percepção da Fase 2 para dentro da colmeia.

Integra os módulos de percepção (texto, documento, equação) ao ciclo
P‑D‑C‑A dos bots. Lê o que o Extractor/Navigator deixaram no contexto e
enriquece com interpretação estruturada: intenção, entidades, equações.
Assim a Fase 2 não fica isolada — a colmeia passa a "entender" melhor.
"""
from __future__ import annotations

import re
from typing import Any

from backend.bots.base import Bot
from backend.perception.equation_solver import EquationSolver
from backend.perception.text_interpreter import TextInterpreter

# Captura um trecho matemático simples: termos, operadores, '=' e potências.
_EQ_SNIPPET = re.compile(r"[\w.^*/+\-() ]*[=][\w.^*/+\-() ]*")


class PerceptorBot(Bot):
    """Enriquece o contexto com interpretação de linguagem e matemática."""

    name = "perceptor"
    skills = ("perceive_text", "perceive_equation", "perceive_entities")

    def __init__(self, memory: Any, emit: Any = None) -> None:
        super().__init__(memory, emit)
        self._text = TextInterpreter()
        self._math = EquationSolver()

    async def plan(
        self, task_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        extracted = self.memory.get_context(task_id, "extracted") or {}
        goal = payload.get("goal", "")
        return {"text": extracted.get("text", "") or goal}

    async def do(self, task_id: str, plan: dict[str, Any]) -> dict[str, Any]:
        text = plan["text"]
        analysis = self._text.interpret(text)
        equations: list[dict[str, Any]] = []
        for snippet in self._math_snippets(text):
            try:
                sol = self._math.solve(self._math.parse(snippet))
                equations.append(sol.to_dict())
            except Exception:  # noqa: BLE001 - trecho não é equação válida
                continue
        return {
            "analysis": analysis.to_dict(),
            "equations": equations,
        }

    def _math_snippets(self, text: str) -> list[str]:
        """Isola trechos que parecem equações, sem as palavras ao redor.

        Remove palavras da linguagem natural, quebra o resto em fragmentos
        contíguos e devolve os que contêm um '=' com termos dos dois lados.
        """
        snippets: list[str] = []
        for raw in _EQ_SNIPPET.findall(text):
            if "=" not in raw:
                continue
            # Descarta palavras (2+ letras) e letras isoladas acentuadas.
            cleaned = re.sub(r"\b[A-Za-zÀ-ÿ]{2,}\b", " ", raw)
            cleaned = re.sub(r"[À-ÿ]", " ", cleaned)
            # Quebra onde houver 2+ espaços (lacunas deixadas pelas palavras).
            for frag in re.split(r"\s{2,}", cleaned):
                frag = frag.strip(" .,:;")
                if "=" in frag and all(
                    re.search(r"[\w)]", side)
                    for side in frag.split("=", 1)
                ):
                    snippets.append(frag)
        return snippets

    async def act(
        self, task_id: str, output: dict[str, Any], ok: bool
    ) -> dict[str, Any]:
        self.memory.set_context(task_id, "perception", output)
        return output
