"""Operárias — operações de arquivo (8.0 · C.2), sob toda a Parte B.

`pathlib`/`shutil` (stdlib): listar, ler, criar, mover, copiar, renomear,
apagar (com confirmação), buscar, detectar duplicados. SEMPRE dentro da
whitelist e passando pelo gate; ações destrutivas exigem confirmação; lote
tem dry-run antes. No runtime web só PLANEJA (declarado); no nativo executa.
"""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Optional


class DeviceFiles:
    """Executa (ou declara) operações de arquivo com segurança."""

    def __init__(self) -> None:
        from backend.action.action_gate import get_action_gate
        from backend.monitoring.device_audit import get_device_audit
        self._gate = get_action_gate()
        self._audit = get_device_audit()

    def _check(self, action: str, path: str, external: Optional[str] = None):
        return self._gate.evaluate(action, path, external)

    def _run(self, action: str, path: str, fn, *, destructive=False,
             confirmed=False, dry_run=False, before=None):
        from backend.action.runtime import is_native
        d = self._check(action, path)
        if not d.allowed:
            return {"executed": False, "denied": True, "reason": d.reason}
        if d.needs_confirmation and not confirmed:
            return {"executed": False, "needs_confirmation": True,
                    "reason": d.reason, "action": action, "path": path}
        if dry_run:
            return {"executed": False, "dry_run": True, "action": action,
                    "path": path, "would_change": destructive}
        if not is_native():
            return {"executed": False, "declared": True, "action": action,
                    "path": path,
                    "note": "execução só no app nativo (modo web planeja)"}
        result = fn()
        entry = self._audit.record(action, d.scope, "ok", bot="operaria",
                                   before=before, after=result)
        return {"executed": True, "action": action, "path": path,
                "result": result, "audit": entry}

    # ---- leitura ----
    def list_dir(self, path: str) -> dict:
        return self._run("list", path,
                         lambda: [p.name for p in Path(path).iterdir()])

    def read_text(self, path: str, limit: int = 20000) -> dict:
        return self._run("read", path,
                         lambda: Path(path).read_text(errors="replace")[:limit])

    def search(self, root: str, name_contains: str) -> dict:
        def _find():
            return [str(p) for p in Path(root).rglob("*")
                    if name_contains.lower() in p.name.lower()][:200]
        return self._run("search", root, _find)

    def find_duplicates(self, root: str) -> dict:
        def _dups():
            seen: dict[str, str] = {}
            dups: list[list[str]] = []
            for p in Path(root).rglob("*"):
                if p.is_file():
                    h = hashlib.sha256(p.read_bytes()).hexdigest()
                    if h in seen:
                        dups.append([seen[h], str(p)])
                    else:
                        seen[h] = str(p)
            return dups
        return self._run("search", root, _dups)

    # ---- escrita ----
    def create(self, path: str, content: str = "") -> dict:
        return self._run("create", path,
                         lambda: (Path(path).write_text(content), str(path))[1])

    def move(self, src: str, dst: str, confirmed: bool = False,
             dry_run: bool = False) -> dict:
        return self._run("move", src, lambda: shutil.move(src, dst) or dst,
                         destructive=True, confirmed=confirmed, dry_run=dry_run,
                         before=src)

    def copy(self, src: str, dst: str) -> dict:
        return self._run("copy", src, lambda: shutil.copy2(src, dst) and dst or dst)

    def delete(self, path: str, confirmed: bool = False,
               dry_run: bool = False) -> dict:
        def _rm():
            p = Path(path)
            p.unlink() if p.is_file() else shutil.rmtree(p)
            return f"apagado: {path}"
        return self._run("delete", path, _rm, destructive=True,
                         confirmed=confirmed, dry_run=dry_run, before=path)
