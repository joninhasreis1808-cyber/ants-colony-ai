"""Router de provedores de busca com fallback automático (escada · fund. 04).

Ordena os providers e tenta cada um em sequência; se um falhar ou não
retornar nada, cai para o próximo. A ordem em si é decidida pelo `BudgetLadder`
(fundamento 01) — o mesmo motor que já decide qual camada de memória consultar
agora decide qual provider tentar, com o mesmo princípio: fontes sem chave
(grátis, sempre elegíveis) custam 0 e vêm primeiro; as que exigem API key paga
(Tavily, Brave) custam mais e só entram depois, opt-in, quando têm chave
configurada. Sem orçamento limitado hoje (`budget` efetivamente ilimitado) o
comportamento de "tenta todo mundo disponível até um responder" continua
idêntico — o custo só passa a valer o dia que algo quiser limitá-lo.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from backend.cognition.budget_ladder import BudgetLadder, Step
from backend.core import SearchResult
from backend.providers.base import SearchProvider
from backend.providers.brave import BraveProvider
from backend.providers.duckduckgo import DuckDuckGoProvider
from backend.providers.tavily import TavilyProvider
from backend.providers.wikipedia import WikipediaProvider

logger = logging.getLogger("ants.router")

_KEY_COST = 1.0     # provider que exige API key paga
_FREE_COST = 0.0    # fonte sem chave — nunca custa nada tentar


class ProviderRouter:
    """Seleciona e encadeia providers com tolerância a falhas."""

    def __init__(
        self, providers: Optional[list[SearchProvider]] = None
    ) -> None:
        # Ordem (fund. 04): Wikipedia e DuckDuckGo (sem chave) primeiro —
        # sempre elegíveis e grátis; Tavily/Brave (chave paga) por último,
        # tentados só se configurados e se as fontes grátis não bastarem.
        self._providers = providers or [
            WikipediaProvider(),
            DuckDuckGoProvider(),
            TavilyProvider(),
            BraveProvider(),
        ]
        # Prioridade em DOIS níveis: sem chave sempre antes de chave paga —
        # não é um acidente de posição na lista, é a escada quem garante isso
        # (fund. 04), mesmo que um provider pago apareça antes na lista de
        # entrada. Dentro do mesmo nível, a posição original desempata. Custo
        # (0 grátis / 1 pago) é o que faria um orçamento real cortar depois;
        # a prioridade é o que decide a ORDEM. `level` fica parado em 0: é
        # uma escada de um degrau só, sem profundidade. A chave do passo é o
        # ÍNDICE, não `.name` — dublês de teste podem repetir o nome, e cada
        # instância precisa continuar endereçável sozinha.
        # `getattr` com padrão: alguns chamadores passam objetos que não
        # implementam `SearchProvider` de verdade (ex.: `LocalProvider`, usado
        # só pela pesquisa profunda, nunca por `search()`/`active_providers`
        # deste router) — sem chave declarada, o padrão honesto é tratá-lo
        # como sem chave, não derrubar a construção.
        _TIER = 1000
        self._escada = BudgetLadder([
            Step(str(i), 0,
                 _KEY_COST if getattr(p, "requires_key", False) else _FREE_COST,
                 -(int(bool(getattr(p, "requires_key", False))) * _TIER + i))
            for i, p in enumerate(self._providers)
        ])
        # Diagnóstico aditivo: registra o desfecho REAL de cada provider da
        # última busca (status HTTP/erro), sem alterar a assinatura de search.
        self.last_report: list[dict] = []

    @property
    def active_providers(self) -> list[str]:
        """Nomes dos providers atualmente disponíveis."""
        return [p.name for p in self._providers if p.available]

    async def search(
        self, query: str, limit: int = 5
    ) -> tuple[list[SearchResult], list[str]]:
        """Busca com fallback.

        Devolve (resultados, tentativas) onde `tentativas` registra quais
        providers foram acionados — útil para telemetria e testes.
        """
        attempts: list[str] = []
        self.last_report = []
        disponiveis = [str(i) for i, p in enumerate(self._providers) if p.available]
        # Orçamento efetivamente ilimitado: a escada decide ORDEM e filtro de
        # disponibilidade (fund. 04), não um teto — a garantia de hoje ("tenta
        # todo mundo disponível") continua valendo byte a byte.
        plano = self._escada.plan(budget=float("inf"), available=disponiveis)
        for step in plano:
            provider = self._providers[int(step.key)]
            attempts.append(provider.name)
            try:
                results = await provider.search(query, limit)
                if results:
                    self.last_report.append(
                        {"provider": provider.name, "status": "ok",
                         "results": len(results)}
                    )
                    return results, attempts
                self.last_report.append(
                    {"provider": provider.name, "status": "sem_resultado"}
                )
                logger.info("Provider %s sem resultados", provider.name)
            except Exception as exc:  # noqa: BLE001 - fallback proposital
                # Extrai o status HTTP real quando existe (403 bloqueado etc.).
                # httpx.HTTPStatusError expõe .response.status_code; erros de
                # proxy/conexão (ex.: 403 do proxy do sandbox) só trazem o
                # código no texto — capturamos ambos, sem inventar nada.
                code = getattr(
                    getattr(exc, "response", None), "status_code", None
                )
                if code is None:
                    m = re.search(r"\b([45]\d\d)\b", str(exc))
                    if m:
                        code = int(m.group(1))
                self.last_report.append(
                    {"provider": provider.name,
                     "status": code if code is not None else "erro",
                     "error": type(exc).__name__}
                )
                logger.warning("Provider %s falhou: %s", provider.name, exc)
                continue
        return [], attempts
