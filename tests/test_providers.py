"""Testes dos providers e do router com fallback."""
from __future__ import annotations

import pytest

from backend.core import SearchResult
from backend.providers.brave import BraveProvider
from backend.providers.duckduckgo import DuckDuckGoProvider
from backend.providers.router import ProviderRouter
from backend.providers.tavily import TavilyProvider
from tests.conftest import FakeProvider


def test_duckduckgo_always_available():
    assert DuckDuckGoProvider().available is True


def test_tavily_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    assert TavilyProvider().available is False


def test_tavily_available_with_key():
    assert TavilyProvider(api_key="abc").available is True


def test_brave_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    assert BraveProvider().available is False


def test_router_active_providers_lists_available():
    router = ProviderRouter([FakeProvider(available=True)])
    assert router.active_providers == ["fake"]


@pytest.mark.asyncio
async def test_router_returns_results():
    router = ProviderRouter([FakeProvider()])
    results, attempts = await router.search("python", 3)
    assert results and attempts == ["fake"]


@pytest.mark.asyncio
async def test_router_skips_unavailable():
    router = ProviderRouter(
        [FakeProvider(available=False), FakeProvider(available=True)]
    )
    _, attempts = await router.search("q")
    assert attempts == ["fake"]  # apenas o disponível foi tentado


@pytest.mark.asyncio
async def test_router_fallback_on_failure():
    good = [SearchResult("t", "u", "s", "backup")]
    router = ProviderRouter(
        [FakeProvider(fail=True), FakeProvider(results=good)]
    )
    results, attempts = await router.search("q")
    assert len(attempts) == 2
    assert results[0].source == "backup"


@pytest.mark.asyncio
async def test_router_empty_when_all_fail():
    router = ProviderRouter([FakeProvider(fail=True)])
    results, attempts = await router.search("q")
    assert results == [] and attempts == ["fake"]
