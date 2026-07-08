"""Esquecimento adaptativo — otimização, não falha.

Enfraquece o irrelevante (decay por tipo), remove o muito fraco (poda,
poupando o bem-associado), resolve interferência entre memórias quase
idênticas e reporta a saúde geral do sistema.
"""
from __future__ import annotations

import numpy as np

from backend.memory.distributed_store import DistributedStore
from backend.memory.reports import Report
from backend.memory.schemas import MemoryType

# Decay por tipo, normalizado por chamada de apply_decay.
_DECAY = {
    MemoryType.WORKING: 0.1,
    MemoryType.EPISODIC: 0.01,
    MemoryType.SEMANTIC: 0.005,
    MemoryType.PROCEDURAL: 0.001,
    MemoryType.EMOTIONAL: 0.0003,  # 3x+ mais lento
}
_OVERLOAD = 10000


class AdaptiveForgetter:
    """Aplica decay, poda e resolução de interferência."""

    def __init__(self, store: DistributedStore) -> None:
        self._store = store

    def apply_decay(self) -> Report:
        """Reduz a força de todas as memórias conforme o tipo."""
        report = Report(action="apply_decay")
        for mem in self._store.all_memories():
            mem.strength = max(
                mem.strength - _DECAY.get(mem.mem_type, 0.01), 0.0
            )
        report.counts = {"decayed": self._store.count()}
        return report

    def prune_weak(self, threshold: float = 0.05) -> Report:
        """Remove memórias fracas, poupando as com >3 associações."""
        report = Report(action="prune_weak")
        removed = preserved = 0
        for mem in list(self._store.all_memories()):
            if mem.strength < threshold:
                if len(mem.associations) > 3:
                    preserved += 1
                    continue
                self._store.remove(mem.id)
                removed += 1
        report.counts = {"removed": removed, "preserved": preserved}
        return report

    def resolve_interference(self, threshold: float = 0.95) -> Report:
        """Funde/remove memórias quase idênticas (cosseno > threshold)."""
        report = Report(action="resolve_interference")
        embs = self._store.all_embeddings()
        ids = list(embs.keys())
        removed = 0
        gone: set[str] = set()
        for i, a in enumerate(ids):
            if a in gone:
                continue
            va = np.asarray(embs[a])
            for b in ids[i + 1:]:
                if b in gone:
                    continue
                if self._cosine(va, np.asarray(embs[b])) > threshold:
                    weaker = self._weaker(a, b)
                    self._store.remove(weaker)
                    gone.add(weaker)
                    removed += 1
        report.counts = {"merged_removed": removed}
        return report

    def get_memory_health(self) -> Report:
        """Panorama de saúde: totais, distribuição e risco de overload."""
        mems = self._store.all_memories()
        strong = sum(1 for m in mems if m.strength > 0.7)
        weak = sum(1 for m in mems if m.strength < 0.3)
        report = Report(action="memory_health")
        report.counts = {
            "total": len(mems), "strong": strong,
            "medium": len(mems) - strong - weak, "weak": weak,
        }
        report.extra = {
            "overload_risk": len(mems) > _OVERLOAD * 0.8,
            "capacity_used": round(len(mems) / _OVERLOAD, 4),
        }
        return report

    def _weaker(self, a: str, b: str) -> str:
        ma, mb = self._store.get(a), self._store.get(b)
        return a if (ma.strength if ma else 0) <= (mb.strength if mb else 0) \
            else b

    def _cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        return float(np.dot(a, b) / (na * nb)) if na and nb else 0.0
