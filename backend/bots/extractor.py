"""ExtractorBot — extrai texto, tabelas e dados estruturados.

Lê as fontes publicadas pelo NavigatorBot no contexto compartilhado e
condensa os trechos em um material bruto para o InterpreterBot. Extração
de HTML completo/tabelas via parsing profundo virá na Fase 2; aqui já
consolidamos snippets e detectamos números/tabelas simples.
"""
from __future__ import annotations

import re
from typing import Any

from backend.bots.base import Bot

_NUMBER_RE = re.compile(r"-?\d[\d.,]*")


class ExtractorBot(Bot):
    """Consolida dados brutos a partir das fontes encontradas."""

    name = "extractor"
    skills = ("extract_text", "extract_tables", "extract_data")

    async def plan(
        self, task_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        sources = self.memory.get_context(task_id, "sources") or []
        return {"sources": sources}

    async def do(self, task_id: str, plan: dict[str, Any]) -> dict[str, Any]:
        texts: list[str] = []
        numbers: list[str] = []
        for src in plan["sources"]:
            snippet = src.get("snippet", "")
            if snippet:
                texts.append(snippet)
                numbers.extend(_NUMBER_RE.findall(snippet))
        return {
            "text": "\n".join(texts),
            "numbers": numbers,
            "chunks": len(texts),
        }

    async def check(self, task_id: str, output: dict[str, Any]) -> bool:
        return output.get("chunks", 0) > 0

    async def act(
        self, task_id: str, output: dict[str, Any], ok: bool
    ) -> dict[str, Any]:
        self.memory.set_context(task_id, "extracted", output)
        return output
