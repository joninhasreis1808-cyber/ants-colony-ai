"""Provider Tavily — busca otimizada para IA (requer API key).

Ativa-se apenas se a variável de ambiente TAVILY_API_KEY estiver definida
(ou se a key for passada no construtor).
"""
from __future__ import annotations

import os
from typing import Optional

import httpx

from backend.core import SearchResult
from backend.providers.base import SearchProvider

_ENDPOINT = "https://api.tavily.com/search"


class TavilyProvider(SearchProvider):
    """Busca via API Tavily."""

    name = "tavily"

    def __init__(
        self, api_key: Optional[str] = None, timeout: float = 15.0
    ) -> None:
        self._api_key = api_key or os.getenv("TAVILY_API_KEY")
        self._timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    async def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        payload = {
            "api_key": self._api_key,
            "query": query,
            "max_results": limit,
            "search_depth": "basic",
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(_ENDPOINT, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return [
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                source=self.name,
            )
            for item in data.get("results", [])[:limit]
        ]
