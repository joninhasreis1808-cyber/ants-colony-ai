"""Agregador dos routers da API do Ant's.

Reexporta todos os routers das fases para importação conveniente:

    from backend.api.routes import (
        hive_router, perception_router, action_router,
        permissions_router, memory_router, factory_router,
    )
"""
from __future__ import annotations

from backend.api.routes.action import router as action_router
from backend.api.routes.factory import router as factory_router
from backend.api.routes.hive import router as hive_router
from backend.api.routes.memory import router as memory_router
from backend.api.routes.perception import router as perception_router
from backend.api.routes.permissions import router as permissions_router

__all__ = [
    "hive_router", "perception_router", "action_router",
    "permissions_router", "memory_router", "factory_router",
]
