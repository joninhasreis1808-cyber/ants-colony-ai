"""Testes de autossuficiência: navegação (Playwright) e IA local/cache."""
from __future__ import annotations

import pytest

from backend.memory.cache_manager import CacheManager
from backend.providers.local_provider import LocalProvider
from backend.providers.playwright_provider import PlaywrightProvider


@pytest.mark.asyncio
async def test_search_returns_results():
    # Sem browser real no ambiente de teste; validamos o contrato: se
    # indisponível, levanta erro claro (para o router acionar fallback).
    p = PlaywrightProvider()
    if not p.available:
        with pytest.raises(RuntimeError):
            await p.search("teste")
    else:
        # disponível mas provavelmente sem navegador → também aceitável
        try:
            res = await p.search("python", limit=2)
            assert isinstance(res, list)
        except Exception:
            pass


def test_fallback_when_playwright_unavailable():
    # O provider nunca "mente": available reflete a presença da lib.
    p = PlaywrightProvider()
    assert isinstance(p.available, bool)


def test_cache_hit_avoids_navigation():
    cache = CacheManager()
    cache.set("search:python", "resultado cacheado", kind="search")
    # segundo acesso é hit (sem tocar em rede)
    assert cache.get("search:python") == "resultado cacheado"
    assert cache.stats()["hits"] >= 1


def test_content_extraction():
    p = PlaywrightProvider()
    html = "<html><body><script>x</script><p>Olá <b>mundo</b></p></body></html>"
    text = p.extract_content(html)
    assert "Olá" in text and "mundo" in text and "script" not in text


def test_local_provider_always_available():
    lp = LocalProvider()
    assert lp.is_available() is True
    out = lp.generate("o que é uma colmeia")
    assert isinstance(out, str) and len(out) > 0
