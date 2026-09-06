"""Meta-cognição: desempenho próprio da colônia (A5 · roteiro de maestria).

A colônia passa a saber **como ela mesma se sai**: tempo por rota, sucesso por
casta, e qual rota costuma funcionar para cada tipo de objetivo. A Rainha
consulta isso ANTES de montar a formação, via `Recruiter._formation_hint()`.

O QUE ESTA CONSULTA MUDA HOJE: NADA. Medido, não suposto.
------------------------------------------------------------------
Estava escrito aqui que a Rainha passava a recrutar "em vez de sempre na
mesma ordem fixa". A ordem é exatamente fixa, e por DOIS motivos
independentes — qualquer um deles sozinho já bastaria:

1. **O crédito é por MISSÃO, não por bot.** `record()` recebe
   `castes=[b.name for b in bots]` e carimba o MESMO desfecho em toda a
   formação. `success_rate()` responde "como foram as missões de que este
   bot participou", nunca "como este bot se saiu". Duas castas que sempre
   correm juntas empatam por construção. Medido em 6 missões reais:

       formation_hint() -> {'navigator': 0.8333, 'extractor': 0.8333,
                            'interpreter': 0.8333, 'decider': 0.8333,
                            'learner': 0.8333}
       valores distintos: [0.8333]

2. **Nenhuma casta divide estágio com outra.** O viés só desempata DENTRO
   de um estágio, e no elenco de hoje cada estágio tem um ocupante só
   (perceptor 0 · navigator 1 · extractor 2 · interpreter 3 · creator 4 ·
   decider 5 · learner 6). `rank()` sozinho já decide 100% da ordem, e a
   chave do viés nunca chega a ser comparada.

Isto NÃO é defeito a consertar às pressas — é o mesmo cenário declarado em
`test_contract_net_recruiter_b04.py` para o critério de custo: motor
pronto, elenco ainda sem disputa. O que era defeito é a frase que estava
aqui, afirmando um efeito que não existe. Ligar mais uma fonte de sinal
(ex.: `hivemind/reputation.py`, reputação por bot × domínio) seria a
terceira peça no mesmo transporte vazio: enquanto (2) valer, nenhuma
delas pode mudar a formação, e (1) precisaria ser resolvido antes de
qualquer uma valer alguma coisa.

`test_formation_hint_inerte.py` prende os dois fatos, para que a alegação
não volte sem a medição voltar junto.

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
        """Viés por casta (taxa de sucesso). Sem histórico → dicionário vazio.

        LEIA O CABEÇALHO DO MÓDULO ANTES DE CONFIAR NESTE NÚMERO. Ele diz
        "como foram as missões de que esta casta participou", não "como
        esta casta se saiu": `record()` credita a formação inteira com o
        desfecho da missão. Castas que sempre correm juntas recebem valores
        IDÊNTICOS, e o consumidor (`Recruiter._order`) usa isto como
        desempate — que empata. Separar o crédito por bot é o pré-requisito
        de qualquer uso real deste método."""
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
