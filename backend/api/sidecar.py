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


def seed_secret_vault() -> bool:
    """Adota o segredo da ponte que o app Tauri passou (handshake 9.20).

    O processo Tauri gera `ANTS_BRIDGE_SECRET` e o entrega ao sidecar; aqui ele
    entra no Secret Vault como mestre 'bridge', habilitando a derivação por
    dispositivo. O `capability_tokens` já lê o mesmo env — os dois lados falam a
    mesma língua. Devolve True se o mestre da ponte ficou disponível.
    """
    from backend.security.secret_vault import get_secret_vault
    vault = get_secret_vault()           # semeia de ANTS_BRIDGE_SECRET/ANTS_API_TOKEN
    return vault.exists("bridge")


def main() -> None:
    os.environ["ANTS_RUNTIME"] = "native"
    # O corpo precisa se declarar para as DUAS leituras de runtime que existem:
    # `backend/action/runtime.py` lê ANTS_RUNTIME e `backend/local_agent/runtime.py`
    # lê ANTS_LOCAL_AGENT. Faltando a segunda, `/local-agent/status` respondia
    # `native: false` DENTRO do app nativo — a colônia rodando no corpo acreditava
    # não ter corpo, e as capacidades de dispositivo seriam recusadas justamente
    # onde deveriam funcionar. Achado compilando e RODANDO o app de verdade.
    #
    # Marcar aqui é seguro por construção: este entrypoint só existe no binário
    # do sidecar (app/ants_backend.spec). O deploy web sobe `backend.api.main:app`
    # direto pelo uvicorn e nunca importa este módulo — o servidor não tem como
    # se declarar nativo por acidente.
    os.environ["ANTS_LOCAL_AGENT"] = "native"
    _prepare_native_data_dir()
    seed_secret_vault()
    import uvicorn
    port = int(os.environ.get("ANTS_PORT", os.environ.get("PORT", "8765")))
    uvicorn.run("backend.api.main:app", host="127.0.0.1", port=port,
                log_level="warning")


if __name__ == "__main__":
    main()
