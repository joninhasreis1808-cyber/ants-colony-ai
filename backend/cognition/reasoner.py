"""Córtex plugável (9.5) — o cérebro compartilhado da Mente Colmeia.

Faculdade que TODAS as castas podem consultar (a Rainha para planejar, as
Operárias para sintetizar…). Auto-detecta o melhor backend disponível e SEMPRE
degrada para o motor de REGRAS determinístico que já existe:

    API (chave OpenAI-compatível)  >  Ollama local  >  regras

Offline-first e sem embutir modelo (decisão do dono): sem cérebro externo, a
colônia raciocina por regras e declara limitação. Nada é obrigatório.

Env: ANTS_LLM=auto|api|ollama|rules · ANTS_LLM_API_URL/KEY/MODEL ·
     ANTS_OLLAMA_URL/MODEL. Sem env → regras (comportamento atual, Render seguro).
"""
from __future__ import annotations

import os
import socket
from typing import Optional
from urllib.parse import urlparse

import httpx

# Cache do probe de alcance do Ollama (por URL) — não sonda a cada chamada.
_OLLAMA_PROBE: dict[str, bool] = {}
_TRUE = {"1", "true", "yes", "sim", "on"}


def _env(k: str, d: str = "") -> str:
    return (os.environ.get(k) or d).strip()


def _mode() -> str:
    return (_env("ANTS_LLM", "auto") or "auto").lower()


def _api_key() -> str:
    return _env("ANTS_LLM_API_KEY")


def _ollama_url() -> str:
    return _env("ANTS_OLLAMA_URL", "http://127.0.0.1:11434")


def _ollama_reachable() -> bool:
    """TCP-probe rápido (sem proxy) da porta do Ollama; cacheado por URL."""
    url = _ollama_url()
    if url in _OLLAMA_PROBE:
        return _OLLAMA_PROBE[url]
    ok = False
    try:
        u = urlparse(url)
        with socket.create_connection((u.hostname or "127.0.0.1", u.port or 11434),
                                      timeout=0.5):
            ok = True
    except Exception:  # noqa: BLE001 - qualquer falha = indisponível
        ok = False
    _OLLAMA_PROBE[url] = ok
    return ok


def backend_name() -> str:
    """Qual cérebro está ativo AGORA: 'api', 'ollama' ou 'rules'."""
    m = _mode()
    if m == "rules":
        return "rules"
    if m in ("auto", "api") and _api_key():
        return "api"
    if m in ("auto", "ollama") and _ollama_reachable():
        return "ollama"
    return "rules"


def available_llm() -> bool:
    return backend_name() != "rules"


def posture() -> dict[str, object]:
    """Postura honesta do córtex para /health e capacidades (sem vazar chave)."""
    b = backend_name()
    model = None
    if b == "api":
        model = _env("ANTS_LLM_MODEL", "gpt-4o-mini")
    elif b == "ollama":
        model = _env("ANTS_OLLAMA_MODEL", "qwen2.5:3b")
    return {"backend": b, "llm": b != "rules", "model": model}


def rule_subqueries(topic: str, n: int = 4) -> list[str]:
    """Fallback determinístico: sub-perguntas por template (offline)."""
    t = (topic or "").strip().rstrip("?.")
    base = [f"o que é {t}", f"história de {t}", f"como funciona {t}",
            f"exemplos de {t}", f"vantagens e limitações de {t}"]
    return base[:max(1, n)]


class Reasoner:
    """O córtex: chamadas de baixo nível + faculdades de alto nível."""

    async def complete(self, system: str, user: str, max_tokens: int = 512) -> Optional[str]:
        """Texto do cérebro externo; None se não há LLM (usa-se o fallback)."""
        b = backend_name()
        try:
            if b == "api":
                return await self._api(system, user, max_tokens)
            if b == "ollama":
                return await self._ollama(system, user, max_tokens)
        except Exception:  # noqa: BLE001 - cérebro falhou → regras assumem
            return None
        return None

    async def _api(self, system: str, user: str, max_tokens: int) -> str:
        url = _env("ANTS_LLM_API_URL", "https://api.openai.com/v1").rstrip("/")
        model = _env("ANTS_LLM_MODEL", "gpt-4o-mini")
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.post(url + "/chat/completions",
                             headers={"Authorization": "Bearer " + _api_key()},
                             json={"model": model, "max_tokens": max_tokens,
                                   "messages": [{"role": "system", "content": system},
                                                {"role": "user", "content": user}]})
            r.raise_for_status()
            return (r.json()["choices"][0]["message"]["content"] or "").strip()

    async def _ollama(self, system: str, user: str, max_tokens: int) -> str:
        model = _env("ANTS_OLLAMA_MODEL", "qwen2.5:3b")
        async with httpx.AsyncClient(timeout=40.0) as c:
            r = await c.post(_ollama_url() + "/api/chat",
                             json={"model": model, "stream": False,
                                   "messages": [{"role": "system", "content": system},
                                                {"role": "user", "content": user}]})
            r.raise_for_status()
            return (r.json().get("message", {}).get("content") or "").strip()

    async def plan_subqueries(self, topic: str, n: int = 4) -> list[str]:
        """Quebra um tema em sub-perguntas (LLM se houver; senão, regras)."""
        sys = ("Você planeja uma pesquisa. Devolva sub-perguntas objetivas, "
               "uma por linha, sem numeração nem comentários.")
        out = await self.complete(sys, f"Tema: {topic}\nGere {n} sub-perguntas.", 256)
        if out:
            subs = [s.strip("-•* \t").strip() for s in out.splitlines() if s.strip()]
            subs = [s for s in subs if len(s) > 3][:n]
            if subs:
                return subs
        return rule_subqueries(topic, n)

    async def synthesize(self, topic: str, evidence: list[str]) -> Optional[str]:
        """Sintetiza a resposta a partir das evidências; None se não há LLM."""
        if not available_llm():
            return None
        joined = "\n".join("- " + str(e) for e in (evidence or [])[:12])
        sys = ("Sintetize uma resposta clara e honesta usando SÓ as evidências. "
               "Se forem insuficientes, diga que não há base suficiente.")
        return await self.complete(sys, f"Tema: {topic}\nEvidências:\n{joined}", 700)


_INSTANCE: Optional[Reasoner] = None


def get_reasoner() -> Reasoner:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = Reasoner()
    return _INSTANCE
