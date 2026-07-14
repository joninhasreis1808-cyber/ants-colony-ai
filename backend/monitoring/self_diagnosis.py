"""Autodiagnóstico (≤50 linhas, leve).

Verifica se cada módulo importa sem erro (imports quebrados, funções
faltantes). Pensado para rodar periodicamente (ex.: a cada 15 min).
"""
from __future__ import annotations

import importlib

CORE_MODULES = [
    "backend.events.event_bus",
    "backend.hivemind.hive",
    "backend.cognitive.orchestrator",
    "backend.memory.retriever",
    "backend.security.immune_system",
    "backend.api.main",
]


class SelfDiagnosis:
    def __init__(self, modules: list[str] | None = None) -> None:
        self.modules = list(modules if modules is not None else CORE_MODULES)

    def check(self) -> dict:
        results: dict[str, str] = {}
        for name in self.modules:
            try:
                importlib.import_module(name)
                results[name] = "ok"
            except Exception as exc:  # import quebrado / dependência ausente
                results[name] = f"broken: {type(exc).__name__}: {exc}"
        healthy = all(v == "ok" for v in results.values())
        broken = [m for m, v in results.items() if v != "ok"]
        return {"healthy": healthy, "modules": results, "broken": broken}
