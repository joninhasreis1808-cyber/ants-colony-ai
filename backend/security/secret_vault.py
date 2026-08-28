"""Secret Vault dedicado (9.20 · Passo 1) — o cofre de segredos da colônia.

Hoje os segredos vivem soltos em variáveis de ambiente (`ANTS_API_TOKEN`,
`ANTS_BRIDGE_SECRET`) — um único valor por ambiente. Este cofre dá o que faltava:
**segredos nomeados, com escopo por-capacidade, rotação, prazo e auditoria** — e,
o mais importante para a ponte cérebro×corpo, **derivação**: de um segredo-mestre
nascem segredos por-dispositivo/por-capacidade via HMAC, sem precisar guardar cada
um. Se um derivado vaza, gira-se o contexto; se o mestre gira, todos caem juntos —
defesa em profundidade sobre o que a FASE 5 abriu.

Interno, offline, custo zero, puro stdlib (`hmac`/`hashlib`/`secrets`). Nunca
registra o VALOR de um segredo — só o nome, a ação e o veredito (Regra 6/segurança).
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class _Entry:
    value: bytes
    scope: str = ""                 # "" = utilizável por qualquer escopo
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    version: int = 1


class SecretVault:
    """Cofre em memória: guarda, deriva, gira e revoga segredos — com auditoria."""

    def __init__(self) -> None:
        self._store: dict[str, _Entry] = {}
        self._audit: list[dict[str, Any]] = []

    # -- escrita ------------------------------------------------------------
    def put(self, name: str, value: str | bytes, *, scope: str = "",
            ttl_seconds: Optional[float] = None) -> None:
        """Guarda (ou substitui) um segredo. Valor nunca é auditado."""
        if not name:
            raise ValueError("segredo precisa de nome")
        raw = value.encode("utf-8") if isinstance(value, str) else bytes(value)
        if not raw:
            raise ValueError("segredo vazio")
        prev = self._store.get(name)
        exp = time.time() + ttl_seconds if ttl_seconds else None
        self._store[name] = _Entry(value=raw, scope=scope, expires_at=exp,
                                    version=(prev.version + 1 if prev else 1))
        self._log(name, "put", scope, True)

    def rotate(self, name: str, new_value: str | bytes) -> int:
        """Troca o valor mantendo nome/escopo; o antigo vale ZERO na hora."""
        cur = self._store.get(name)
        if cur is None:
            raise KeyError(name)
        raw = new_value.encode("utf-8") if isinstance(new_value, str) else bytes(new_value)
        if not raw:
            raise ValueError("segredo vazio")
        cur.value = raw
        cur.version += 1
        cur.created_at = time.time()
        self._log(name, "rotate", cur.scope, True)
        return cur.version

    def revoke(self, name: str) -> None:
        if self._store.pop(name, None) is not None:
            self._log(name, "revoke", "", True)

    # -- leitura ------------------------------------------------------------
    def _live(self, name: str) -> Optional[_Entry]:
        e = self._store.get(name)
        if e is None:
            return None
        if e.expires_at is not None and time.time() > e.expires_at:
            self._store.pop(name, None)     # expirou → some do cofre
            self._log(name, "expire", e.scope, False)
            return None
        return e

    def _scope_ok(self, entry: _Entry, scope: Optional[str]) -> bool:
        # segredo sem escopo é livre; com escopo, exige o mesmo escopo.
        return not entry.scope or scope is None or entry.scope == scope

    def get(self, name: str, *, scope: Optional[str] = None) -> Optional[bytes]:
        """Devolve o valor se existir, não expirou e o escopo confere (senão None)."""
        e = self._live(name)
        if e is None:
            self._log(name, "get", scope or "", False, "inexistente/expirado")
            return None
        if not self._scope_ok(e, scope):
            self._log(name, "get", scope or "", False, "escopo incompatível")
            return None
        self._log(name, "get", e.scope, True)
        return e.value

    def exists(self, name: str) -> bool:
        return self._live(name) is not None

    # -- derivação e verificação -------------------------------------------
    def derive(self, name: str, context: str, *, length: int = 32,
               scope: Optional[str] = None) -> Optional[bytes]:
        """Deriva um segredo por-contexto do mestre `name` via HMAC-SHA256.

        Determinístico: mesmo (mestre, contexto) → mesmo derivado. Um master
        vira muitos segredos (por dispositivo, por capacidade) sem armazená-los.
        """
        master = self.get(name, scope=scope)
        if master is None:
            return None
        out = hmac.new(master, context.encode("utf-8"), hashlib.sha256).digest()
        self._log(name, "derive", context, True)
        return out[:length]

    def verify(self, name: str, candidate: str | bytes, *,
               scope: Optional[str] = None) -> bool:
        """Compara um candidato ao segredo em TEMPO CONSTANTE (anti-timing)."""
        e = self._live(name)
        if e is None or not self._scope_ok(e, scope):
            self._log(name, "verify", scope or "", False)
            return False
        cand = candidate.encode("utf-8") if isinstance(candidate, str) else bytes(candidate)
        ok = hmac.compare_digest(e.value, cand)
        self._log(name, "verify", e.scope, ok)
        return ok

    # -- introspecção -------------------------------------------------------
    def names(self) -> list[str]:
        return sorted(n for n in self._store if self._live(n) is not None)

    def info(self, name: str) -> Optional[dict[str, Any]]:
        """Metadados de um segredo — NUNCA o valor."""
        e = self._live(name)
        if e is None:
            return None
        return {"name": name, "scope": e.scope, "version": e.version,
                "created_at": e.created_at, "expires_at": e.expires_at}

    def audit(self) -> list[dict[str, Any]]:
        return list(self._audit)

    def seed_from_env(self) -> int:
        """Adota os segredos de ambiente existentes (unifica a fonte). Idempotente."""
        loaded = 0
        for env, name, scope in (
            ("ANTS_BRIDGE_SECRET", "bridge", "local_agent"),
            ("ANTS_API_TOKEN", "api_token", "api"),
        ):
            val = (os.environ.get(env) or "").strip()
            if val and not self.exists(name):
                self.put(name, val, scope=scope)
                loaded += 1
        return loaded

    def _log(self, name: str, action: str, scope: str, ok: bool,
             reason: str = "") -> None:
        self._audit.append({"ts": time.time(), "name": name, "action": action,
                            "scope": scope, "ok": ok, "reason": reason})


_INSTANCE: Optional[SecretVault] = None


def get_secret_vault() -> SecretVault:
    """Singleton de processo do cofre (semeado do ambiente na 1ª vez)."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = SecretVault()
        _INSTANCE.seed_from_env()
    return _INSTANCE


def derive_bridge_secret(device_id: str) -> Optional[bytes]:
    """Segredo da ponte POR DISPOSITIVO, derivado do mestre 'bridge'.

    Em vez de todos os corpos compartilharem um único `ANTS_BRIDGE_SECRET`, cada
    dispositivo recebe um derivado exclusivo — vazou um, gira-se só aquele.
    """
    return get_secret_vault().derive("bridge", f"device:{device_id}",
                                     scope="local_agent")
