"""Compactação de memórias antigas (≤40 linhas, leve).

Memórias com >30 dias e <3 acessos viram RESUMO (não são deletadas). O
resumo mantém tipo, data, palavras-chave e conclusão.
"""
from __future__ import annotations

import time

_DAY = 86400


class MemoryCompactor:
    def __init__(self, max_age_days: int = 30, min_access: int = 3) -> None:
        self.max_age = max_age_days * _DAY
        self.min_access = min_access

    def should_compact(self, mem: dict) -> bool:
        if mem.get("_compacted"):
            return False
        age = time.time() - mem.get("ts", time.time())
        return age > self.max_age and mem.get("accesses", 0) < self.min_access

    def compact(self, mem: dict) -> dict:
        text = str(mem.get("content", ""))
        keywords = sorted({w.lower() for w in text.split() if len(w) > 4})[:8]
        return {"_compacted": True, "type": mem.get("type", "geral"),
                "ts": mem.get("ts"), "keywords": keywords,
                "conclusion": text[:120], "accesses": mem.get("accesses", 0)}

    def run(self, memories: list[dict]) -> list[dict]:
        return [self.compact(m) if self.should_compact(m) else m for m in memories]
