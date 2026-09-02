"""Conselho REAL + teoria da mente leve (A7 · roteiro de maestria).

A lacuna
--------
`QueenCouncil` existia, mas era uma casca: `deliberate()` recebia os votos
prontos de fora. Os membros nunca avaliavam nada — o conselho registrava uma
votação que alguém já tinha feito. Aqui os conselheiros passam a **formar a
própria opinião** a partir de sinais reais, e a **modelar a mente uns dos
outros**.

Conselho real
-------------
Cada conselheiro tem uma BASE declarada — o único sinal que ele sabe ler:

  pesquisador  -> nº de fontes          crítico     -> nº de contradições
  verificador  -> ancoragem             simulador   -> score simulado (A1)
  especialista -> apoio causal (A2)     planejador  -> sucesso passado (A5)

Sem dado na sua base, o conselheiro **se abstém**. Não chuta, não vota por
educação: declara que não tem como opinar (I8).

Teoria da mente leve
--------------------
Cada conselheiro **só enxerga os VALORES da própria base** — o crítico conta
contradições, ele não vê a contagem de fontes do pesquisador. O que ele vê dos
outros é apenas se *existe* dado na base deles, nunca quanto.

Com isso ele prevê assim, e a premissa está declarada porque é uma premissa:
**"um colega racional com dado bom chega onde eu cheguei"**. Então prevê a
própria escolha para quem tem dado, e abstenção para quem não tem. É uma teoria
da mente *leve* — um modelo do outro, não uma simulação dele.

A previsão erra de verdade, e é aí que está o valor:

• **muita surpresa** = os conselheiros olham para coisas diferentes e não se
  espelham; se ainda assim convergirem, a concordância vale muito;
• **pouca surpresa** = eles se espelham, e a concordância informa menos.

Independência e fragilidade
---------------------------
O conselho conta quantas BASES DISTINTAS sustentaram o vencedor. Uma decisão
apoiada numa base só — inclusive a "unanimidade de um conselheiro só" — é
marcada como **frágil**, por mais unânime que pareça. Um conselho que não sabe
distinguir convergência de redundância acha que é sábio quando é só repetitivo.

Determinístico, stdlib, sem I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

# Nome da base de cada conselheiro = o campo da evidência que ele sabe ler.
BASES: dict[str, str] = {
    "pesquisador": "sources",
    "critico": "contradictions",
    "verificador": "grounded",
    "simulador": "simulated_score",
    "especialista": "causal_support",
    "planejador": "past_success",
}
MEMBERS: tuple[str, ...] = tuple(BASES)

_QUORUM = 0.7


@dataclass
class OptionEvidence:
    """Os sinais REAIS de uma opção. Campo ausente = sinal inexistente."""

    option: str
    sources: Optional[int] = None
    contradictions: Optional[int] = None
    grounded: Optional[bool] = None
    simulated_score: Optional[float] = None
    causal_support: Optional[int] = None
    past_success: Optional[float] = None

    def get(self, campo: str) -> Any:
        return getattr(self, campo, None)

    def to_dict(self) -> dict[str, Any]:
        return {"option": self.option, "sources": self.sources,
                "contradictions": self.contradictions, "grounded": self.grounded,
                "simulated_score": self.simulated_score,
                "causal_support": self.causal_support,
                "past_success": self.past_success}


def _tem_dado(evidencias: list[OptionEvidence], campo: str) -> bool:
    """Existe algum dado nesta base? (o que um conselheiro vê dos outros)"""
    return any(e.get(campo) is not None for e in evidencias)


def _melhor(evidencias: list[OptionEvidence], campo: str,
            maior_vence: bool) -> Optional[tuple[str, float]]:
    """Melhor opção pelo campo. None quando não há como distinguir."""
    pares = [(e.option, e.get(campo)) for e in evidencias
             if e.get(campo) is not None]
    if not pares:
        return None                      # sem dado nenhum -> abstém
    valores = [float(v) for _, v in pares]
    if len(set(valores)) == 1:
        return None                      # todos iguais -> nada a distinguir
    pares.sort(key=lambda kv: (-float(kv[1]) if maior_vence else float(kv[1]),
                               kv[0]))
    melhor_v, segundo_v = float(pares[0][1]), float(pares[1][1])
    faixa = max(valores) - min(valores)
    margem = abs(melhor_v - segundo_v) / faixa if faixa else 0.0
    return pares[0][0], round(min(1.0, 0.5 + margem / 2.0), 4)


# Regra publicada de cada conselheiro (é ELA que os outros rodam ao prever).
RULES: dict[str, Callable[[list[OptionEvidence]], Optional[tuple[str, float]]]] = {
    "pesquisador": lambda ev: _melhor(ev, "sources", True),
    "critico": lambda ev: _melhor(ev, "contradictions", False),
    "verificador": lambda ev: _melhor(ev, "grounded", True),
    "simulador": lambda ev: _melhor(ev, "simulated_score", True),
    "especialista": lambda ev: _melhor(ev, "causal_support", True),
    "planejador": lambda ev: _melhor(ev, "past_success", True),
}


@dataclass
class Opinion:
    """A opinião de um conselheiro, com a base que a sustentou."""

    member: str
    choice: Optional[str]                 # None = abstenção declarada
    confidence: float = 0.0
    basis: Optional[str] = None
    reason: str = ""
    predictions: dict[str, Optional[str]] = field(default_factory=dict)

    @property
    def abstained(self) -> bool:
        return self.choice is None

    def to_dict(self) -> dict[str, Any]:
        return {"member": self.member, "choice": self.choice,
                "confidence": self.confidence, "basis": self.basis,
                "reason": self.reason, "abstained": self.abstained,
                "predictions": dict(self.predictions)}


@dataclass
class CouncilVerdict:
    """O que o conselho decidiu — e o quanto essa decisão vale."""

    question: str
    options: list[str]
    opinions: list[Opinion] = field(default_factory=list)
    winner: Optional[str] = None
    reached: bool = False
    consensus: str = "sem quorum"
    fragile: bool = False
    fragile_reason: str = ""
    independence: int = 0            # bases distintas que sustentam o vencedor
    tom_accuracy: Optional[float] = None
    surprises: list[str] = field(default_factory=list)

    @property
    def abstentions(self) -> list[str]:
        return [o.member for o in self.opinions if o.abstained]

    def to_dict(self) -> dict[str, Any]:
        return {"question": self.question, "options": list(self.options),
                "opinions": [o.to_dict() for o in self.opinions],
                "winner": self.winner, "reached": self.reached,
                "consensus": self.consensus, "fragile": self.fragile,
                "fragile_reason": self.fragile_reason,
                "independence": self.independence,
                "abstentions": self.abstentions,
                "theory_of_mind": {"accuracy": self.tom_accuracy,
                                   "surprises": list(self.surprises)}}


class RealCouncil:
    """Os conselheiros opinam de verdade — e modelam a mente uns dos outros."""

    def __init__(self, members: tuple[str, ...] = MEMBERS,
                 quorum: float = _QUORUM) -> None:
        self._members = tuple(m for m in members if m in RULES)
        self._quorum = quorum

    # -- 1. cada conselheiro forma a própria opinião ------------------------
    def _opinar(self, membro: str, ev: list[OptionEvidence]) -> Opinion:
        base = BASES[membro]
        r = RULES[membro](ev)
        if r is None:
            return Opinion(member=membro, choice=None, basis=base,
                           reason=f"sem sinal utilizável em '{base}' - abstenção")
        escolha, conf = r
        return Opinion(member=membro, choice=escolha, confidence=conf, basis=base,
                       reason=f"melhor '{base}' entre as opções")

    # -- 2. teoria da mente: modelar o outro com informação incompleta -----
    def _prever(self, membro: str, minha_escolha: Optional[str],
                ev: list[OptionEvidence]) -> dict[str, Optional[str]]:
        """O que ESTE conselheiro acha que cada outro vai votar.

        Ele enxerga os VALORES só da própria base; dos outros, enxerga apenas se
        existe dado. A premissa do modelo — declarada, porque é premissa — é que
        **um colega racional com dado bom chega onde ele chegou**. Logo: prevê a
        própria escolha para quem tem dado, e abstenção para quem não tem.

        A premissa falha o tempo todo (o colega discorda, ou se abstém porque o
        dado dele não distingue nada) — e é justamente esse erro que o conselho
        mede.

        Caso digno de nota: quem se absteve tem `minha_escolha = None` e portanto
        prevê que **ninguém** decidiu — modela o colega à própria imagem. Erra
        sempre que alguém conseguiu decidir, e essa surpresa é justamente o
        sinal de que aquele conselheiro estava cego, não o conselho inteiro.
        """
        out: dict[str, Optional[str]] = {}
        for outro in self._members:
            if outro == membro:
                continue
            out[outro] = minha_escolha if _tem_dado(ev, BASES[outro]) else None
        return out

    # -- 3. o conselho se reúne --------------------------------------------
    def convene(self, question: str, evidence: list[OptionEvidence]) -> CouncilVerdict:
        opcoes = [e.option for e in evidence]
        v = CouncilVerdict(question=question, options=opcoes)
        for m in self._members:
            op = self._opinar(m, evidence)
            op.predictions = self._prever(m, op.choice, evidence)
            v.opinions.append(op)

        votos = [o.choice for o in v.opinions if not o.abstained]
        if votos:
            contagem: dict[str, int] = {}
            for c in votos:
                contagem[c] = contagem.get(c, 0) + 1
            lider, n = max(contagem.items(), key=lambda kv: (kv[1], kv[0]))
            razao = n / len(votos)
            v.reached = razao >= self._quorum
            v.winner = lider if v.reached else None
            v.consensus = ("unânime" if n == len(votos)
                           else "maioria" if v.reached else "sem quorum")

        self._avaliar_tom(v)
        self._detectar_ponto_cego(v)
        return v

    # -- 4. o conselho se audita -------------------------------------------
    @staticmethod
    def _avaliar_tom(v: CouncilVerdict) -> None:
        """Compara previsão com realidade — e registra cada surpresa."""
        real = {o.member: o.choice for o in v.opinions}
        acertos = total = 0
        for o in v.opinions:
            for outro, previsto in o.predictions.items():
                if outro not in real:
                    continue
                total += 1
                if previsto == real[outro]:
                    acertos += 1
                else:
                    v.surprises.append(
                        f"{o.member} previu que {outro} votaria "
                        f"'{previsto or 'abstenção'}', mas foi "
                        f"'{real[outro] or 'abstenção'}'")
        v.tom_accuracy = round(acertos / total, 4) if total else None

    @staticmethod
    def _detectar_ponto_cego(v: CouncilVerdict) -> None:
        """Conta as bases independentes e marca a decisão apoiada numa base só."""
        vencedores = [o for o in v.opinions
                      if not o.abstained and o.choice == v.winner]
        v.independence = len({o.basis for o in vencedores})
        if not v.reached or v.independence > 1:
            return
        base = vencedores[0].basis if vencedores else "nenhuma"
        v.fragile = True
        v.fragile_reason = (
            f"decisão apoiada em uma base só ('{base}'): pode parecer unânime, "
            f"mas nenhum outro sinal independente a confirmou")


_INSTANCE: Optional[RealCouncil] = None


def get_real_council() -> RealCouncil:
    """Singleton de processo do conselho real."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = RealCouncil()
    return _INSTANCE
