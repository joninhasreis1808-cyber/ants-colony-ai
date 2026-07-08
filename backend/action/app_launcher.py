"""Lançador de aplicativos no dispositivo.

Abstrai o backend do sistema operacional por trás de uma interface
uniforme. Na Fase 2 fornecemos um backend em memória (registrável e
testável) e a fiação para um backend real de SO na Fase 3. Todas as ações
exigem permissão.
"""
from __future__ import annotations

from typing import Protocol

from backend.permissions.permission_manager import PermissionManager


class LauncherBackend(Protocol):
    """Contrato que qualquer backend de lançamento deve cumprir."""

    def launch(self, app_name: str) -> bool: ...
    def close(self, app_name: str) -> bool: ...
    def list_installed(self) -> list[str]: ...
    def is_running(self, app_name: str) -> bool: ...


class InMemoryBackend:
    """Backend simulado: mantém estado de apps 'instalados' e 'rodando'."""

    def __init__(self, installed: list[str] | None = None) -> None:
        self._installed = set(installed or ["browser", "notes", "calc"])
        self._running: set[str] = set()

    def launch(self, app_name: str) -> bool:
        if app_name not in self._installed:
            return False
        self._running.add(app_name)
        return True

    def close(self, app_name: str) -> bool:
        self._running.discard(app_name)
        return True

    def list_installed(self) -> list[str]:
        return sorted(self._installed)

    def is_running(self, app_name: str) -> bool:
        return app_name in self._running


class AppLauncher:
    """Abre/fecha apps através de um backend, com permissões e auditoria."""

    def __init__(
        self,
        permissions: PermissionManager,
        backend: LauncherBackend | None = None,
        user: str = "system",
    ) -> None:
        self._perms = permissions
        self._backend = backend or InMemoryBackend()
        self._user = user

    def launch(self, app_name: str) -> bool:
        """Abre um app (ação sensível, requer nível ADVANCED)."""
        if not self._perms.check(self._user, "app.launch", app_name):
            raise PermissionError("Sem permissão para abrir apps")
        return self._backend.launch(app_name)

    def close(self, app_name: str) -> bool:
        """Fecha um app."""
        if not self._perms.check(self._user, "app.close", app_name):
            raise PermissionError("Sem permissão para fechar apps")
        return self._backend.close(app_name)

    def list_installed(self) -> list[str]:
        """Lista apps instalados (leitura, sem ação)."""
        return self._backend.list_installed()

    def is_running(self, app_name: str) -> bool:
        """Verifica se um app está em execução."""
        return self._backend.is_running(app_name)
