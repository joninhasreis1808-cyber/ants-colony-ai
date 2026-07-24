"""Rate limiter de busca por domínio (8.0 · E).

Máx. 1 req/s por domínio, com backoff exponencial (1s→2s→4s→8s) após falhas,
e respeito a `robots.txt` (`urllib.robotparser`). Educado e honesto — a colônia
não martela servidores. Determinístico e testável (o relógio é injetável).
"""
from __future__ import annotations

import time
from typing import Callable, Optional
from urllib.parse import urlparse


class DomainRateLimiter:
    """Controla a cadência de requisições por domínio."""

    def __init__(self, min_interval: float = 1.0,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self._min = min_interval
        self._clock = clock
        self._last: dict[str, float] = {}
        self._backoff: dict[str, float] = {}

    @staticmethod
    def _domain(url: str) -> str:
        return urlparse(url).netloc.lower() or url

    def wait_time(self, url: str) -> float:
        """Segundos a esperar antes de chamar este domínio (0 = pode agora)."""
        dom = self._domain(url)
        now = self._clock()
        gap = self._min + self._backoff.get(dom, 0.0)
        last = self._last.get(dom)
        if last is None:
            return 0.0
        remaining = gap - (now - last)
        return max(0.0, remaining)

    def record(self, url: str) -> None:
        """Marca que uma requisição foi feita agora."""
        self._last[self._domain(url)] = self._clock()

    def penalize(self, url: str) -> float:
        """Aplica backoff exponencial (1→2→4→8, teto 8s) após falha."""
        dom = self._domain(url)
        cur = self._backoff.get(dom, 0.0)
        self._backoff[dom] = min(8.0, cur * 2 if cur else 1.0)
        return self._backoff[dom]

    def reset(self, url: str) -> None:
        """Sucesso → zera o backoff do domínio."""
        self._backoff.pop(self._domain(url), None)

    def allowed_by_robots(self, url: str, ua: Optional[str] = None) -> bool:
        """Consulta robots.txt; em erro/timeout, é permissivo (não trava)."""
        try:
            from urllib.robotparser import RobotFileParser
            parsed = urlparse(url)
            rp = RobotFileParser()
            rp.set_url(f"{parsed.scheme}://{parsed.netloc}/robots.txt")
            rp.read()
            return rp.can_fetch(ua or "*", url)
        except Exception:  # noqa: BLE001 - sem robots acessível → permitir
            return True
