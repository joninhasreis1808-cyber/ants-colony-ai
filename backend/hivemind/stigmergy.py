"""Estigmergia — o raciocínio orgânico do enxame (abelhas e formigas).

Formigas não têm um chefe: elas se coordenam deixando *feromônios* no
ambiente. Trilhas usadas com sucesso ficam mais fortes; as ruins evaporam.
Abelhas decidem por quórum, com "danças" que recrutam mais forrageadoras
para as melhores fontes.

Este módulo dá à colmeia esse mesmo mecanismo: os bots depositam
feromônios em "trilhas" (tipos de tarefa × estratégia) conforme os
resultados. O roteamento futuro consulta essas trilhas — a colônia
aprende sozinha quais caminhos valem a pena, sem ninguém programar regras.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class Trail:
    """Uma trilha de feromônio: intensidade que evapora com o tempo."""

    key: str
    strength: float = 0.1
    deposits: int = 0
    last_update: float = field(default_factory=time.time)


class PheromoneField:
    """Campo de feromônios compartilhado por toda a colônia.

    Thread-safe: vários bots depositam/consultam em paralelo. As trilhas
    evaporam continuamente, então só o que é reforçado com frequência
    permanece forte — memória coletiva emergente, não programada.
    """

    def __init__(
        self, evaporation: float = 0.02, max_strength: float = 1.0
    ) -> None:
        self._trails: dict[str, Trail] = {}
        self._evaporation = evaporation
        self._max = max_strength
        self._lock = threading.RLock()

    def deposit(self, key: str, amount: float = 0.15) -> float:
        """Deposita feromônio numa trilha (sucesso reforça o caminho)."""
        with self._lock:
            self._evaporate()
            trail = self._trails.get(key) or Trail(key)
            trail.strength = min(trail.strength + amount, self._max)
            trail.deposits += 1
            trail.last_update = time.time()
            self._trails[key] = trail
            return trail.strength

    def sense(self, key: str) -> float:
        """Lê a intensidade atual de uma trilha (0.0 se inexistente)."""
        with self._lock:
            self._evaporate()
            trail = self._trails.get(key)
            return trail.strength if trail else 0.0

    def strongest(self, prefix: str = "", limit: int = 5) -> list[Trail]:
        """Trilhas mais fortes (opcionalmente sob um prefixo)."""
        with self._lock:
            self._evaporate()
            items = [
                t for k, t in self._trails.items() if k.startswith(prefix)
            ]
        items.sort(key=lambda t: t.strength, reverse=True)
        return items[:limit]

    def _evaporate(self) -> None:
        """Evapora todas as trilhas proporcionalmente ao tempo decorrido."""
        now = time.time()
        dead: list[str] = []
        for key, trail in self._trails.items():
            dt = now - trail.last_update
            if dt <= 0:
                continue
            # Evaporação exponencial suave (uma "meia-vida" natural).
            trail.strength *= max(0.0, 1.0 - self._evaporation * dt)
            trail.last_update = now
            if trail.strength < 0.01:
                dead.append(key)
        for key in dead:
            self._trails.pop(key, None)

    def snapshot(self) -> dict[str, float]:
        """Estado atual das trilhas, para telemetria/observação."""
        with self._lock:
            self._evaporate()
            return {k: round(t.strength, 4) for k, t in self._trails.items()}
