"""Navegação sem API — busca via navegador real (Playwright).

Reduz a dependência de APIs de busca: quando o Playwright está instalado,
a colônia navega como um humano (user-agent real, pequenos atrasos) e
extrai os resultados diretamente da página. Se o Playwright não estiver
disponível, o provider se declara indisponível e o router segue para o
próximo (APIs configuradas) — degradação graciosa, nunca um erro fatal.

O carregamento do Playwright é *lazy*: só é importado quando realmente se
vai navegar, para não pesar no startup.
"""
from __future__ import annotations

import asyncio
import random

from backend.core import SearchResult

_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0 Safari/537.36",
]


class PlaywrightProvider:
    """Busca por navegação real; indisponível se o Playwright faltar."""

    name = "playwright"

    def __init__(self) -> None:
        self._checked = False
        self._has_playwright = False

    @property
    def available(self) -> bool:
        """Detecta o Playwright de forma lazy (só na primeira consulta)."""
        if not self._checked:
            self._checked = True
            try:
                import playwright  # noqa: F401
                self._has_playwright = True
            except ImportError:
                self._has_playwright = False
        return self._has_playwright

    async def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Navega no DuckDuckGo HTML e extrai os resultados."""
        if not self.available:
            raise RuntimeError("Playwright indisponível")
        return await self._search_duckduckgo(query, limit)

    async def _search_duckduckgo(
        self, query: str, limit: int
    ) -> list[SearchResult]:
        from playwright.async_api import async_playwright

        results: list[SearchResult] = []
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                page = await browser.new_page(
                    user_agent=random.choice(_UA_POOL)
                )
                await asyncio.sleep(random.uniform(0.2, 0.6))  # humano
                await page.goto(
                    f"https://html.duckduckgo.com/html/?q={query}",
                    timeout=15000,
                )
                nodes = await page.query_selector_all(".result")
                for node in nodes[:limit]:
                    results.append(await self._parse(node))
            finally:
                await browser.close()
        return [r for r in results if r is not None]

    async def _parse(self, node) -> SearchResult | None:
        try:
            title_el = await node.query_selector(".result__a")
            snippet_el = await node.query_selector(".result__snippet")
            if not title_el:
                return None
            title = (await title_el.inner_text()).strip()
            url = (await title_el.get_attribute("href")) or ""
            snippet = (
                await snippet_el.inner_text() if snippet_el else ""
            ).strip()
            return SearchResult(title=title, url=url, snippet=snippet,
                                source="playwright")
        except Exception:
            return None

    def extract_content(self, html: str) -> str:
        """Extrai texto limpo de um HTML (utilitário simples, sem libs)."""
        import re

        text = re.sub(r"<script.*?</script>", " ", html, flags=re.DOTALL)
        text = re.sub(r"<style.*?</style>", " ", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", text).strip()
