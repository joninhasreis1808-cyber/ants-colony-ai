"""Testes da busca web robusta (8.0 · Parte E) — rate limit + UA honesto."""
from __future__ import annotations

import pytest

from backend.search.rate_limiter import DomainRateLimiter
from backend.search.user_agents import HONEST, honest, next_agent, pool


def test_user_agent_honesto_identifica_o_bot():
    assert "ants-colony-ai" in honest()
    assert honest() == HONEST
    assert next_agent() in pool()


def test_rate_limit_1_req_por_segundo():
    t = {"now": 100.0}
    rl = DomainRateLimiter(min_interval=1.0, clock=lambda: t["now"])
    url = "https://exemplo.com/busca"
    assert rl.wait_time(url) == 0.0        # 1a chamada: livre
    rl.record(url)
    t["now"] += 0.3
    assert rl.wait_time(url) == pytest.approx(0.7, abs=1e-6)   # espera o resto
    t["now"] += 1.0
    assert rl.wait_time(url) == 0.0        # passou 1s → livre


def test_backoff_exponencial_e_reset():
    rl = DomainRateLimiter()
    url = "https://x.com/y"
    assert rl.penalize(url) == 1.0
    assert rl.penalize(url) == 2.0
    assert rl.penalize(url) == 4.0
    assert rl.penalize(url) == 8.0
    assert rl.penalize(url) == 8.0         # teto em 8s
    rl.reset(url)
    # após reset, backoff volta a zero (só o intervalo base conta)
    rl.record(url)
    assert rl.wait_time(url) <= 1.0


def test_robots_permissivo_em_falha():
    rl = DomainRateLimiter()
    # domínio inexistente → sem robots acessível → permissivo (não trava)
    assert rl.allowed_by_robots("http://dominio-que-nao-existe-xyz.invalid/p") is True
