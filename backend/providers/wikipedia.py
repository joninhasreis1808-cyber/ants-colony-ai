"""Provider Wikipedia — conhecimento de mundo, gratuito e sem chave (9.0 · A).

Faz um opensearch para achar a página e busca o resumo (REST summary) do topo,
devolvendo resultados normalizados. É a primeira fonte da cascata para "o que é
X" — autoritativa, gratuita e disponível em qualquer dispositivo com internet.
Degrada com honestidade: sem rede, levanta exceção e o router segue.
"""
from __future__ import annotations

import re
import unicodedata

import httpx

from backend.core import SearchResult
from backend.providers.base import SearchProvider

# Prefixos de pergunta que atrapalham a busca na Wikipedia.
_STRIP = re.compile(
    r"^\s*(o que (e|sao|é|são)|quem (e|é|foi)|qual (e|é|a|o)|me fale sobre|"
    r"defina|explique|significado de)\s+", re.I)


def _clean(query: str) -> str:
    q = _STRIP.sub("", query or "").strip().rstrip("?.!")
    return q or query


class WikipediaProvider(SearchProvider):
    """Busca conhecimento na Wikipedia (opensearch + REST summary)."""

    name = "wikipedia"

    def __init__(self, lang: str = "pt", timeout: float = 8.0) -> None:
        self._lang = lang
        self._timeout = timeout

    @property
    def available(self) -> bool:
        return True  # gratuita, sem credencial

    async def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        from backend.search.user_agents import honest
        headers = {"User-Agent": honest()}
        q = _clean(query)
        async with httpx.AsyncClient(timeout=self._timeout, headers=headers) as c:
            resp = await c.get(
                f"https://{self._lang}.wikipedia.org/w/api.php",
                params={"action": "opensearch", "search": q, "limit": limit,
                        "namespace": 0, "format": "json"})
            resp.raise_for_status()
            data = resp.json()
            titles, descs, urls = data[1], data[2], data[3]
            results = self._to_results(titles, descs, urls)
            if titles:
                results[0].snippet = await self._summary(c, titles[0]) or results[0].snippet
        return results

    async def _summary(self, client: httpx.AsyncClient, title: str) -> str:
        try:
            slug = title.strip().replace(" ", "_")
            r = await client.get(
                f"https://{self._lang}.wikipedia.org/api/rest_v1/page/summary/{slug}")
            r.raise_for_status()
            return (r.json().get("extract") or "").strip()[:2000]
        except Exception:  # noqa: BLE001 - sem resumo → usa a descrição
            return ""

    def _to_results(self, titles, descs, urls) -> list[SearchResult]:
        out: list[SearchResult] = []
        for i, title in enumerate(titles):
            snippet = descs[i] if i < len(descs) else ""
            url = urls[i] if i < len(urls) else ""
            out.append(SearchResult(title=title, url=url,
                                    snippet=snippet or title, source=self.name))
        return out
