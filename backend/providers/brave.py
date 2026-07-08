"""Provider Brave Search (requer API key).

Ativa-se apenas se BRAVE_API_KEY estiver definida.
"""
from __future__ import annotations

import os
from typing import Optional

import httpx

from backend.core import SearchResult
from backend.providers.base import SearchProvider

_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"


class BraveProvider(SearchProvider):
    """Busca via API Brave Search."""

    name = "brave"

    def __init__(
        self, api_key: Optional[str] = None, timeout: float = 15.0
    ) -> None:
        self._api_key = api_key or os.getenv("BRAVE_API_KEY")
        self._timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    async def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self._api_key or "",
        }
        params = {"q": query, "count": limit}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(_ENDPOINT, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
        web = data.get("web", {}).get("results", [])
        return [
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("description", ""),
                source=self.name,
            )
            for item in web[:limit]
        ]
