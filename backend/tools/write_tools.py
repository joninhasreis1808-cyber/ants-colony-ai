"""Ferramentas de ESCRITA (9.8 · FASE D) — as "mãos" que modificam, com trava.

Escrever e apagar são irreversíveis, então aqui a regra é dupla:
  1) sempre atrás do `path_guard` (só dentro das pastas autorizadas pelo dono);
  2) **dry-run por padrão** — a ferramenta diz o que FARIA e só age de verdade
     com `confirm: true`. É o "olhe antes de apagar" da colônia.

O escopo de permissão (`write_files`) já é validado pelo ToolRegistry ANTES de
chegar aqui (capacidade ≠ permissão). Estas funções assumem que a permissão
passou e cuidam da segurança do CAMINHO e da confirmação. Puro stdlib.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.permissions.path_guard import get_path_guard

_MAX_BYTES = 200_000


def _ensure_allowed(path: str) -> None:
    if not get_path_guard().is_allowed(path):
        raise PermissionError(
            f"caminho fora das pastas autorizadas: {path}. "
            "Autorize a pasta em /device/paths/allow.")


def _confirmed(args: dict) -> bool:
    return bool(args.get("confirm"))


def write_file(args: dict[str, Any]) -> dict[str, Any]:
    """Escreve texto num arquivo autorizado. Dry-run salvo `confirm: true`."""
    path = str(args.get("path", ""))
    _ensure_allowed(path)
    content = str(args.get("content", ""))
    data = content.encode("utf-8")
    if len(data) > _MAX_BYTES:
        return {"path": path, "ok": False,
                "error": f"conteúdo excede {_MAX_BYTES} bytes"}
    fp = Path(path)
    existed = fp.exists()
    if not _confirmed(args):
        return {"path": path, "dry_run": True, "would_write": True,
                "bytes": len(data), "exists": existed,
                "note": "prévia — envie confirm:true para gravar de verdade"}
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_bytes(data)
    return {"path": path, "dry_run": False, "written": True,
            "bytes": len(data), "overwrote": existed}


def make_dir(args: dict[str, Any]) -> dict[str, Any]:
    """Cria uma pasta autorizada. Dry-run salvo `confirm: true`."""
    path = str(args.get("path", ""))
    _ensure_allowed(path)
    dp = Path(path)
    if not _confirmed(args):
        return {"path": path, "dry_run": True, "would_create": True,
                "exists": dp.exists(),
                "note": "prévia — envie confirm:true para criar de verdade"}
    dp.mkdir(parents=True, exist_ok=True)
    return {"path": path, "dry_run": False, "created": True}


def delete_path(args: dict[str, Any]) -> dict[str, Any]:
    """Apaga um arquivo autorizado ou pasta VAZIA. Dry-run salvo `confirm: true`.

    Nunca apaga uma árvore inteira (pasta com conteúdo é recusada) — segurança
    dura, mesmo com confirmação."""
    path = str(args.get("path", ""))
    _ensure_allowed(path)
    tp = Path(path)
    if not tp.exists():
        return {"path": path, "ok": False, "error": "não existe"}
    is_dir = tp.is_dir()
    if is_dir and any(tp.iterdir()):
        return {"path": path, "ok": False,
                "error": "pasta não vazia — a colônia não apaga árvores inteiras"}
    if not _confirmed(args):
        return {"path": path, "dry_run": True, "would_delete": True,
                "is_dir": is_dir,
                "note": "prévia — envie confirm:true para apagar de verdade"}
    if is_dir:
        tp.rmdir()
    else:
        tp.unlink()
    return {"path": path, "dry_run": False, "deleted": True, "was_dir": is_dir}
