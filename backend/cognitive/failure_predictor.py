"""Predição de falhas (≤50 linhas, leve).

Combina sinais pré-falha (CPU, latência, erros recentes) em uma
probabilidade. >60% dispara alerta com sugestão. Aprende com falhas reais.
"""
from __future__ import annotations


class FailurePredictor:
    def __init__(self) -> None:
        # pesos por sinal (normalizados 0-1 na entrada)
        self.weights = {"cpu": 0.35, "latency": 0.30, "recent_errors": 0.35}
        self.seen = 0
        self.failures = 0

    def probability(self, signals: dict) -> float:
        score = 0.0
        for key, w in self.weights.items():
            score += w * max(0.0, min(1.0, float(signals.get(key, 0))))
        return round(min(1.0, score), 3)

    def assess(self, signals: dict) -> dict:
        p = self.probability(signals)
        suggestion = None
        if p > 0.6:
            worst = max(self.weights, key=lambda k: signals.get(k, 0))
            suggestion = f"Reduzir carga: sinal dominante é '{worst}'. Considere adiar ou dividir a tarefa."
        return {"probability": p, "alert": p > 0.6, "suggestion": suggestion}

    def learn(self, signals: dict, failed: bool) -> None:
        self.seen += 1
        if failed:
            self.failures += 1
            for key in self.weights:
                if signals.get(key, 0) > 0.5:  # reforça sinais presentes na falha
                    self.weights[key] = min(0.6, self.weights[key] + 0.01)
