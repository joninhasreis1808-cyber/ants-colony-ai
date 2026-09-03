"""Escada de busca + fontes sem chave (item 4 do Repertório da Colmeia).

O router de providers sempre teve fallback (§9.0), mas era um `for` cru sobre
uma lista — a ORDEM em si não vinha de nenhuma decisão declarada, e os dois
providers pagos (Tavily, Brave) ficavam ENTRE a Wikipedia e o DuckDuckGo, os
dois grátis. Sem chave configurada isso não mudava o resultado prático (os
pagos ficam indisponíveis e são pulados), mas a intenção do projeto — grátis
primeiro, pago como extra opt-in — não estava expressa em código nenhum.

Agora a ORDEM é decidida pelo `BudgetLadder` (fundamento 01): cada provider
declara `requires_key`, o custo vem disso (grátis = 0, pago = 1), e a escada
respeita a prioridade por posição. Prova aqui: mesmo com a chave paga
configurada (provider disponível), a fonte sem chave continua vindo primeiro
— "sem chave" é uma preferência de ORDEM, não só um substituto para quando
falta credencial.
"""
from __future__ import annotations

import pytest

from backend.providers.base import SearchProvider
from backend.providers.brave import BraveProvider
from backend.providers.duckduckgo import DuckDuckGoProvider
from backend.providers.router import ProviderRouter
from backend.providers.tavily import TavilyProvider
from backend.providers.wikipedia import WikipediaProvider


def test_wikipedia_e_duckduckgo_sao_sem_chave_tavily_e_brave_sao():
    assert WikipediaProvider.requires_key is False
    assert DuckDuckGoProvider.requires_key is False
    assert TavilyProvider.requires_key is True
    assert BraveProvider.requires_key is True


def test_ordem_padrao_poe_as_duas_fontes_sem_chave_antes_das_pagas():
    nomes = [p.name for p in ProviderRouter()._providers]
    assert nomes.index("wikipedia") < nomes.index("tavily")
    assert nomes.index("duckduckgo") < nomes.index("tavily")
    assert nomes.index("wikipedia") < nomes.index("brave")
    assert nomes.index("duckduckgo") < nomes.index("brave")


def test_router_usa_o_budget_ladder_para_decidir_a_ordem():
    """Não é só um `for` — a escada (fund. 01) é quem decide o plano."""
    router = ProviderRouter()
    passos = router._escada.steps_in_order()
    assert [s.cost for s in passos] == [0.0, 0.0, 1.0, 1.0], \
        "sem chave custa 0, chave paga custa mais — nessa ordem"


class _FakePaga(SearchProvider):
    """Provider pago, mas SEMPRE disponível (chave configurada de propósito)."""

    name = "paga_disponivel"
    requires_key = True

    @property
    def available(self) -> bool:
        return True

    async def search(self, query: str, limit: int = 5):
        return []


class _FakeGratis(SearchProvider):
    """Provider grátis, também disponível."""

    name = "gratis"
    requires_key = False

    @property
    def available(self) -> bool:
        return True

    async def search(self, query: str, limit: int = 5):
        return []


@pytest.mark.asyncio
async def test_mesmo_com_chave_configurada_a_fonte_sem_chave_e_tentada_primeiro():
    # A ordem de CONSTRUÇÃO já põe a paga primeiro de propósito — a prova real
    # é que a escada REORDENA pelo custo, não pela posição de entrada aqui.
    router = ProviderRouter([_FakePaga(), _FakeGratis()])
    _, tentativas = await router.search("qualquer coisa")
    assert tentativas[0] == "gratis", \
        "sem chave vem antes mesmo entrando depois na lista"
    assert tentativas == ["gratis", "paga_disponivel"]
