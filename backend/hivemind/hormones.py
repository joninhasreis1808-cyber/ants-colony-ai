"""Sistema hormonal — reguladores globais de comportamento.

Além dos feromônios (locais), a colônia tem hormônios (globais): dopamina
reforça o que funcionou, cortisol aumenta a cautela após erros, ocitocina
fortalece a cooperação. Todos decaem com o tempo, voltando ao equilíbrio.
"""
from __future__ import annotations

from enum import Enum


class Hormone(str, Enum):
    DOPAMINE = "dopamine"      # recompensa: repetir o que deu certo
    CORTISOL = "cortisol"      # estresse: mais verificação, menos risco
    OXYTOCIN = "oxytocin"      # cooperação: compartilhar mais
    SEROTONIN = "serotonin"    # bem-estar: tarefa concluída com sucesso
    ADRENALINE = "adrenaline"  # urgência: acelera o processamento
    MELATONIN = "melatonin"    # fim do ciclo diurno: hora de consolidar


class HormoneSystem:
    """Mantém e degrada os níveis hormonais da colônia."""

    def __init__(self) -> None:
        self._levels: dict[str, float] = {h.value: 0.0 for h in Hormone}

    def release(self, hormone: Hormone, intensity: float = 0.2) -> float:
        """Libera um hormônio, elevando seu nível (teto 1.0)."""
        self._levels[hormone.value] = min(
            1.0, self._levels[hormone.value] + intensity)
        return self._levels[hormone.value]

    def get_hormone_level(self, hormone: Hormone) -> float:
        return self._levels[hormone.value]

    def decay_all(self, rate: float = 0.05) -> None:
        """Degradação natural: tudo tende ao equilíbrio."""
        for h in self._levels:
            self._levels[h] = round(max(0.0, self._levels[h] - rate), 3)

    def risk_appetite(self) -> float:
        """Apetite a risco: sobe com dopamina, cai com cortisol."""
        return round(0.5 + 0.5 * self._levels["dopamine"]
                     - 0.5 * self._levels["cortisol"], 3)

    def cooperation_bonus(self) -> float:
        """Quanto a ocitocina incentiva o compartilhamento."""
        return self._levels["oxytocin"]

    def well_being(self) -> float:
        """Bem-estar da colônia: serotonina alta, cortisol baixo."""
        return round(max(0.0, self._levels["serotonin"] - 0.5 * self._levels["cortisol"]), 3)

    def urgency_boost(self) -> float:
        """Aceleração por adrenalina (1.0 = normal, até 1.5)."""
        return round(1.0 + 0.5 * self._levels["adrenaline"], 3)

    def consolidation_ready(self) -> bool:
        """Melatonina alta indica que é hora de consolidar a memória."""
        return self._levels["melatonin"] >= 0.6
