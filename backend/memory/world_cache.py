"""Cache mundial — se já pesquisou, não pesquisa de novo.

Camada fina sobre o CacheManager, dedicada a resultados de pesquisa do
mundo (web/consultas). Economiza tempo e recursos evitando repetição.
"""
from __future__ import annotations

from backend.memory.cache_manager import CacheManager


class WorldCache:
    """Memoriza resultados de consultas ao mundo, com TTL e invalidação."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._cache = CacheManager(db_path)

    def get_cached(self, query: str):
        """Devolve o resultado memorizado de uma consulta, ou None."""
        return self._cache.get_json("world:" + query.lower().strip())

    def cache_result(self, query: str, result, ttl: int = 3600) -> None:
        """Memoriza o resultado de uma consulta ao mundo."""
        self._cache.set_json("world:" + query.lower().strip(), result,
                             ttl=ttl, kind="search")

    def invalidate(self, pattern: str = "") -> int:
        """Invalida entradas cujo padrão bate (prefixo)."""
        return self._cache.invalidate("world:" + pattern)

    def stats(self) -> dict:
        return self._cache.stats()
