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
from backend.api.routes import device as device_routes
from backend.api.routes import local_agent as local_agent_routes
from backend.api.routes import calibration as calibration_routes
from backend.api.routes import nervous as nervous_routes
from backend.api.routes import tools as tools_routes
from backend.api.routes import mission as mission_routes
from backend.api.routes import evolution_ledger as evolution_ledger_routes
from backend.api.security import auth_posture
from backend.events.audit import EventAuditor
from backend.events.middleware import EventBusMiddleware

VERSION = "2.0.0"
_STARTED = time.time()


def _count_tests() -> int:
    """Conta funções de teste reais varrendo tests/ (9.4 · T8) — sem número
    fixo. Se a pasta não estiver na imagem (deploy enxuto), devolve 0 e o front
    mostra "—" (honesto), nunca um valor inventado."""
    import re
    root = Path(__file__).resolve().parents[2] / "tests"
    if not root.is_dir():
        return 0
    n = 0
    for f in root.rglob("test_*.py"):
        try:
            n += len(re.findall(r"^\s*(?:async\s+)?def test_",
                                f.read_text(encoding="utf-8"), re.M))
        except Exception:  # noqa: BLE001
            pass
    return n


_TESTS = _count_tests()


def _reasoning_posture() -> dict:
    """Postura do córtex plugável (9.5) — nunca derruba o /health."""
    try:
        from backend.cognition.reasoner import posture
        return posture()
    except Exception:  # noqa: BLE001
        return {"backend": "rules", "llm": False, "model": None}


def _intelligence_posture() -> dict:
    """Postura da inteligência FASE B (9.7) — planejar/executar como um Manus.

    Declara honestamente o que a camada de inteligência oferece: as rotas que a
    Cartógrafa conhece, o planejador hierárquico, a memória de experiência viva e
    o endpoint de missão. Nunca derruba o /health."""
    try:
        from backend.cognition.cartographer import _CATALOG
        from backend.cognition.experience import (
            get_error_memory, get_strategy_memory,
        )
        from backend.tools.registry import get_tool_registry
        tools = get_tool_registry().list()
        return {
            "cartographer": [c[0] for c in _CATALOG],
            "tools": [{"name": t["name"], "risk": t["risk"],
                       "available": t["available"]} for t in tools],
            "hierarchical_planner": True,
            "contradiction_engine": True,
            "goal_drift_guard": True,
            "collective_decision": True,
            "attention_field": True,
            "adaptive_labor": True,
            "autonomous_loop": True,
            "controlled_evolution": True,
            "learning": {
                "successes": len(get_strategy_memory()._log),
                "errors": len(get_error_memory()._log),
            },
            "mission_endpoint": "/mission",
            "evolution_endpoint": "/evolution",
        }
    except Exception:  # noqa: BLE001
        return {"hierarchical_planner": False}

app = FastAPI(title="Ant's — Colônia de Bots", version=VERSION)

# CORS liberado: a interface web (PWA) pode ser servida de qualquer origem.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# Sistema nervoso central: injeta o EventBus e mantém auditoria/replay.
app.add_middleware(EventBusMiddleware)
app.state.auditor = EventAuditor()  # subscreve a "*" (todos os eventos)

# Registro de todos os módulos.
app.include_router(nervous_routes.router)
app.include_router(hive_routes.router, prefix="/hive")
app.include_router(perception_routes.router)
app.include_router(action_routes.router)
app.include_router(permission_routes.router)
app.include_router(device_routes.router)
app.include_router(local_agent_routes.router)
app.include_router(calibration_routes.router)
app.include_router(memory_routes.router)
app.include_router(factory_routes.router)
app.include_router(bio_routes.router)
app.include_router(mind_routes.router)
app.include_router(evolution_routes.router)
app.include_router(organism_routes.router)
app.include_router(tools_routes.router)
app.include_router(mission_routes.router)
app.include_router(evolution_ledger_routes.router)


@app.get("/ping")
async def ping() -> dict[str, str]:
    """Keep-alive ultraleve: acorda o serviço sem tocar em módulo algum.

    Ideal para monitores/uptime-robots no free tier (que hiberna): responde
    em microssegundos, sem consultar memória, hive ou provedores.
    """
    return {"pong": "ok"}


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
            "planning": True,
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
            "nervous_system": True,
            "metrics": True,
        },
        "bots_active": 5,
        "memories_stored": mem_count,
        "tasks_submitted": hive_stats["tasks_submitted"],
        "providers": hive_stats["providers"],
        "uptime_seconds": round(time.time() - _STARTED, 1),
        "tests": _TESTS,   # 9.4 · T8: contagem real (0 = pasta ausente → "—")
        # Córtex plugável (9.5): qual cérebro rege o raciocínio agora, sem vazar
        # a chave. backend ∈ {rules, ollama, api}. Sem cérebro externo = rules.
        "reasoning": _reasoning_posture(),
        # Inteligência FASE B (9.7): rotas da Cartógrafa, planejador hierárquico,
        # crítica (contradição + desvio) e memória de experiência viva.
        "intelligence": _intelligence_posture(),
        # Postura de autenticação (9.3 · C-2): confere o modo sem revelar o token.
        # No Render: "mode" tem que ser "token" e "publico" true.
        "auth": auth_posture(),
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
