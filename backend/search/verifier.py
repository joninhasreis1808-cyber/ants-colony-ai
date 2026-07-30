"""Verificação cruzada de fontes (9.0 · A.4).

Cruza 2–3 fontes e mede a concordância (Jaccard sobre termos) para definir a
confiança de uma resposta da web. Alimenta o Critic/Verifier existentes: mais
fontes concordantes → maior confiança; fonte única → confiança moderada.
Determinístico, offline, sem dependências.
"""
from __future__ import annotations

import re
import unicodedata


def _tokens(text: str) -> set[str]:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return {t for t in re.findall(r"\w+", text) if len(t) > 3}


def jaccard(a: str, b: str) -> float:
    """Similaridade de Jaccard entre dois textos (0..1)."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def cross_check(snippets: list[str]) -> dict:
    """Mede concordância entre fontes e devolve confiança + nível.

    - 1 fonte → confiança 0.6 (sem cruzamento possível);
    - 2+ fontes → média das similaridades par-a-par escala a confiança
      (0.6 a 0.95), premiando concordância real.
    """
    clean = [s for s in (snippets or []) if s and s.strip()]
    n = len(clean)
    if n == 0:
        return {"confidence": 0.15, "agreement": 0.0, "sources": 0,
                "note": "sem fontes"}
    if n == 1:
        return {"confidence": 0.6, "agreement": 0.0, "sources": 1,
                "note": "fonte única — sem verificação cruzada"}
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    sims = [jaccard(clean[i], clean[j]) for i, j in pairs]
    agreement = sum(sims) / len(sims) if sims else 0.0
    confidence = round(min(0.95, 0.6 + agreement * 0.35), 3)
    return {"confidence": confidence, "agreement": round(agreement, 3),
            "sources": n,
            "note": f"{n} fontes cruzadas (concordância {agreement:.0%})"}
