"""Ferramentas de arquivo READ-ONLY (9.6 · FASE A) — as primeiras "mãos".

Só leitura, e sempre atrás do path_guard (8.0): a colônia só lê DENTRO das
pastas autorizadas pelo dono. Sem pasta liberada, recusa tudo — a árvore do
sistema fica intocável. Execução real de escrita/apagar fica para a FASE D/E,
com dry-run + aprovação. Puro stdlib.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.permissions.path_guard import get_path_guard

_MAX_ENTRIES = 300
_MAX_BYTES = 40_000


def _ensure_allowed(path: str) -> None:
    if not get_path_guard().is_allowed(path):
        raise PermissionError(
            f"caminho fora das pastas autorizadas: {path}. "
            "Autorize a pasta em /device/paths/allow.")


def list_dir(args: dict[str, Any]) -> dict[str, Any]:
    """Lista o conteúdo de uma pasta autorizada (nomes, tipo, tamanho)."""
    path = str(args.get("path", ""))
    _ensure_allowed(path)
    base = Path(path)
    if not base.is_dir():
        return {"path": path, "entries": [], "note": "não é um diretório"}
    entries = []
    for item in sorted(base.iterdir())[:_MAX_ENTRIES]:
        try:
            is_dir = item.is_dir()
            entries.append({"name": item.name, "dir": is_dir,
                            "size": (None if is_dir else item.stat().st_size)})
        except OSError:
            continue
    return {"path": path, "entries": entries, "count": len(entries)}


def read_file(args: dict[str, Any]) -> dict[str, Any]:
    """Lê o início de um arquivo autorizado (texto, limitado)."""
    path = str(args.get("path", ""))
    _ensure_allowed(path)
    fp = Path(path)
    if not fp.is_file():
        return {"path": path, "error": "não é um arquivo"}
    data = fp.read_bytes()[:_MAX_BYTES]
    return {"path": path, "bytes": len(data),
            "truncated": fp.stat().st_size > _MAX_BYTES,
            "text": data.decode("utf-8", "replace")}
