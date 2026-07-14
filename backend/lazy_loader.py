"""Lazy loading de módulos (≤40 linhas, leve).

Adia o import de um módulo até o primeiro uso — reduz startup e RAM inicial.
(Fica na raiz de backend/ porque core.py é módulo, não pacote.)

    heavy = lazy("backend.perception.image_analyzer")
    heavy.ImageAnalyzer()   # só aqui o módulo é realmente importado
"""
from __future__ import annotations

import importlib
from typing import Any

_LOADED: set[str] = set()


class LazyModule:
    def __init__(self, name: str) -> None:
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_mod", None)

    def _load(self):
        mod = object.__getattribute__(self, "_mod")
        if mod is None:
            mod = importlib.import_module(object.__getattribute__(self, "_name"))
            object.__setattr__(self, "_mod", mod)
            _LOADED.add(object.__getattribute__(self, "_name"))
        return mod

    def __getattr__(self, attr: str) -> Any:
        return getattr(self._load(), attr)


def lazy(name: str) -> LazyModule:
    return LazyModule(name)


def loaded_modules() -> set[str]:
    return set(_LOADED)
