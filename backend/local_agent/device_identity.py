"""Identidade de dispositivo (9.25 · etapa 3) — a ponte remota segura.

Para o cérebro remoto (Render) comandar um corpo local pela rede, cada
dispositivo tem uma IDENTIDADE e um SEGREDO PRÓPRIO — derivado do mestre do
Secret Vault via HMAC (`derive_bridge_secret`), nunca o mestre compartilhado.
Assim um grant assinado para o dispositivo A não vale no B; se um vazar, gira-se
só aquele contexto (ou o mestre, e todos caem juntos).

O segredo derivado é ENTREGUE UMA VEZ ao parear o dispositivo (canal do dono) e
o corpo o guarda; o cérebro o re-deriva quando precisa assinar. O registro guarda
só metadados — jamais o segredo. Puro stdlib; offline.
"""
from __future__ import annotations

import secrets
import time
from typing import Any, Optional

from backend.security.secret_vault import get_secret_vault

# Escopo do mestre da ponte no cofre (mesmo de derive_bridge_secret).
_BRIDGE = "bridge"
_SCOPE = "local_agent"


def ensure_bridge_master() -> None:
    """Garante que exista um mestre da ponte no cofre (gera um se faltar).

    O cérebro é dono do mestre: se o ambiente não trouxe `ANTS_BRIDGE_SECRET`,
    cria um aleatório de processo — os derivados por dispositivo nascem dele.
    """
    vault = get_secret_vault()
    if not vault.exists(_BRIDGE):
        vault.put(_BRIDGE, secrets.token_hex(32), scope=_SCOPE)


def device_secret(device_id: str) -> bytes:
    """Segredo POR DISPOSITIVO, derivado do mestre (determinístico)."""
    ensure_bridge_master()
    return get_secret_vault().derive(_BRIDGE, f"device:{device_id}", scope=_SCOPE)


class DeviceRegistry:
    """Registro dos dispositivos pareados — metadados, nunca segredos."""

    def __init__(self) -> None:
        self._devices: dict[str, dict[str, Any]] = {}

    def register(self, device_id: str, name: str = "") -> dict[str, Any]:
        """Pareia um dispositivo e devolve o SEGREDO derivado UMA vez (pairing)."""
        if not device_id:
            raise ValueError("device_id é obrigatório")
        now = time.time()
        rec = self._devices.get(device_id) or {"device_id": device_id,
                                               "registered_at": now}
        rec["name"] = name or rec.get("name", "")
        rec["last_seen"] = now
        self._devices[device_id] = rec
        # entregue UMA vez no pareamento; depois o cérebro re-deriva.
        return {"device_id": device_id, "name": rec["name"],
                "secret": device_secret(device_id).hex(),
                "registered_at": rec["registered_at"]}

    def is_registered(self, device_id: str) -> bool:
        return device_id in self._devices

    def touch(self, device_id: str) -> None:
        if device_id in self._devices:
            self._devices[device_id]["last_seen"] = time.time()

    def revoke(self, device_id: str) -> bool:
        return self._devices.pop(device_id, None) is not None

    def info(self, device_id: str) -> Optional[dict[str, Any]]:
        d = self._devices.get(device_id)
        return dict(d) if d else None       # metadados; nunca o segredo

    def list(self) -> list[dict[str, Any]]:
        return [dict(d) for d in self._devices.values()]


_INSTANCE: Optional[DeviceRegistry] = None


def get_device_registry() -> DeviceRegistry:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = DeviceRegistry()
    return _INSTANCE
