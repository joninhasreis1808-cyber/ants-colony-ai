"""Testes da busca em cascata com aprendizado (7.2 · Bloco D.3)."""
from __future__ import annotations

import pytest

from backend.providers.router import ProviderRouter
from backend.search.cascade import CascadeSearch
from tests.conftest import FakeProvider


@pytest.mark.asyncio
async def test_cascata_cai_para_seed_quando_web_vazia():
    cs = CascadeSearch(router=ProviderRouter([FakeProvider(results=[])]))
    r = await cs.search("o que são feromônios")
    assert r["source"] in ("seed", "none")
    assert r["cached"] is False
    assert r["steps"]


@pytest.mark.asyncio
async def test_segunda_busca_volta_cached_aprendeu():
    cs = CascadeSearch(router=ProviderRouter([FakeProvider(results=[])]))
    await cs.search("o que são feromônios")
    r2 = await cs.search("o que são feromônios")
    assert r2["cached"] is True
    assert r2["source"] == "memory"


@pytest.mark.asyncio
async def test_web_com_resultado_vira_fonte_web():
    cs = CascadeSearch(router=ProviderRouter([FakeProvider()]))
    r = await cs.search("linguagem python")
    assert r["source"] == "web"
    assert r["urls"]


@pytest.mark.asyncio
async def test_ttl_expira_e_esquece():
    cs = CascadeSearch(router=ProviderRouter([FakeProvider(results=[])]), ttl=0)
    await cs.search("estigmergia")
    r2 = await cs.search("estigmergia")
    assert r2["cached"] is False   # TTL 0 → não usa cache


@pytest.mark.asyncio
async def test_endpoint_search_aprende():
    from fastapi.testclient import TestClient
    from backend.api.main import app
    c = TestClient(app)
    q = {"query": "o que é uma colônia de formigas"}
    r1 = c.post("/hive/search", json=q).json()
    r2 = c.post("/hive/search", json=q).json()
    assert r1["cached"] is False
    assert r2["cached"] is True
