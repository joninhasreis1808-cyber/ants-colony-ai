"""Calibração de confiança (9.19 · FASE 6) — o predito bate com o real?

O Relatório Mestre pede "Confidence calibration (predito × real)": de nada
adianta a colônia dizer "90% de certeza" se, quando diz isso, acerta só 60%.
Este módulo observa pares (confiança prevista, acertou?) e mede o desvio de
calibração (ECE — Expected Calibration Error), além de oferecer uma confiança
**corrigida** pela taxa de acerto REAL naquela faixa.

Honestidade acima de tudo: só corrige onde há dados suficientes; sem amostra, a
confiança passa intacta (nunca inventa uma correção). Puro stdlib, determinístico.
"""
from __future__ import annotations

from typing import Any


class ConfidenceCalibrator:
    """Aprende, das observações reais, quão confiável é cada faixa de confiança."""

    def __init__(self, bins: int = 10, min_samples: int = 5) -> None:
        if bins < 1:
            raise ValueError("bins deve ser >= 1")
        self._bins = bins
        self._min = min_samples
        self._count = [0] * bins
        self._hits = [0] * bins
        self._sum_pred = [0.0] * bins

    def _bin_of(self, confidence: float) -> int:
        c = 0.0 if confidence < 0 else 1.0 if confidence > 1 else float(confidence)
        idx = int(c * self._bins)
        return min(idx, self._bins - 1)   # 1.0 cai no último bin

    def record(self, predicted: float, correct: bool) -> None:
        """Registra uma previsão de confiança e se ela se confirmou."""
        b = self._bin_of(predicted)
        self._count[b] += 1
        self._sum_pred[b] += max(0.0, min(1.0, float(predicted)))
        if correct:
            self._hits[b] += 1

    @property
    def total(self) -> int:
        return sum(self._count)

    def observed_rate(self, confidence: float) -> float | None:
        """Taxa de acerto REAL observada na faixa desta confiança (ou None)."""
        b = self._bin_of(confidence)
        if self._count[b] < self._min:
            return None
        return self._hits[b] / self._count[b]

    def calibrate(self, raw_confidence: float) -> float:
        """Confiança corrigida pela realidade — ou a original, se faltam dados."""
        rate = self.observed_rate(raw_confidence)
        return rate if rate is not None else max(0.0, min(1.0, float(raw_confidence)))

    def ece(self) -> float:
        """Expected Calibration Error: desvio médio |previsto − observado|.

        0 = perfeitamente calibrado. Ponderado pela massa de amostras de cada bin.
        """
        total = self.total
        if total == 0:
            return 0.0
        err = 0.0
        for b in range(self._bins):
            if self._count[b] == 0:
                continue
            avg_pred = self._sum_pred[b] / self._count[b]
            observed = self._hits[b] / self._count[b]
            err += (self._count[b] / total) * abs(avg_pred - observed)
        return round(err, 6)

    def reliability(self) -> list[dict[str, Any]]:
        """Diagrama de confiabilidade por faixa (para auditoria/UI honesta)."""
        out = []
        for b in range(self._bins):
            if self._count[b] == 0:
                continue
            out.append({
                "bin": b,
                "predicted": round(self._sum_pred[b] / self._count[b], 4),
                "observed": round(self._hits[b] / self._count[b], 4),
                "count": self._count[b],
            })
        return out

    def to_dict(self) -> dict[str, Any]:
        return {"total": self.total, "ece": self.ece(),
                "reliability": self.reliability()}


_INSTANCE: "ConfidenceCalibrator | None" = None


def get_calibrator() -> "ConfidenceCalibrator":
    """Singleton de processo — o calibrador VIVO, alimentado pelas missões reais."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = ConfidenceCalibrator()
    return _INSTANCE
