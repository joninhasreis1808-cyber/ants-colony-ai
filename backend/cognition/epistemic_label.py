"""Rótulo epistêmico ampliado (B4 · roteiro de maestria).

O problema
----------
A colônia já dizia muita coisa sobre o próprio conhecimento — `provenance`,
`fallback`, `cross_check`, `calibration`, `grounding`, `confidence` — mas
**espalhada em seis campos**. Para saber que tipo de conhecimento uma resposta é,
alguém precisava ler os seis e cruzá-los na cabeça. Na prática, ninguém lia: a
interface mostrava a confiança e pronto.

O que este módulo faz
---------------------
Reúne os sinais que JÁ existem num rótulo único, sem inventar nenhum. Uma
manchete e cinco eixos:

  **manchete** — que tipo de conhecimento é isto, numa palavra
  **origem**   — de onde veio
  **verificação** — outra rota independente conferiu? (B2)
  **calibração**  — o número foi corrigido pela realidade medida? (B3)
  **recência**    — se veio da memória, de quando é o registro
  **limites**     — o que a colônia sabe que NÃO checou

A manchete que faltava
----------------------
Antes havia rótulo para "ancorado" e para "sem base", mas **nenhum para
contestado**. Uma resposta com duas rotas se contradizendo era apresentada com a
mesma cara de uma resposta tranquila. Agora `contestado` existe e ganha da
maioria dos outros: divergência não é detalhe de rodapé.

Regra que vale para os cinco eixos: **eixo sem sinal diz "não medido"**, nunca
um valor plausível. Ausência de medição não é medição de ausência.

Determinístico, stdlib, sem I/O — deriva tudo do resultado já compilado.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# Manchetes possíveis, da mais forte à mais frágil.
HEADLINES = ("verificado", "fundamentado", "recordado", "inferido",
             "contestado", "sem_base")

_NAO_MEDIDO = "não medido"
# Fontes que contam como evidência dura (cálculo exato ou externa real).
_DURAS = ("computation", "web_search", "deep_research")
# Fontes que são registro/conhecimento guardado, não verificação.
_RECORDADAS = ("own_memory", "memory", "seed_knowledge", "knowledge_base")


@dataclass
class EpistemicLabel:
    """O que a colônia sabe sobre o próprio conhecimento, num lugar só."""

    headline: str
    origin: str
    verification: str
    calibration: str
    recency: str
    cortex: str = "não usado: a colônia compôs por regras"
    limits: list[str] = field(default_factory=list)
    confidence: Optional[float] = None
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"headline": self.headline, "origin": self.origin,
                "verification": self.verification, "calibration": self.calibration,
                "recency": self.recency, "cortex": self.cortex,
                "limits": list(self.limits),
                "confidence": self.confidence, "explanation": self.explanation}


def _verification(cross: Optional[dict]) -> tuple[str, Optional[str]]:
    """Eixo verificação + o limite que ele revela, se houver."""
    if not cross:
        return ("não conferido: nenhuma segunda rota respondeu",
                "nenhuma rota independente conferiu esta resposta")
    v = cross.get("verdict")
    if v == "confirmado":
        n = len(cross.get("agreeing") or [])
        return (f"confirmado por {n} rota(s) independente(s)", None)
    if v == "divergente":
        return ("CONTESTADO: rotas independentes se contradizem",
                cross.get("reason") or "há contradição entre as rotas")
    if v == "isolado":
        return (cross.get("reason") or "isolado",
                "nenhuma rota independente confirmou esta resposta")
    return ("não conferido", "nenhuma rota independente conferiu esta resposta")


def _calibration(cal: Optional[dict]) -> str:
    """Eixo calibração — o que o B3 fez (ou não fez) com o número."""
    if not cal:
        return f"{_NAO_MEDIDO}: a calibração não rodou nesta missão"
    if not cal.get("applied"):
        return f"não corrigido: {cal.get('reason', 'sem amostra')}"
    bruta, corrigida = cal.get("raw"), cal.get("calibrated")
    if isinstance(bruta, (int, float)) and isinstance(corrigida, (int, float)):
        if abs(float(corrigida) - float(bruta)) < 5e-5:
            return "corrigido: já batia com a realidade medida nesta faixa"
        return (f"corrigido pela realidade: {float(bruta):.0%} declarado, "
                f"{float(corrigida):.0%} observado de fato")
    return "corrigido pela realidade medida"


def _recency(grounded: Optional[dict], source: str) -> str:
    """Eixo recência — só faz sentido quando a resposta veio da memória."""
    if source not in _RECORDADAS:
        return "não se aplica: a resposta não veio de registro guardado"
    idade = (grounded or {}).get("age_days")
    if idade is None:
        return f"{_NAO_MEDIDO}: o registro não guardou data"
    if idade < 1:
        return "registro de hoje"
    if idade < 2:
        return "registro de ontem"
    return f"registro de {idade:.0f} dias atrás"


def _cortex(prov: dict) -> tuple[str, Optional[str]]:
    """Eixo córtex — um modelo externo encostou nesta resposta? (B6)

    Mesmo aprovada, a síntese de um LLM fica declarada: a verificação reduz o
    risco de fato inventado, não o elimina. Quem lê decide quanto confiar.
    """
    uso = prov.get("cortex")
    if not uso:
        return ("não usado: a colônia compôs por regras", None)
    if not uso.get("used"):
        motivo = ((uso.get("check") or {}).get("reason")
                  or "o córtex não devolveu texto aproveitável")
        return (f"consultado e REJEITADO: {motivo}", None)
    modelo = uso.get("model") or uso.get("backend")
    return (f"refinou o texto ({modelo}), verificado contra as evidências",
            (uso.get("check") or {}).get("unverifiable"))


def _headline(source: str, cross: Optional[dict], escalate: bool,
              grounded: Optional[dict]) -> tuple[str, str]:
    """A manchete e a frase que a explica."""
    if source in (None, "", "none") or escalate:
        return ("sem_base",
                "a colônia não reuniu base suficiente e prefere dizer isso a "
                "preencher o vazio")
    if (cross or {}).get("verdict") == "divergente":
        return ("contestado",
                "há resposta, mas rotas independentes se contradizem - a "
                "divergência é mostrada em vez de resolvida em silêncio")
    if (cross or {}).get("verdict") == "confirmado" and source in _DURAS:
        return ("verificado",
                "evidência dura confirmada por pelo menos uma rota independente")
    if source in _DURAS or (grounded or {}).get("sufficient"):
        return ("fundamentado",
                "ancorado em fonte real e citada, porém sem confirmação "
                "independente")
    if source in _RECORDADAS:
        return ("recordado",
                "vem do que a colônia guardou ou já sabia, sem verificação nova")
    return ("inferido",
            "raciocínio próprio sem fatos externos - o degrau mais frágil "
            "antes de escalar ao humano")


def build(result: dict[str, Any]) -> EpistemicLabel:
    """Monta o rótulo a partir do resultado JÁ compilado. Não inventa sinal."""
    prov = result.get("provenance") or {}
    source = prov.get("source") or "none"
    cross = result.get("cross_check")
    grounded = result.get("grounding")
    escalate = bool((result.get("fallback") or {}).get("escalate_human"))

    manchete, explicacao = _headline(source, cross, escalate, grounded)
    verificacao, limite_verif = _verification(cross)
    cortex, limite_cortex = _cortex(prov)
    limites: list[str] = []
    if limite_verif:
        limites.append(limite_verif)
    if limite_cortex:
        limites.append(limite_cortex)
    if cross and cross.get("undetectable"):
        limites.append(cross["undetectable"])
    for lacuna in (prov.get("gaps") or []):
        limites.append(str(lacuna))
    web = str(prov.get("web") or "")
    if "bloqueado" in web or "erro" in web:
        limites.append(f"a busca externa não estava disponível ({web})")
    fb = result.get("feedback") or {}
    if fb.get("honored") is False and fb.get("note"):
        limites.append(fb["note"])          # B5: proibição que não pôde ser honrada
    elif fb.get("blocked"):
        limites.append(f"rotas vetadas pelo dono nesta missão: "
                       f"{', '.join(fb['blocked'])}")

    return EpistemicLabel(
        headline=manchete, origin=source, verification=verificacao,
        calibration=_calibration(result.get("calibration")),
        recency=_recency(grounded, source), cortex=cortex,
        limits=limites, confidence=result.get("confidence"),
        explanation=explicacao)
