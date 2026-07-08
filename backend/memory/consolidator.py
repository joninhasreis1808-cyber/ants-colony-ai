"""Consolidação de memórias — fortalece o que importa.

Simula a consolidação sináptica: memórias acessadas, associadas ou de alta
atenção ficam mais fortes; as ociosas enfraquecem. A força combina
atenção, uso, associações e recência conforme a fórmula da especificação.
"""
from __future__ import annotations

import time

from backend.memory.distributed_store import DistributedStore
from backend.memory.reports import Report
from backend.memory.schemas import Memory

_DAY = 86400.0


class MemoryConsolidator:
    """Ajusta a força das memórias com base em uso e relevância."""

    def __init__(self, store: DistributedStore) -> None:
        self._store = store

    def reinforce(self, memory_id: str, boost: float = 0.1) -> None:
        """Fortalece uma memória (usada/acessada). Máximo 1.0."""
        if mem := self._store.get(memory_id):
            mem.strength = min(mem.strength + boost, 1.0)
            mem.access_count += 1
            mem.last_access = time.time()

    def weaken(self, memory_id: str, decay: float = 0.01) -> None:
        """Enfraquece uma memória. Mínimo 0.0."""
        if mem := self._store.get(memory_id):
            mem.strength = max(mem.strength - decay, 0.0)

    def get_memory_strength(self, memory_id: str) -> float:
        """Força atual de uma memória (0.0 se inexistente)."""
        mem = self._store.get(memory_id)
        return mem.strength if mem else 0.0

    def compute_strength(self, mem: Memory) -> float:
        """Fórmula de força combinando os quatro sinais."""
        access_norm = min(mem.access_count / 10.0, 1.0)
        assoc_norm = min(len(mem.associations) / 10.0, 1.0)
        days = (time.time() - mem.last_access) / _DAY
        recency = 1.0 / (1.0 + days)
        return round(
            mem.attention_score * 0.4
            + access_norm * 0.3
            + assoc_norm * 0.2
            + recency * 0.1,
            4,
        )

    def consolidate_daily(self) -> Report:
        """Rodada diária: reforça relevantes, enfraquece ociosas, poda."""
        report = Report(action="consolidate_daily")
        now = time.time()
        reinforced = weakened = removed = 0
        for mem in list(self._store.all_memories()):
            days_idle = (now - mem.last_access) / _DAY
            if (
                mem.attention_score > 0.7
                or len(mem.associations) > 5
                or days_idle < 1.0
            ):
                mem.strength = min(mem.strength + 0.1, 1.0)
                reinforced += 1
            elif days_idle >= 7.0:
                mem.strength = max(mem.strength - 0.1, 0.0)
                weakened += 1
            if mem.strength < 0.05:
                self._store.remove(mem.id)
                removed += 1
        report.counts = {
            "reinforced": reinforced, "weakened": weakened, "removed": removed,
        }
        return report

    def get_strongest_memories(self, limit: int = 20) -> list[Memory]:
        """Memórias mais fortes (strength > 0.7), ordenadas."""
        strong = [
            m for m in self._store.all_memories() if m.strength > 0.7
        ]
        strong.sort(key=lambda m: m.strength, reverse=True)
        return strong[:limit]
