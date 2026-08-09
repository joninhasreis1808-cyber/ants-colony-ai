"""Testes da busca web 9.0: extractor, verifier, learner, Wikipedia."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from backend.memory.answer_cache import get_answer_cache
from backend.providers.wikipedia import WikipediaProvider, _clean
from backend.search.extractor import extract_text
from backend.search.learner import STABLE_TTL, VOLATILE_TTL, is_volatile, validity_ttl
from backend.search.verifier import cross_check, jaccard


# ---- extractor (A.3) ----
def test_extractor_remove_scripts_e_limpa():
    html = ("<html><head><style>.x{}</style></head><body>"
            "<nav>menu</nav><script>evil()</script>"
            "<p>Conteúdo <b>real</b> da página.</p></body></html>")
    text = extract_text(html)
    assert "Conteúdo real da página." in text
    assert "evil" not in text and "menu" not in text


def test_extractor_vazio_nao_quebra():
    assert extract_text("") == ""
    assert extract_text(None) == ""


# ---- verifier (A.4) ----
def test_jaccard_e_cross_check():
    assert jaccard("gato preto corre", "gato preto dorme") > 0
    uma = cross_check(["console da microsoft lançado em 2005"])
    assert uma["confidence"] == 0.6 and uma["sources"] == 1
    duas = cross_check(["console microsoft 2005 videogame",
                        "videogame console microsoft 2005"])
    assert duas["sources"] == 2 and duas["confidence"] > 0.6
    assert cross_check([])["confidence"] < 0.2


# ---- learner (A.5) ----
def test_validity_volatil_vs_estavel():
    assert is_volatile("cotação do dólar hoje") is True
    assert is_volatile("o que é o algoritmo de Dijkstra") is False
    assert validity_ttl("cotação do dólar") == VOLATILE_TTL
    assert validity_ttl("o que é Xbox 360") == STABLE_TTL


def test_learner_grava_com_validade():
    from backend.search.learner import learn
    get_answer_cache().clear()
    ttl = learn("o que é Xbox 360", {"answer": "console", "source": "web_search"})
    assert ttl == STABLE_TTL
    assert get_answer_cache().get("o que é Xbox 360")["answer"] == "console"


# ---- Wikipedia provider (A.1) ----
def test_wikipedia_limpa_pergunta():
    assert _clean("o que é Xbox 360?") == "Xbox 360"
    assert _clean("quem foi Alan Turing?") == "Alan Turing"


def test_wikipedia_parse_com_mock():
    class FakeResp:
        def __init__(self, j): self._j = j
        def raise_for_status(self): pass
        def json(self): return self._j

    async def fake_get(url, params=None):
        if params and "opensearch" in str(params.get("action", "")):
            return FakeResp(["Xbox 360", ["Xbox 360"], ["Console Microsoft"],
                             ["https://pt.wikipedia.org/wiki/Xbox_360"]])
        return FakeResp({"extract": "O Xbox 360 é um console da Microsoft de 2005."})

    async def run():
        with patch.object(httpx.AsyncClient, "get", new=AsyncMock(side_effect=fake_get)):
            return await WikipediaProvider().search("o que é Xbox 360?")

    results = asyncio.run(run())
    assert results and results[0].source == "wikipedia"
    assert "console" in results[0].snippet.lower()
    assert results[0].url.endswith("Xbox_360")


def test_router_inclui_wikipedia():
    from backend.providers.router import ProviderRouter
    names = [p.name for p in ProviderRouter()._providers]
    assert "wikipedia" in names
    assert names[0] == "wikipedia"   # primeira fonte da cascata
