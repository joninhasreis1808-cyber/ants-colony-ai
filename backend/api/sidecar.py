"""Entrypoint do sidecar nativo (8.0 · A).

O app Tauri inicia este processo com `ANTS_PORT` (porta livre encontrada em
runtime) e `ANTS_RUNTIME=native`. Aqui: marca o runtime nativo, aponta a
persistência para o diretório de dados do app (memória permanente — fim do
`memories_stored:0`) e sobe o FastAPI em 127.0.0.1 na porta dada.

No modo web (Render) este arquivo não é usado — lá o uvicorn sobe direto.
"""
from __future__ import annotations

import os
from pathlib import Path


def _prepare_native_data_dir() -> None:
    """Persiste tudo (DB, escopos, auditoria) no diretório de dados do app."""
    base = os.environ.get("ANTS_DATA_DIR")
    if not base:
        home = Path.home()
        base = str(home / ".local" / "share" / "ants")   # padrão Linux/macOS
    Path(base).mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("ANTS_DB", str(Path(base) / "ants.db"))
    os.environ.setdefault("ANTS_SCOPES", str(Path(base) / "scopes.json"))
    os.environ.setdefault("ANTS_AUDIT_LOG", str(Path(base) / "device_audit.jsonl"))


def main() -> None:
    os.environ["ANTS_RUNTIME"] = "native"
    _prepare_native_data_dir()
    import uvicorn
    port = int(os.environ.get("ANTS_PORT", os.environ.get("PORT", "8765")))
    uvicorn.run("backend.api.main:app", host="127.0.0.1", port=port,
                log_level="warning")


if __name__ == "__main__":
    main()
