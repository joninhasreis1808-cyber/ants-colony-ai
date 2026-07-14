"""Metabolismo digital — custo e benefício de cada tarefa.

Todo organismo tem metabolismo. A colônia também: cada tarefa tem um custo
(CPU, RAM, tempo, bateria) e um benefício esperado. Se o custo supera o
benefício ponderado pela prioridade, a tarefa é adiada ou recusada — energia
não se gasta à toa. Eficiência antes de força.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MetabolicCost:
    cpu: float
    ram: float
    time: float
    battery: float

    @property
    def total(self) -> float:
        """Custo agregado normalizado (0-1 aproximado)."""
        return round((self.cpu + self.ram + self.time + self.battery) / 4, 3)


class Metabolism:
    """Avalia se vale a pena gastar energia numa tarefa."""

    def __init__(self, energy_budget: float = 1.0) -> None:
        self._budget = energy_budget

    def calculate_cost(self, task: dict) -> MetabolicCost:
        """Estima o custo de uma tarefa a partir de sua descrição."""
        weight = float(task.get("weight", 0.3))
        return MetabolicCost(
            cpu=min(1.0, weight),
            ram=min(1.0, weight * 0.8),
            time=min(1.0, weight * 1.2),
            battery=min(1.0, weight * 0.5),
        )

    def calculate_benefit(self, task: dict) -> float:
        """Estima o benefício (0-1) de concluir a tarefa."""
        return max(0.0, min(1.0, float(task.get("benefit", 0.5))))

    def should_execute(
        self, cost: MetabolicCost, benefit: float, priority: float = 0.5
    ) -> bool:
        """Executa só se o benefício ponderado cobre o custo."""
        return benefit * max(0.1, priority) >= cost.total * self._budget

    def get_energy_budget(self) -> float:
        return self._budget

    def set_energy_budget(self, budget: float) -> None:
        """Ajusta o orçamento (ex.: bateria baixa reduz)."""
        self._budget = max(0.1, min(1.0, budget))
