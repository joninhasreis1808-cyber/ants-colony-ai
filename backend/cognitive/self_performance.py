"""Meta-cognição: desempenho próprio da colônia (A5 · roteiro de maestria).

A colônia passa a saber **como ela mesma se sai**: tempo por rota, sucesso por
casta, e qual rota costuma funcionar para cada tipo de objetivo. A Rainha consulta
isso ANTES de montar a formação — em vez de recrutar sempre na mesma ordem fixa.

Princípio de segurança do incremento: **sem histórico, o viés é zero** — a
formação fica byte a byte igual à de hoje. O aprendizado só desempata; nunca
inverte o fluxo natural de trabalho (planejar → pesquisar → verificar → agir).

Puro stdlib, determinístico, memória de processo (dado, nunca código).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

_MAX_RECORDS = 500          # janela recente; a colônia esquece o antigo


@dataclass
class MissionRecord:
    """O desfecho de uma missão, do ponto de vista do desempenho próprio."""

    signature: str
    route: str
    castes: list[str] = field(default_factory=list)
    success: bool = False
    duration: float = 0.0


class SelfPerformance:
    """O que a colônia aprendeu sobre o próprio desempenho."""

    def __init__(self) -> None:
        self._log: list[MissionRecord] = []

    # -- escrita ------------------------------------------------------------
    def record(self, *, signature: str, route: str, castes: list[str],
               success: bool, duration: float = 0.0) -> None:
        self._log.append(MissionRecord(signature=signature or "", route=route or "",
                                       castes=list(castes or []),
                                       success=bool(success),
                                       duration=max(0.0, float(duration))))
        if len(self._log) > _MAX_RECORDS:
            del self._log[:-_MAX_RECORDS]

    @property
    def total(self) -> int:
        return len(self._log)

    # -- leitura ------------------------------------------------------------
    def success_rate(self, caste: str) -> Optional[float]:
        """Taxa de sucesso das missões em que esta casta participou."""
        rel = [r for r in self._log if caste in r.castes]
        if not rel:
            return None
        return round(sum(1 for r in rel if r.success) / len(rel), 4)

    def avg_time(self, route: str) -> Optional[float]:
        """Tempo médio das missões que usaram esta rota."""
        rel = [r for r in self._log if r.route == route]
        if not rel:
            return None
        return round(sum(r.duration for r in rel) / len(rel), 4)

    def success_of_route(self, route: str) -> Optional[float]:
        """Taxa de sucesso das missões que usaram esta rota. Sem missão -> None."""
        rel = [r for r in self._log if r.route == route]
        if not rel:
            return None
        return round(sum(1 for r in rel if r.success) / len(rel), 4)

    def best_route(self, signature: str) -> Optional[str]:
        """Rota com maior taxa de sucesso para este tipo de objetivo."""
        por_rota: dict[str, list[bool]] = {}
        for r in self._log:
            if r.signature == signature and r.route:
                por_rota.setdefault(r.route, []).append(r.success)
        if not por_rota:
            return None
        # maior taxa; empate → mais observações; empate → nome (determinístico)
        return max(por_rota.items(),
                   key=lambda kv: (sum(kv[1]) / len(kv[1]), len(kv[1]), kv[0]))[0]

    def formation_hint(self) -> dict[str, float]:
        """Viés por casta (taxa de sucesso). Sem histórico → dicionário vazio."""
        castes = {c for r in self._log for c in r.castes}
        out = {}
        for c in castes:
            taxa = self.success_rate(c)
            if taxa is not None:
                out[c] = taxa
        return out

    def to_dict(self) -> dict[str, Any]:
        return {"total": self.total,
                "formation_hint": self.formation_hint(),
                "routes": sorted({r.route for r in self._log if r.route})}


_INSTANCE: Optional[SelfPerformance] = None


def get_self_performance() -> SelfPerformance:
    """Singleton de processo — a memória de desempenho próprio da colônia."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = SelfPerformance()
    return _INSTANCE
