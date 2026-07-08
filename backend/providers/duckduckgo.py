"""Provider DuckDuckGo — busca gratuita, sem API key.

Usa a Instant Answer API pública do DuckDuckGo. É o provider padrão e o
último fallback, pois está sempre disponível.
"""
from __future__ import annotations

from typing import Any

import httpx

from backend.core import SearchResult
from backend.providers.base import SearchProvider

_ENDPOINT = "https://api.duckduckgo.com/"


class DuckDuckGoProvider(SearchProvider):
    """Busca via DuckDuckGo Instant Answer API (gratuita)."""

    name = "duckduckgo"

    def __init__(self, timeout: float = 10.0) -> None:
        self._timeout = timeout

    @property
    def available(self) -> bool:
        return True  # sempre disponível: não requer credenciais

    async def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        params = {"q": query, "format": "json", "no_html": 1}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(_ENDPOINT, params=params)
            resp.raise_for_status()
            data = resp.json()
        return self._parse(data, limit)

    def _parse(self, data: dict[str, Any], limit: int) -> list[SearchResult]:
        results: list[SearchResult] = []
        # Abstract principal, quando existe.
        if data.get("AbstractText"):
            results.append(
                SearchResult(
                    title=data.get("Heading", query_fallback(data)),
                    url=data.get("AbstractURL", ""),
                    snippet=data["AbstractText"],
                    source=self.name,
                )
            )
        # Tópicos relacionados.
        for topic in data.get("RelatedTopics", []):
            if len(results) >= limit:
                break
            if "Text" in topic and "FirstURL" in topic:
                results.append(
                    SearchResult(
                        title=topic["Text"][:80],
                        url=topic["FirstURL"],
                        snippet=topic["Text"],
                        source=self.name,
                    )
                )
        return results[:limit]


def query_fallback(data: dict[str, Any]) -> str:
    """Título de reserva quando o Heading vem vazio."""
    return data.get("Heading") or "Resultado DuckDuckGo"
