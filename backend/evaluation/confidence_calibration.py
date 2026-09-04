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

    def reset(self) -> None:
        """Zera toda a calibração acumulada — isolamento entre testes/execuções."""
        self._count = [0.0] * self._bins
        self._hits = [0.0] * self._bins
        self._sum_pred = [0.0] * self._bins
        self._raw = [0] * self._bins

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


class RouteCalibrator:
    """Calibração por ROTA (Precisão Offline v1 · item 3), irmã de
    `ConfidenceCalibrator` — mesmo princípio (não corrige sem amostra
    suficiente), eixo diferente: aqui o que se mede é a taxa de acerto real
    de cada rota da Cartógrafa (`backend/cognition/cartographer.py`), não a
    faixa de confiança declarada.

    Os priors do catálogo da Cartógrafa (`success_probability` por rota)
    sempre foram constantes chutadas à mão, nunca recalibradas pelo
    resultado observado. Este calibrador fecha esse laço, reaproveitando o
    MESMO sinal de acerto em camadas (B3, `correctness_signal.py`) que já
    alimenta `ConfidenceCalibrator` — não inventa um sinal novo.

    Correção proporcional à evidência: com poucas amostras, o prior do
    catálogo quase não se move; a partir de `full_trust` amostras
    (ponderadas), a taxa observada domina. Sem amostra suficiente, o prior
    passa intacto — nunca uma correção fabricada.
    """

    def __init__(self, min_samples: int = 5, full_trust: int = 20) -> None:
        if min_samples < 1:
            raise ValueError("min_samples deve ser >= 1")
        if full_trust < min_samples:
            raise ValueError("full_trust deve ser >= min_samples")
        self._min = min_samples
        self._full_trust = full_trust
        self._hits: dict[str, float] = {}
        self._count: dict[str, float] = {}
        self._raw: dict[str, int] = {}

    def record(self, route: str, correct: bool, weight: float = 1.0) -> None:
        """Registra o desfecho real de uma rota, com o PESO do sinal (B3) —
        mesmo par (correct, weight) que `ConfidenceCalibrator.record` recebe."""
        if not route:
            return
        w = max(0.0, float(weight))
        self._count[route] = self._count.get(route, 0.0) + w
        self._raw[route] = self._raw.get(route, 0) + 1
        if correct:
            self._hits[route] = self._hits.get(route, 0.0) + w

    def reset(self) -> None:
        """Zera toda calibração acumulada — isolamento entre testes/execuções."""
        self._hits.clear()
        self._count.clear()
        self._raw.clear()

    def raw_count(self, route: str) -> int:
        return self._raw.get(route, 0)

    def observed_rate(self, route: str) -> float | None:
        """Taxa de acerto REAL observada para esta rota (ou None, sem amostra)."""
        if self._raw.get(route, 0) < self._min or self._count.get(route, 0) <= 0:
            return None
        return self._hits.get(route, 0.0) / self._count[route]

    def calibrate(self, route: str, prior: float) -> float:
        """Prior do catálogo puxado em direção à taxa real, proporcional ao
        tanto de evidência já visto. Sem amostra suficiente, devolve o prior
        intacto — nunca inventa uma correção."""
        rate = self.observed_rate(route)
        if rate is None:
            return prior
        w = min(1.0, self.raw_count(route) / self._full_trust)
        return round(prior * (1 - w) + rate * w, 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            route: {
                "raw": self._raw[route],
                "weight": round(self._count[route], 4),
                "observed_rate": self.observed_rate(route),
            }
            for route in self._raw
        }


_ROUTE_INSTANCE: "RouteCalibrator | None" = None


def get_route_calibrator() -> "RouteCalibrator":
    """Singleton de processo — calibração por rota, alimentada pelas missões reais."""
    global _ROUTE_INSTANCE
    if _ROUTE_INSTANCE is None:
        _ROUTE_INSTANCE = RouteCalibrator()
    return _ROUTE_INSTANCE
