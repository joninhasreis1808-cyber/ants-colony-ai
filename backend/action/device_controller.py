"""Controle de dispositivos (mobile/desktop) mediado por permissões.

Expõe operações de alto nível — abrir/fechar apps, screenshot, localização,
toques/gestos, notificações — delegando o "como" a um backend plugável.
TODAS as ações exigem permissão explícita (nível ADVANCED) e são
auditadas. Na Fase 2 há um backend simulado; a Fase 3 pluga ADB/uiautomator.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from backend.action.app_launcher import AppLauncher, InMemoryBackend
from backend.permissions.permission_manager import PermissionManager


@dataclass
class Location:
    """Coordenadas geográficas do dispositivo."""

    latitude: float
    longitude: float
    accuracy_m: float = 10.0


class DeviceBackend(Protocol):
    """Contrato do backend de dispositivo."""

    def screenshot(self) -> str: ...
    def location(self) -> Location: ...
    def tap(self, x: int, y: int) -> bool: ...
    def notify(self, title: str, body: str) -> bool: ...


class SimulatedDevice:
    """Dispositivo simulado, determinístico para testes."""

    def __init__(self) -> None:
        self.notifications: list[tuple[str, str]] = []
        self.taps: list[tuple[int, int]] = []

    def screenshot(self) -> str:
        return "/tmp/device_screenshot.png"

    def location(self) -> Location:
        return Location(-23.5505, -46.6333)  # São Paulo, exemplo

    def tap(self, x: int, y: int) -> bool:
        self.taps.append((x, y))
        return True

    def notify(self, title: str, body: str) -> bool:
        self.notifications.append((title, body))
        return True


class DeviceController:
    """Controla um dispositivo com permissões e apps integrados."""

    def __init__(
        self,
        permissions: PermissionManager,
        backend: DeviceBackend | None = None,
        user: str = "system",
    ) -> None:
        self._perms = permissions
        self._backend = backend or SimulatedDevice()
        self._user = user
        self._apps = AppLauncher(permissions, InMemoryBackend(), user)

    def _authorize(self, action: str, resource: str = "") -> None:
        if not self._perms.check(self._user, action, resource):
            raise PermissionError(f"Ação não autorizada: {action}")

    def open_app(self, app_name: str) -> bool:
        """Abre um aplicativo no dispositivo."""
        return self._apps.launch(app_name)

    def close_app(self, app_name: str) -> bool:
        """Fecha um aplicativo no dispositivo."""
        return self._apps.close(app_name)

    def take_screenshot(self) -> str:
        """Captura a tela do dispositivo."""
        self._authorize("device.control", "screenshot")
        return self._backend.screenshot()

    def get_location(self) -> Location:
        """Obtém a localização atual (requer permissão dedicada)."""
        self._authorize("device.location", "gps")
        return self._backend.location()

    def tap(self, x: int, y: int) -> bool:
        """Simula um toque nas coordenadas (x, y)."""
        self._authorize("device.control", f"tap:{x},{y}")
        return self._backend.tap(x, y)

    def send_notification(self, title: str, body: str) -> bool:
        """Envia uma notificação ao dispositivo."""
        self._authorize("device.control", "notification")
        return self._backend.notify(title, body)
