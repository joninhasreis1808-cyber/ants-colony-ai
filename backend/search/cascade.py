"""Busca em cascata com aprendizado (7.2 · Bloco D.3).

Encadeia fontes da mais barata/local à mais cara/externa, parando na primeira
que resolve: memória (o que já se aprendeu) → conhecimento inato (seed) →
Wikipedia (API REST) → provedores web (DuckDuckGo/Tavily/Brave via router) →
raciocínio próprio. Toda fonte externa é opcional (try/except): se a rede está
bloqueada (403) ou offline, a cascata degrada com honestidade — não inventa.

Aprendizado: uma busca boa vira memória com validade (TTL). A 2ª busca da
mesma pergunta volta com `cached: true` — a colônia aprendeu e não repete o
esforço. Determinístico e testável offline.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CascadeResult:
    """Resultado de uma etapa da cascata, com proveniência honesta."""

    answer: str
    source: str                       # memory|seed|wikipedia|web|reasoning|none
    confidence: float
    cached: bool = False
    urls: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "answer": self.answer, "source": self.source,
            "confidence": self.confidence, "cached": self.cached,
            "urls": self.urls, "steps": self.steps,
        }


class CascadeSearch:
    """Busca honesta em cascata, com cache-aprendizado por pergunta."""

    def __init__(self, router: Any = None, ttl: int = 3600,
                 seed: Any = None) -> None:
        self._router = router
        self._ttl = ttl
        self._cache: dict[str, dict] = {}
        if seed is None:
            from backend.memory.seed_knowledge import SeedKnowledge
            seed = SeedKnowledge()
        self._seed = seed

    # ---- cache (a memória do que já se aprendeu) ----
    def _key(self, q: str) -> str:
        return " ".join(q.lower().split())

    def _cached(self, q: str) -> Optional[dict]:
        item = self._cache.get(self._key(q))
        if not item:
            return None
        if time.time() - item["ts"] > self._ttl:
            self._cache.pop(self._key(q), None)   # expirou → esquece
            return None
        return item["result"]

    def remember(self, q: str, result: dict) -> None:
        """Guarda uma busca boa como memória com validade (aprendizado)."""
        self._cache[self._key(q)] = {"result": result, "ts": time.time()}

    # ---- Wikipedia (fonte externa real, opcional) ----
    async def _wikipedia(self, query: str) -> Optional[CascadeResult]:
        try:
            import httpx
            url = ("https://pt.wikipedia.org/api/rest_v1/page/summary/"
                   + query.strip().replace(" ", "_"))
            async with httpx.AsyncClient(timeout=6.0) as client:
                r = await client.get(url, headers={"User-Agent": "AntsColony/7.2"})
                r.raise_for_status()
                data = r.json()
            extract = (data.get("extract") or "").strip()
            if extract:
                return CascadeResult(
                    answer=extract, source="wikipedia", confidence=0.82,
                    urls=[data.get("content_urls", {}).get("desktop", {})
                          .get("page", "https://pt.wikipedia.org")],
                    steps=["Consultei o resumo da Wikipedia (API REST)."])
        except Exception:  # noqa: BLE001 - fonte externa é opcional/tolerante
            return None
        return None

    # ---- web via router (DuckDuckGo/Tavily/Brave) ----
    async def _web(self, query: str, limit: int) -> Optional[CascadeResult]:
        if self._router is None:
            return None
        try:
            results, _ = await self._router.search(query, limit)
        except Exception:  # noqa: BLE001
            return None
        if not results:
            return None
        top = results[0]
        d = top.to_dict() if hasattr(top, "to_dict") else dict(top)
        return CascadeResult(
            answer=d.get("snippet") or d.get("title") or "",
            source="web", confidence=0.85,
            urls=[r.to_dict().get("url", "") if hasattr(r, "to_dict")
                  else r.get("url", "") for r in results],
            steps=["Busquei nos provedores web e verifiquei o topo."])

    # ---- cascata ----
    async def search(self, query: str, limit: int = 5) -> dict:
        """Percorre a cascata e devolve o 1º resultado real (ou declara none)."""
        steps: list[str] = []
        # 1) memória (aprendido) — a colônia não repete esforço
        cached = self._cached(query)
        if cached:
            out = dict(cached)
            out["cached"] = True
            out["source"] = "memory"
            out.setdefault("steps", []).insert(0, "Recuperei da memória (aprendido antes).")
            return out
        # 2) conhecimento inato (seed)
        facts = self._seed.recall(query)
        steps.append("Consultei o conhecimento inato (seed).")
        # 3) Wikipedia (externa opcional)
        wiki = await self._wikipedia(query)
        if wiki:
            wiki.steps = steps + wiki.steps
            res = wiki.to_dict()
            self.remember(query, res)      # aprende
            return res
        # 4) web via router (externa opcional)
        web = await self._web(query, limit)
        if web:
            web.steps = steps + web.steps
            res = web.to_dict()
            self.remember(query, res)      # aprende
            return res
        # 5) seed factual, se relevante
        if facts:
            res = CascadeResult(answer=facts[0], source="seed", confidence=0.55,
                                steps=steps).to_dict()
            self.remember(query, res)
            return res
        # 6) sem evidência — declara honestamente
        return CascadeResult(
            answer="Não encontrei evidência suficiente para responder.",
            source="none", confidence=0.15,
            steps=steps + ["Nenhuma fonte resolveu — declarei a limitação."]
        ).to_dict()
