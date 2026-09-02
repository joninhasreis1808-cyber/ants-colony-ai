"""Verificação cruzada entre rotas independentes (B2 · roteiro de maestria).

O que faltava
-------------
A colônia sempre teve várias rotas capazes de responder a mesma coisa — cálculo
exato, memória própria (B1), busca web, conhecimento inato, raciocínio. Mas
escolhia UMA pela ordem de autoridade e **descartava as outras caladas**. Se a
memória dizia 210 e a web dizia 180, a colônia entregava uma delas sem nunca
mencionar que havia divergência.

Aqui as rotas passam a se conferir. Duas coisas mudam:

  • **Concordância** de fontes independentes é registrada e sobe um pouco a
    confiança (no máximo +0.10, e nunca acima do teto da própria rota).
  • **Divergência** é EXPOSTA e derruba a confiança. A colônia nunca escolhe
    calada entre duas versões: ela mostra as duas e diz que discordam.

O que este detector realmente detecta
-------------------------------------
Com todas as letras, porque isto é um sinal declarado e não mágica:

  • **contradição numérica** — o sinal forte. As mesmas grandezas com valores
    diferentes (210 contra 180) são conflito objetivo.
  • **divergência lexical** — sinal fraco. Sobreposição de termos abaixo de um
    piso indica que as rotas falam de coisas diferentes, não necessariamente que
    se contradizem.

Ele **não** detecta contradição semântica ("sobe" contra "desce"). Isso exigiria
um modelo de linguagem, que este projeto não usa como cérebro. O que não é
detectado fica declarado como não detectado — nunca contado como concordância.

Regra de assimetria (a mesma do gate de ações): um sinal fraco pode **pedir
cautela** à vontade e só pode **conceder confiança** com parcimônia. Divergência
derruba forte; concordância sobe pouco.

Determinístico, offline, stdlib.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

# Rotas consideradas INDEPENDENTES entre si. Duas afirmações da mesma rota não
# se confirmam: é a mesma testemunha falando duas vezes.
INDEPENDENT = ("computation", "own_memory", "web_search", "knowledge_base",
               "reasoning", "seed_knowledge")

_AGREE_BONUS = 0.05      # por fonte independente que confirma
_MAX_BONUS = 0.10        # teto do bônus: concordância não é prova
_CONFLICT_CAP = 0.5      # teto da confiança quando há contradição numérica
_LEXICAL_FLOOR = 0.12    # abaixo disto, as rotas falam de assuntos diferentes
_STOP = {"de", "da", "do", "a", "o", "e", "em", "para", "com", "que", "os",
         "as", "um", "uma", "no", "na", "por", "e'", "ao", "the", "of", "is"}


@dataclass
class Claim:
    """O que UMA rota afirmou."""

    source: str
    text: str
    confidence: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {"source": self.source, "confidence": self.confidence,
                "excerpt": (self.text or "")[:160]}


@dataclass
class CrossCheck:
    """O resultado do confronto entre rotas."""

    verdict: str = "sem_base"        # confirmado | divergente | isolado | sem_base
    reason: str = ""
    claims: list[Claim] = field(default_factory=list)
    agreeing: list[str] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    adjustment: float = 0.0
    undetectable: str = ("contradição semântica não é detectada sem modelo de "
                         "linguagem - ausência de conflito aqui não é prova de "
                         "concordância")

    def to_dict(self) -> dict[str, Any]:
        return {"verdict": self.verdict, "reason": self.reason,
                "claims": [c.to_dict() for c in self.claims],
                "agreeing": list(self.agreeing), "conflicts": list(self.conflicts),
                "adjustment": self.adjustment, "undetectable": self.undetectable}


def _numbers(text: str) -> list[float]:
    """Grandezas citadas no texto (o sinal forte de contradição)."""
    out: list[float] = []
    for bruto in re.findall(r"-?\d+(?:[.,]\d+)?", text or ""):
        try:
            out.append(float(bruto.replace(",", ".")))
        except ValueError:
            continue
    return out


def _terms(text: str) -> set[str]:
    """Termos significativos, minúsculos, sem palavras vazias."""
    brutos = re.findall(r"[a-zà-ÿ0-9]{3,}", (text or "").lower())
    return {t for t in brutos if t not in _STOP}


def lexical_overlap(a: str, b: str) -> float:
    """Jaccard entre os termos. 0.0 quando um dos lados não tem termo."""
    ta, tb = _terms(a), _terms(b)
    if not ta or not tb:
        return 0.0
    return round(len(ta & tb) / len(ta | tb), 4)


def numeric_conflict(a: str, b: str) -> Optional[tuple[list[float], list[float]]]:
    """Contradição numérica entre os dois textos, se houver.

    Só acusa conflito quando **ambos** citam grandezas e **nenhuma** delas
    coincide. Se compartilham qualquer número, a colônia trata como a mesma
    grandeza dita duas vezes — e não inventa contradição.

    Devolve os conjuntos INTEIROS de cada lado, não um par escolhido. Apontar
    "4 contra 2" quando os textos citam [4] e [2, 5] seria fingir que a colônia
    sabe qual número responde à pergunta — e ela não sabe, porque isso exigiria
    interpretar a frase. Mostrar tudo é honesto; escolher um par é chute.
    """
    na, nb = _numbers(a), _numbers(b)
    if not na or not nb:
        return None
    if set(na) & set(nb):
        return None
    return sorted(set(na)), sorted(set(nb))


def cross_check(claims: list[Claim], base_confidence: Optional[float] = None
                ) -> CrossCheck:
    """Confronta o que cada rota independente afirmou."""
    validos = [c for c in claims
               if c.source in INDEPENDENT and (c.text or "").strip()]
    # Uma rota, uma voz: a mesma testemunha não se confirma.
    por_fonte: dict[str, Claim] = {}
    for c in validos:
        por_fonte.setdefault(c.source, c)
    unicos = list(por_fonte.values())

    r = CrossCheck(claims=unicos)
    if not unicos:
        r.verdict, r.reason = "sem_base", "nenhuma rota afirmou nada"
        return r
    if len(unicos) == 1:
        r.verdict = "isolado"
        r.reason = (f"só a rota '{unicos[0].source}' respondeu - não há segunda "
                    f"opinião para conferir")
        return r

    principal = unicos[0]
    for outro in unicos[1:]:
        conflito = numeric_conflict(principal.text, outro.text)
        if conflito is not None:
            r.conflicts.append({"a": principal.source, "b": outro.source,
                                "valores_a": conflito[0], "valores_b": conflito[1],
                                "tipo": "numérico"})
            continue
        if lexical_overlap(principal.text, outro.text) >= _LEXICAL_FLOOR:
            r.agreeing.append(outro.source)

    if r.conflicts:
        r.verdict = "divergente"
        c = r.conflicts[0]
        r.reason = (f"'{c['a']}' cita {c['valores_a']} e '{c['b']}' cita "
                    f"{c['valores_b']} - nenhum número em comum. A colônia "
                    f"mostra as duas versões em vez de escolher calada")
        r.adjustment = _conflict_adjustment(base_confidence)
        return r
    if r.agreeing:
        r.verdict = "confirmado"
        r.reason = (f"'{principal.source}' foi confirmada por "
                    f"{len(r.agreeing)} rota(s) independente(s): "
                    f"{', '.join(r.agreeing)}")
        r.adjustment = round(min(_MAX_BONUS, _AGREE_BONUS * len(r.agreeing)), 4)
        return r
    r.verdict = "isolado"
    r.reason = ("as rotas responderam sobre assuntos diferentes demais para se "
                "confirmarem - nenhuma confirma a outra")
    return r


def _conflict_adjustment(base: Optional[float]) -> float:
    """Quanto derrubar a confiança diante de contradição numérica."""
    if base is None:
        return 0.0
    return round(min(0.0, _CONFLICT_CAP - float(base)), 4)


def apply_adjustment(confidence: Optional[float], check: CrossCheck
                     ) -> Optional[float]:
    """Aplica o ajuste, sem nunca sair de [0, 1]. Sem confiança, nada muda."""
    if confidence is None or not isinstance(confidence, (int, float)):
        return confidence
    return round(max(0.0, min(1.0, float(confidence) + check.adjustment)), 4)
