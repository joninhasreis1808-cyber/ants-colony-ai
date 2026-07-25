"""Escopos de permissão de dispositivo (8.0 · B.1).

Permissões granulares e independentes para o que a colônia pode fazer no
dispositivo. **Nenhuma concedida por padrão.** Cada escopo é revogável, pode
ter validade (TTL — "confiar por 1 hora") e é persistido em disco (JSON no
diretório de dados do app) para sobreviver a reinícios no runtime nativo.

Toda ação de device valida o escopo aqui ANTES de executar. Sem escopo →
recusa honesta, nunca execução silenciosa.
"""
from __future__ import annotations

import json
import os
import time
from typing import Optional

# Os sete escopos independentes do contrato (§B.1).
SCOPES = (
    "read_files", "write_files", "run_apps", "control_input",
    "screen_capture", "system_commands", "network",
)


class DeviceScopes:
    """Concede/revoga/consulta escopos, com validade e persistência."""

    def __init__(self, path: Optional[str] = None) -> None:
        self._granted: dict[str, Optional[float]] = {}   # escopo → expira_em
        self._path = path or os.environ.get("ANTS_SCOPES")
        self._load()

    def grant(self, scope: str, ttl_seconds: Optional[int] = None) -> None:
        """Concede um escopo; `ttl_seconds` limita no tempo (revogável)."""
        if scope not in SCOPES:
            raise ValueError(f"escopo desconhecido: {scope}")
        self._granted[scope] = (time.time() + ttl_seconds) if ttl_seconds else None
        self._save()

    def revoke(self, scope: str) -> None:
        """Revoga imediatamente um escopo."""
        self._granted.pop(scope, None)
        self._save()

    def revoke_all(self) -> None:
        """Revoga tudo (usado pelo botão de pânico e pelo 'revogar tudo')."""
        self._granted.clear()
        self._save()

    def is_granted(self, scope: str) -> bool:
        """Escopo ativo agora? Expira sozinho quando o TTL passa."""
        if scope not in self._granted:
            return False
        expires = self._granted[scope]
        if expires is not None and time.time() > expires:
            self._granted.pop(scope, None)   # expirou → esquece
            self._save()
            return False
        return True

    def granted(self) -> dict[str, dict]:
        """Estado atual de todos os escopos (para o painel de permissões)."""
        out: dict[str, dict] = {}
        for s in SCOPES:
            active = self.is_granted(s)
            exp = self._granted.get(s)
            out[s] = {
                "granted": active,
                "expires_in": round(exp - time.time()) if (active and exp) else None,
            }
        return out

    # ---- persistência (JSON no diretório de dados do app) ----
    def _load(self) -> None:
        if not self._path or not os.path.exists(self._path):
            return
        try:
            with open(self._path, encoding="utf-8") as fh:
                data = json.load(fh)
            self._granted = {k: v for k, v in data.items() if k in SCOPES}
        except Exception:  # noqa: BLE001 - arquivo corrompido → começa limpo
            self._granted = {}

    def _save(self) -> None:
        if not self._path:
            return
        try:
            os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as fh:
                json.dump(self._granted, fh)
        except Exception:  # noqa: BLE001 - persistência é best-effort
            pass


_INSTANCE: Optional[DeviceScopes] = None


def get_device_scopes() -> DeviceScopes:
    """Singleton de processo dos escopos de device."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = DeviceScopes()
    return _INSTANCE
