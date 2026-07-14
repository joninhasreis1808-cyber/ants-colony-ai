"""Estigmergia avançada — feromônios multi-tipo (formigas).

Evolução do `stigmergy.py`: além de "sucesso", a colônia agora fala uma
linguagem química mais rica. Cada bot pode depositar quatro tipos de
feromônio numa trilha:

    EXPLORATION  "tem algo interessante aqui, venham ver"
    SUCCESS      "este caminho funcionou, reforcem"
    DANGER       "não passem por aqui, deu problema"
    RECRUITMENT  "preciso de ajuda nesta tarefa"

Feromônios evaporam com o tempo e se acumulam quando vários bots passam.
A melhor trilha é a de maior (SUCCESS − DANGER): a colônia é atraída ao
que funciona e repelida do que falha, sem nenhuma regra central.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum


class PheromoneType(str, Enum):
    """Os quatro sinais químicos da colônia."""

    EXPLORATION = "exploration"
    SUCCESS = "success"
    DANGER = "danger"
    RECRUITMENT = "recruitment"


@dataclass
class PheromoneTrail:
    """Estado de uma trilha: intensidade por tipo, com evaporação."""

    id: str
    intensities: dict[PheromoneType, float] = field(default_factory=dict)
    last_update: float = field(default_factory=time.time)

    def score(self) -> float:
        """Atratividade líquida: sucesso puxa, perigo repele."""
        return (self.intensities.get(PheromoneType.SUCCESS, 0.0)
                - self.intensities.get(PheromoneType.DANGER, 0.0))


class PheromoneField:
    """Campo de feromônios multi-tipo, thread-safe e com evaporação."""

    def __init__(
        self, decay: float = 0.05, max_intensity: float = 1.0,
        max_trails: int = 50,
    ) -> None:
        self._trails: dict[str, PheromoneTrail] = {}
        self._decay = decay
        self._max = max_intensity
        self._max_trails = max_trails
        self._lock = threading.RLock()

    def deposit(
        self, trail_id: str, ptype: PheromoneType, intensity: float = 0.2
    ) -> float:
        """Deposita feromônio de um tipo numa trilha (acumula)."""
        with self._lock:
            self._evaporate()
            trail = self._trails.get(trail_id) or PheromoneTrail(trail_id)
            cur = trail.intensities.get(ptype, 0.0)
            trail.intensities[ptype] = min(cur + intensity, self._max)
            trail.last_update = time.time()
            self._trails[trail_id] = trail
            self._evict_if_needed()
            return trail.intensities[ptype]

    def sense(self, trail_id: str) -> dict[str, float]:
        """Lê a intensidade de cada tipo numa trilha."""
        with self._lock:
            self._evaporate()
            trail = self._trails.get(trail_id)
            if not trail:
                return {p.value: 0.0 for p in PheromoneType}
            return {p.value: round(trail.intensities.get(p, 0.0), 4)
                    for p in PheromoneType}

    def get_best_trail(self) -> str | None:
        """Trilha de maior atratividade líquida (SUCCESS − DANGER)."""
        with self._lock:
            self._evaporate()
            if not self._trails:
                return None
            best = max(self._trails.values(), key=lambda t: t.score())
            return best.id if best.score() > 0 else None

    def evaporate_all(self) -> None:
        """Força uma rodada de evaporação (chamável por agendador)."""
        with self._lock:
            self._evaporate()

    def _evaporate(self) -> None:
        now = time.time()
        dead: list[str] = []
        for tid, trail in self._trails.items():
            dt = now - trail.last_update
            if dt <= 0:
                continue
            factor = max(0.0, 1.0 - self._decay * dt)
            for ptype in list(trail.intensities):
                trail.intensities[ptype] *= factor
                if trail.intensities[ptype] < 0.01:
                    del trail.intensities[ptype]
            trail.last_update = now
            if not trail.intensities:
                dead.append(tid)
        for tid in dead:
            self._trails.pop(tid, None)

    def _evict_if_needed(self) -> None:
        """LRU: mantém no máximo `max_trails` trilhas (as mais recentes)."""
        if len(self._trails) <= self._max_trails:
            return
        oldest = sorted(self._trails.values(), key=lambda t: t.last_update)
        for trail in oldest[: len(self._trails) - self._max_trails]:
            self._trails.pop(trail.id, None)

    def snapshot(self) -> dict[str, dict[str, float]]:
        """Panorama de todas as trilhas por tipo, para telemetria."""
        with self._lock:
            self._evaporate()
            return {tid: self.sense(tid) for tid in self._trails}
