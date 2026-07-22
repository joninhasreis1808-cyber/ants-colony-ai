"""Router de provedores de busca com fallback automático.

Ordena os providers por prioridade (os pagos/melhores primeiro, se
disponíveis) e tenta cada um em sequência. Se um falhar ou não retornar
nada, cai para o próximo. O DuckDuckGo, sempre disponível, é a rede de
segurança final.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from backend.core import SearchResult
from backend.providers.base import SearchProvider
from backend.providers.brave import BraveProvider
from backend.providers.duckduckgo import DuckDuckGoProvider
from backend.providers.tavily import TavilyProvider

logger = logging.getLogger("ants.router")


class ProviderRouter:
    """Seleciona e encadeia providers com tolerância a falhas."""

    def __init__(
        self, providers: Optional[list[SearchProvider]] = None
    ) -> None:
        # Ordem de preferência: Tavily > Brave > DuckDuckGo.
        self._providers = providers or [
            TavilyProvider(),
            BraveProvider(),
            DuckDuckGoProvider(),
        ]
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
        for provider in self._providers:
            if not provider.available:
                continue
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
