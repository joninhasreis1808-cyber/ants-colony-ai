"""Auditoria de ações de device (8.0 · B.7) — append-only.

Registra TODA ação de device: o quê, quando, qual bot/formação, escopo usado,
resultado e estado antes/depois (hash/diff). Consultável e exportável na UI.
Append-only: entradas nunca são alteradas nem removidas. Persiste em JSONL no
diretório de dados do app (opcional) e mantém um buffer em memória para a UI.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any, Optional


def state_hash(value: Any) -> str:
    """Hash estável de um estado (arquivo/DOM) para o diff antes/depois."""
    data = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]


class DeviceAudit:
    """Trilha de auditoria append-only das ações de device."""

    def __init__(self, path: Optional[str] = None, limit: int = 500) -> None:
        self._path = path or os.environ.get("ANTS_AUDIT_LOG")
        self._buf: list[dict] = []
        self._limit = limit

    def record(
        self, action: str, scope: str, result: str,
        bot: str = "", formation: str = "",
        before: Any = None, after: Any = None, extra: Optional[dict] = None,
    ) -> dict:
        """Anexa uma entrada imutável ao registro."""
        entry = {
            "ts": time.time(), "action": action, "scope": scope,
            "result": result, "bot": bot, "formation": formation,
            "before_hash": state_hash(before) if before is not None else None,
            "after_hash": state_hash(after) if after is not None else None,
            "changed": (before is not None and after is not None
                        and state_hash(before) != state_hash(after)),
        }
        if extra:
            entry.update(extra)
        self._buf.append(entry)
        if len(self._buf) > self._limit:
            self._buf = self._buf[-self._limit:]
        self._append_disk(entry)
        return entry

    def entries(self, limit: int = 100) -> list[dict]:
        """Últimas entradas para a UI (mais recentes ao fim)."""
        return self._buf[-limit:]

    def export_jsonl(self) -> str:
        """Exporta toda a trilha em memória como JSONL."""
        return "\n".join(json.dumps(e, ensure_ascii=False) for e in self._buf)

    def clear(self) -> None:
        """Limpa o buffer em memória (isolamento de testes; disco é append)."""
        self._buf.clear()

    def _append_disk(self, entry: dict) -> None:
        if not self._path:
            return
        try:
            os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
            with open(self._path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001 - best-effort
            pass


_INSTANCE: DeviceAudit | None = None


def get_device_audit() -> DeviceAudit:
    """Singleton de processo da auditoria de device."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = DeviceAudit()
    return _INSTANCE
