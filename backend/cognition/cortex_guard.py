"""Guarda do córtex plugável (B6 · roteiro de maestria).

O risco real
------------
O córtex opcional (`reasoner.py`) já existia e era bem-feito: auto-detecta
backend, degrada para regras, não vaza chave. Mas em `deep_research` a síntese do
LLM virava a resposta assim:

    syn = await reasoner.synthesize(topic, evidence)
    base = syn or ". ".join(...)
    answer = composer.web(base, ...)          # confiança 0.9

Ou seja: **o texto do modelo externo saía como resposta da colônia, sem nenhuma
verificação e sem nenhum aviso.** O invariante I3 ("sem LLM externo como
cérebro") existia como convenção, e convenção não é freio.

O que este módulo faz
---------------------
Transforma a convenção em regra mecânica. O córtex pode **refinar**; não pode
**decidir** nem **acrescentar fato**:

  • **Números são o freio duro.** Toda grandeza que aparece na síntese e não
    aparece em nenhuma evidência é fato inventado. Uma síntese assim é
    **rejeitada**, e a colônia volta para a composição determinística.
  • **Cobertura lexical é o freio macio.** Uma síntese que quase não compartilha
    termos com as evidências está falando de outra coisa; isso derruba também.
  • **Uso declarado.** Toda vez que o córtex encosta na resposta, isso vira
    rótulo — qual backend, qual modelo, se passou na verificação.

O que NÃO é verificado, e fica dito
-----------------------------------
Números e vocabulário são checáveis sem modelo de linguagem. **Afirmação falsa
escrita com as palavras certas e sem número não é detectada.** A verificação
reduz o risco; não o elimina. Por isso o rótulo diz que houve LLM mesmo quando a
síntese passa: quem lê decide quanto confiar.

Determinístico, offline, stdlib.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

_MIN_COVERAGE = 0.15     # piso de termos compartilhados com as evidências
_STOP = {"de", "da", "do", "a", "o", "e", "em", "para", "com", "que", "os",
         "as", "um", "uma", "no", "na", "por", "ao", "se", "sao", "são",
         "the", "of", "is", "and", "to", "in"}


def _numbers(text: str) -> set[float]:
    out: set[float] = set()
    for bruto in re.findall(r"-?\d+(?:[.,]\d+)?", text or ""):
        try:
            out.add(float(bruto.replace(",", ".")))
        except ValueError:
            continue
    return out


def _terms(text: str) -> set[str]:
    brutos = re.findall(r"[a-zà-ÿ0-9]{4,}", (text or "").lower())
    return {t for t in brutos if t not in _STOP}


@dataclass
class SynthesisCheck:
    """O veredito sobre um texto que o córtex externo produziu."""

    accepted: bool
    reason: str
    invented_numbers: list[float] = field(default_factory=list)
    coverage: float = 0.0
    unverifiable: str = ("afirmação falsa escrita com as palavras certas e sem "
                         "número não é detectada sem modelo de linguagem - a "
                         "verificação reduz o risco, não o elimina")

    def to_dict(self) -> dict[str, Any]:
        return {"accepted": self.accepted, "reason": self.reason,
                "invented_numbers": list(self.invented_numbers),
                "coverage": self.coverage, "unverifiable": self.unverifiable}


def verify_synthesis(text: str, evidence: list[str]) -> SynthesisCheck:
    """A síntese do córtex ficou dentro das evidências que recebeu?"""
    corpo = (text or "").strip()
    if not corpo:
        return SynthesisCheck(False, "o córtex não devolveu texto")
    juntas = " ".join(str(e) for e in (evidence or []) if e)
    if not juntas.strip():
        return SynthesisCheck(
            False, "sem evidência para conferir a síntese - o córtex não pode "
                   "ser a única origem do que a colônia afirma")

    inventados = sorted(_numbers(corpo) - _numbers(juntas))
    if inventados:
        return SynthesisCheck(
            False,
            f"a síntese cita {inventados}, que não aparece em nenhuma evidência "
            f"- fato acrescentado pelo córtex, não refinamento",
            invented_numbers=inventados)

    tsin, tev = _terms(corpo), _terms(juntas)
    cobertura = round(len(tsin & tev) / len(tsin), 4) if tsin else 0.0
    if cobertura < _MIN_COVERAGE:
        return SynthesisCheck(
            False,
            f"só {cobertura:.0%} dos termos da síntese aparecem nas evidências "
            f"(piso {_MIN_COVERAGE:.0%}) - o córtex falou de outra coisa",
            coverage=cobertura)

    return SynthesisCheck(
        True, "a síntese ficou dentro das evidências (nenhum número novo)",
        coverage=cobertura)


@dataclass
class CortexUse:
    """O registro de que o córtex externo encostou nesta resposta."""

    used: bool
    backend: str = "rules"
    model: Optional[str] = None
    role: str = "refino"          # SEMPRE refino; o córtex nunca decide
    check: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {"used": self.used, "backend": self.backend, "model": self.model,
                "role": self.role, "check": self.check,
                "note": ("o córtex externo só refina texto; a decisão, a rota e "
                         "a proveniência continuam da colônia")}


def current_cortex() -> tuple[str, Optional[str]]:
    """Backend e modelo ativos agora, sem vazar chave. ('rules', None) se não há."""
    try:
        from backend.cognition.reasoner import posture
        p = posture()
        return str(p.get("backend", "rules")), p.get("model")  # type: ignore[return-value]
    except Exception:  # noqa: BLE001
        return "rules", None


def guarded_synthesis(text: Optional[str], evidence: list[str]
                      ) -> tuple[Optional[str], CortexUse]:
    """Aceita a síntese do córtex só se ela passar na verificação.

    Devolve `(texto_aprovado_ou_None, registro)`. Quando devolve None, quem
    chamou deve usar a composição determinística — e o registro explica por quê.
    """
    backend, model = current_cortex()
    if not text:
        return None, CortexUse(False, backend, model)
    check = verify_synthesis(text, evidence)
    uso = CortexUse(check.accepted, backend, model, check=check.to_dict())
    return (text if check.accepted else None), uso
