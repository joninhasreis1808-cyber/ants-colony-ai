"""Testes do controlador de dispositivo e lançador de apps."""
from __future__ import annotations

import pytest

from backend.action.app_launcher import AppLauncher, InMemoryBackend
from backend.action.device_controller import DeviceController, SimulatedDevice
from backend.permissions.permission_manager import PermissionManager


def make_pm(level: int, user: str = "system") -> PermissionManager:
    pm = PermissionManager()
    pm.grant(user, level)
    return pm


def test_app_launch_requires_advanced():
    launcher = AppLauncher(make_pm(4), InMemoryBackend(["browser"]))
    assert launcher.launch("browser")
    assert launcher.is_running("browser")


def test_app_launch_denied_low_level():
    launcher = AppLauncher(make_pm(2), InMemoryBackend(["browser"]))
    with pytest.raises(PermissionError):
        launcher.launch("browser")


def test_device_screenshot_and_location():
    dev = DeviceController(make_pm(4), SimulatedDevice())
    assert dev.take_screenshot().endswith(".png")
    loc = dev.get_location()
    assert -90 <= loc.latitude <= 90


def test_device_notification_recorded():
    backend = SimulatedDevice()
    dev = DeviceController(make_pm(4), backend)
    assert dev.send_notification("Oi", "corpo")
    assert backend.notifications == [("Oi", "corpo")]
