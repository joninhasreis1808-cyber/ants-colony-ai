"""Contrato base para provedores de busca.

Todo provider (DuckDuckGo, Tavily, Brave...) implementa a mesma interface
`search`, devolvendo resultados normalizados. Isso permite ao router trocar
de provider de forma transparente.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from backend.core import SearchResult


class SearchProvider(ABC):
    """Interface comum de um provedor de busca."""

    name: str = "base"

    @property
    @abstractmethod
    def available(self) -> bool:
        """Se este provider está pronto para uso (ex.: tem API key)."""
        raise NotImplementedError

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Executa a busca e devolve resultados normalizados.

        Deve levantar exceção em caso de falha, para o router acionar o
        fallback para o próximo provider.
        """
        raise NotImplementedError
