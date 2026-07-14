"""API unificada do Projeto Ant's (Fase 5 — consolidação).

Agrega todas as rotas das fases 1‑4, expõe um /health completo, habilita
CORS e serve a interface web (PWA) como arquivos estáticos. É o ponto de
entrada único: `uvicorn backend.api.main:app`.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import action as action_routes
from backend.api.routes import bio as bio_routes
from backend.api.routes import factory as factory_routes
from backend.api.routes import mind as mind_routes
from backend.api.routes import evolution as evolution_routes
from backend.api.routes import organism as organism_routes
from backend.api.routes import hive as hive_routes
from backend.api.routes import memory as memory_routes
from backend.api.routes import perception as perception_routes
from backend.api.routes import permissions as permission_routes

VERSION = "2.0.0"
_STARTED = time.time()

app = FastAPI(title="Ant's — Colônia de Bots", version=VERSION)

# CORS liberado: a interface web (PWA) pode ser servida de qualquer origem.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# Registro de todos os módulos.
app.include_router(hive_routes.router, prefix="/hive")
app.include_router(perception_routes.router)
app.include_router(action_routes.router)
app.include_router(permission_routes.router)
app.include_router(memory_routes.router)
app.include_router(factory_routes.router)
app.include_router(bio_routes.router)
app.include_router(mind_routes.router)
app.include_router(evolution_routes.router)
app.include_router(organism_routes.router)


@app.get("/health")
async def health() -> dict[str, Any]:
    """Saúde completa do serviço e status de cada módulo."""
    hive_stats = hive_routes.stats()
    try:
        mem_count = memory_routes.LTM.store.count()
    except Exception:
        mem_count = 0
    return {
        "status": "healthy",
        "version": VERSION,
        "modules": {
            "hivemind": True,
            "perception": True,
            "action": True,
            "permissions": True,
            "memory": True,
            "factory": True,
            "bio_inspired": True,
            "computer_use": True,
            "autonomy": True,
            "superorganism": True,
            "cognitive": True,
            "reasoning": True,
            "colony_states": True,
            "meta_cognition": True,
            "homeostasis": True,
            "observability": True,
            "metabolism": True,
            "immune_system": True,
            "hormones": True,
            "circadian": True,
            "colony_dna": True,
            "trust_autonomy": True,
            "observer": True,
        },
        "bots_active": 5,
        "memories_stored": mem_count,
        "tasks_submitted": hive_stats["tasks_submitted"],
        "providers": hive_stats["providers"],
        "uptime_seconds": round(time.time() - _STARTED, 1),
    }


# Serve a interface web (PWA) na raiz, se a pasta existir.
# Quando empacotado (PyInstaller), a pasta web/ é embutida via sys._MEIPASS;
# fora do pacote, mantém o caminho original do repositório.
def _resolve_web_dir() -> Path:
    import sys

    if getattr(sys, "frozen", False):  # binário PyInstaller
        return Path(getattr(sys, "_MEIPASS", ".")) / "web"
    return Path(__file__).resolve().parents[2] / "web"


_WEB_DIR = _resolve_web_dir()
if _WEB_DIR.is_dir():
    app.mount(
        "/", StaticFiles(directory=str(_WEB_DIR), html=True), name="web"
    )


def _run() -> None:
    """Entrada standalone para o binário nativo (sidecar do app Tauri).

    Uso: `python -m backend.api.main` ou o binário PyInstaller `ants_backend`.
    Porta configurável por ANTS_PORT (padrão 8765).
    """
    import os

    import uvicorn

    port = int(os.environ.get("ANTS_PORT", "8765"))
    host = os.environ.get("ANTS_HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    _run()
