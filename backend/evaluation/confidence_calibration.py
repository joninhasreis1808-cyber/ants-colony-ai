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
        self._count = [0.0] * bins       # massa PONDERADA de observações
        self._hits = [0.0] * bins
        self._sum_pred = [0.0] * bins
        self._raw = [0] * bins           # nº bruto de missões, para auditoria

    def _bin_of(self, confidence: float) -> int:
        c = 0.0 if confidence < 0 else 1.0 if confidence > 1 else float(confidence)
        idx = int(c * self._bins)
        return min(idx, self._bins - 1)   # 1.0 cai no último bin

    def record(self, predicted: float, correct: bool,
               weight: float = 1.0) -> None:
        """Registra uma previsão e se ela se confirmou, com o PESO do sinal.

        O peso vem da força do sinal de acerto (B3): confirmação humana move a
        calibração mais que auto-consistência, porque vale mais. Peso 1.0 é o
        padrão e reproduz exatamente o comportamento anterior.
        """
        b = self._bin_of(predicted)
        w = max(0.0, float(weight))
        self._count[b] += w
        self._raw[b] += 1
        self._sum_pred[b] += max(0.0, min(1.0, float(predicted))) * w
        if correct:
            self._hits[b] += w

    @property
    def total(self) -> int:
        """Missões observadas (contagem bruta, não a massa ponderada)."""
        return sum(self._raw)

    @property
    def mass(self) -> float:
        """Massa ponderada acumulada — o que de fato move a calibração."""
        return round(sum(self._count), 4)

    def observed_rate(self, confidence: float) -> float | None:
        """Taxa de acerto REAL observada na faixa desta confiança (ou None)."""
        b = self._bin_of(confidence)
        if self._raw[b] < self._min or self._count[b] <= 0:
            return None                  # amostra insuficiente -> não corrige
        return self._hits[b] / self._count[b]

    def calibrate(self, raw_confidence: float) -> float:
        """Confiança corrigida pela realidade — ou a original, se faltam dados."""
        rate = self.observed_rate(raw_confidence)
        return rate if rate is not None else max(0.0, min(1.0, float(raw_confidence)))

    def ece(self) -> float:
        """Expected Calibration Error: desvio médio |previsto − observado|.

        0 = perfeitamente calibrado. Ponderado pela massa de amostras de cada bin.
        """
        total = sum(self._count)
        if total <= 0:
            return 0.0
        err = 0.0
        for b in range(self._bins):
            if self._count[b] <= 0:
                continue
            avg_pred = self._sum_pred[b] / self._count[b]
            observed = self._hits[b] / self._count[b]
            err += (self._count[b] / total) * abs(avg_pred - observed)
        return round(err, 6)

    def reliability(self) -> list[dict[str, Any]]:
        """Diagrama de confiabilidade por faixa (para auditoria/UI honesta)."""
        out = []
        for b in range(self._bins):
            if self._count[b] <= 0:
                continue
            out.append({
                "bin": b,
                "predicted": round(self._sum_pred[b] / self._count[b], 4),
                "observed": round(self._hits[b] / self._count[b], 4),
                "count": self._raw[b],
                "weight": round(self._count[b], 4),
            })
        return out

    def to_dict(self) -> dict[str, Any]:
        return {"total": self.total, "mass": self.mass, "ece": self.ece(),
                "reliability": self.reliability(),
                "min_samples": self._min}


_INSTANCE: "ConfidenceCalibrator | None" = None


def get_calibrator() -> "ConfidenceCalibrator":
    """Singleton de processo — o calibrador VIVO, alimentado pelas missões reais."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = ConfidenceCalibrator()
    return _INSTANCE
