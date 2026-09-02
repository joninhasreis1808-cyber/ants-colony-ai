"""Sinais REAIS de acerto, em camadas declaradas (B3 · roteiro de maestria).

O problema
----------
Até aqui o calibrador era alimentado por **um único sinal fraco**: "a resposta
ficou ancorada e não escalou ao humano". Isso é auto-consistência — a colônia
conferindo a si mesma —, e eu declarei isso em todo incremento. Só que a colônia
já tem sinais melhores e não os usava.

As três camadas
---------------
Cada sinal declara **de onde vem** e **quanto vale**. Peso maior significa que
aquela observação move mais a calibração:

  forte (peso 3.0) · **confirmação humana** — o dono disse se a resposta serviu.
      É a única verdade externa que este projeto tem. Nada supera.
  médio (peso 2.0) · **verificação cruzada (B2)** — outra rota independente
      confirmou (ou contradisse). Não é verdade externa, mas é uma segunda
      testemunha, e isso vale mais que a colônia se auto-avaliar.
  fraco (peso 1.0) · **auto-consistência** — ancorado e sem escalar. O sinal que
      já existia. Continua valendo, mas agora sabe que é o mais fraco dos três.

A colônia usa **o melhor sinal disponível**, nunca a soma dos três: eles falam
sobre o mesmo desfecho, e somá-los seria contar a mesma missão três vezes.

Divergência é sinal NEGATIVO, não ausência de sinal: quando o B2 acusa
contradição numérica, isso é evidência de que a confiança declarada estava alta
demais — e a calibração precisa aprender com o erro, não só com o acerto.

Determinístico, stdlib, sem I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

WEIGHTS = {"forte": 3.0, "medio": 2.0, "fraco": 1.0}


@dataclass
class CorrectnessSignal:
    """O melhor sinal de acerto disponível para UMA missão."""

    correct: bool
    strength: str            # forte | medio | fraco
    basis: str               # a frase que explica de onde veio

    @property
    def weight(self) -> float:
        return WEIGHTS.get(self.strength, 1.0)

    def to_dict(self) -> dict[str, Any]:
        return {"correct": self.correct, "strength": self.strength,
                "basis": self.basis, "weight": self.weight}


def best_signal(*, human: Optional[bool] = None,
                cross_verdict: Optional[str] = None,
                grounded: bool = False,
                escalate_human: bool = False) -> CorrectnessSignal:
    """Escolhe o sinal mais forte que existir. Nunca soma camadas."""
    if human is not None:
        return CorrectnessSignal(
            bool(human), "forte",
            "confirmação humana explícita sobre esta missão")
    if cross_verdict == "confirmado":
        return CorrectnessSignal(
            True, "medio",
            "rota independente confirmou a resposta (B2)")
    if cross_verdict == "divergente":
        return CorrectnessSignal(
            False, "medio",
            "rota independente contradisse a resposta (B2) - a confiança "
            "declarada estava alta demais")
    return CorrectnessSignal(
        bool(grounded and not escalate_human), "fraco",
        "auto-consistência: ancorada e sem escalar ao humano - a colônia "
        "conferindo a si mesma, o mais fraco dos três sinais")
