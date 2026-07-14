"""Homeostase — a colônia se autorregula para não sobrecarregar.

Como um organismo mantém temperatura e pressão, a colônia observa CPU, RAM,
fila e erros, e ajusta quantos bots ficam ativos. Em situação crítica
(bateria/recursos no limite), hiberna para se preservar. Regras adaptativas,
não fixas — o objetivo é equilíbrio contínuo.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HealthStatus:
    healthy: bool
    recommended_bots: int
    actions: list


class Homeostasis:
    """Regula recursos da colônia conforme as métricas do sistema."""

    def __init__(self, max_bots: int = 15) -> None:
        self._max = max_bots
        self._metrics: dict[str, float] = {}

    def monitor(self, cpu: float, ram: float,
                queue: int = 0, errors: float = 0.0,
                battery: float = 100.0) -> dict:
        """Coleta um retrato das métricas atuais (0-100 para percentuais)."""
        self._metrics = {"cpu": cpu, "ram": ram, "queue": queue,
                         "errors": errors, "battery": battery}
        return dict(self._metrics)

    def regulate(self) -> HealthStatus:
        """Decide quantos bots manter e que ações tomar."""
        m = self._metrics
        bots = self._max
        actions: list[str] = []
        if m.get("cpu", 0) > 75:
            bots = max(2, bots // 2)
            actions.append("reduzir bots (CPU alta)")
        if m.get("ram", 0) > 80:
            actions.append("compactar memória (RAM alta)")
        if m.get("queue", 0) > 5:
            actions.append("criar operários temporários (fila grande)")
        if m.get("errors", 0) > 0.3:
            actions.append("modo conservador (erros subindo)")
        healthy = not actions
        return HealthStatus(healthy, bots, actions)

    def emergency_shutdown(self) -> bool:
        """Hiberna tudo se a situação for crítica (ex.: bateria baixa)."""
        m = self._metrics
        return m.get("battery", 100) < 15 or m.get("ram", 0) > 95

    def get_health_status(self) -> dict:
        status = self.regulate()
        return {"healthy": status.healthy,
                "recommended_bots": status.recommended_bots,
                "actions": status.actions,
                "emergency": self.emergency_shutdown()}
