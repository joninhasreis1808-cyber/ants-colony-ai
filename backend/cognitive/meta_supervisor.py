"""Meta-cognição — o supervisor que observa a própria colônia.

O MetaSupervisor nunca resolve tarefas. Ele apenas OBSERVA o pipeline
cognitivo: quais camadas gastaram tempo, quais geraram erro, o custo de
cada decisão. Com isso, identifica gargalos e ajusta gradualmente os pesos
internos das camadas — a colônia aprende a pensar melhor sobre como pensa.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

_LAYERS = ("planner", "researcher", "hypothesizer", "critic",
           "verifier", "executor")


@dataclass
class LayerStat:
    calls: int = 0
    total_time: float = 0.0
    errors: int = 0

    @property
    def avg_time(self) -> float:
        return self.total_time / self.calls if self.calls else 0.0


class MetaSupervisor:
    """Observa métricas do pipeline e calibra os pesos das camadas."""

    def __init__(self) -> None:
        self._stats: dict[str, LayerStat] = defaultdict(LayerStat)
        self._weights: dict[str, float] = {layer: 1.0 for layer in _LAYERS}
        self._observations = 0

    def observe(self, pipeline_log: list[dict]) -> None:
        """Registra as métricas de uma execução do pipeline.

        Cada item do log: {"layer": str, "time": float, "error": bool}.
        """
        self._observations += 1
        for entry in pipeline_log:
            layer = entry.get("layer", "")
            if layer not in self._weights:
                continue
            st = self._stats[layer]
            st.calls += 1
            st.total_time += float(entry.get("time", 0.0))
            if entry.get("error"):
                st.errors += 1

    def analyze_patterns(self) -> dict:
        """Aponta o maior gargalo (tempo médio) e a camada mais falha."""
        if not self._stats:
            return {"bottleneck": None, "most_errors": None}
        bottleneck = max(self._stats.items(), key=lambda kv: kv[1].avg_time)
        most_errors = max(self._stats.items(), key=lambda kv: kv[1].errors)
        return {"bottleneck": bottleneck[0],
                "most_errors": most_errors[0] if most_errors[1].errors else
                None}

    def adjust_weights(self) -> dict[str, float]:
        """Ajusta pesos: penaliza gargalos e camadas que erram muito."""
        for layer, st in self._stats.items():
            if st.calls == 0:
                continue
            error_rate = st.errors / st.calls
            # Menos peso para quem erra muito; leve reforço para quem acerta.
            delta = -0.05 if error_rate > 0.3 else 0.03
            self._weights[layer] = round(
                min(1.5, max(0.3, self._weights[layer] + delta)), 3)
        return dict(self._weights)

    def get_weights(self) -> dict[str, float]:
        return dict(self._weights)

    def get_insights(self) -> dict:
        """Relatório legível das melhorias detectadas."""
        patterns = self.analyze_patterns()
        return {"observations": self._observations,
                "bottleneck": patterns["bottleneck"],
                "most_errors": patterns["most_errors"],
                "weights": self.get_weights()}
