"""Capability tokens + comandos assinados (9.18 · FASE 5 · trava de segurança).

A ÚNICA coisa que o servidor faz em relação ao device é **assinar** um pedido de
capacidade — nunca executá-lo. O Local Agent nativo valida a assinatura, o prazo e
o nonce (anti-replay) ANTES de agir. Sem os quatro — capacidade conhecida,
assinatura válida, dentro do prazo, nonce novo — nada acontece.

Puro stdlib (hmac/hashlib), determinístico, sem I/O de device. Comparação em tempo
constante; o segredo da ponte nunca é logado.

Fluxo: servidor `sign_command(cap, resource)` → token → (transporte) → Local Agent
`verify_command(token, seen=nonce_store)` → grant válido ⇒ o Agent executa
localmente, sob a permissão do dono; grant inválido ⇒ recusa honesta.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Optional

from backend.core import new_id

# Capacidades possíveis do corpo local (o "posso fazer" ≠ "sei fazer").
CAPABILITIES = frozenset({
    "CAN_READ_FILES", "CAN_WRITE_FILES", "CAN_SCREENSHOT",
    "CAN_BROWSER", "CAN_RUN_COMMAND", "CAN_CONTROL_APP",
})

_DEFAULT_TTL = 30.0           # segundos — grants são curtos por segurança
_EPHEMERAL = os.urandom(32)   # segredo de processo se ANTS_BRIDGE_SECRET faltar


def _secret(secret: Optional[bytes] = None) -> bytes:
    if secret is not None:
        return secret
    s = (os.environ.get("ANTS_BRIDGE_SECRET") or "").strip()
    return s.encode("utf-8") if s else _EPHEMERAL


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(txt: str) -> bytes:
    pad = "=" * (-len(txt) % 4)
    return base64.urlsafe_b64decode(txt + pad)


@dataclass
class CapabilityGrant:
    """Um pedido de capacidade assinado — dados, jamais execução."""

    capability: str
    resource: str
    nonce: str
    issued_at: float
    expires_at: float

    def to_dict(self) -> dict:
        return {"capability": self.capability, "resource": self.resource,
                "nonce": self.nonce, "issued_at": self.issued_at,
                "expires_at": self.expires_at}


def sign_command(capability: str, resource: str, *, ttl_seconds: float = _DEFAULT_TTL,
                 secret: Optional[bytes] = None) -> str:
    """Assina um pedido de capacidade (o servidor PROPÕE). Nunca executa nada."""
    if capability not in CAPABILITIES:
        raise ValueError(f"capacidade desconhecida: {capability}")
    now = time.time()
    payload = {"capability": capability, "resource": str(resource),
               "nonce": new_id("cap"), "issued_at": now,
               "expires_at": now + max(1.0, float(ttl_seconds))}
    body = _b64(json.dumps(payload, sort_keys=True).encode("utf-8"))
    sig = hmac.new(_secret(secret), body.encode("ascii"), hashlib.sha256).digest()
    return body + "." + _b64(sig)


def verify_command(token: str, *, secret: Optional[bytes] = None,
                   seen: Optional[set] = None) -> tuple[bool, object]:
    """Valida assinatura + prazo + nonce (o Local Agent VALIDA antes de agir).

    Devolve (True, CapabilityGrant) ou (False, motivo). Se `seen` for passado,
    protege contra replay: um nonce só vale uma vez.
    """
    try:
        body, sig_b64 = token.split(".", 1)
    except (ValueError, AttributeError):
        return False, "token malformado"
    expected = hmac.new(_secret(secret), body.encode("ascii"),
                        hashlib.sha256).digest()
    try:
        given = _unb64(sig_b64)
    except Exception:  # noqa: BLE001
        return False, "assinatura ilegível"
    if not hmac.compare_digest(expected, given):
        return False, "assinatura inválida"
    try:
        p = json.loads(_unb64(body).decode("utf-8"))
    except Exception:  # noqa: BLE001
        return False, "payload ilegível"
    if p.get("capability") not in CAPABILITIES:
        return False, "capacidade desconhecida"
    if time.time() > float(p.get("expires_at", 0)):
        return False, "expirado"
    nonce = p.get("nonce")
    if seen is not None:
        if nonce in seen:
            return False, "nonce reutilizado (replay)"
        seen.add(nonce)
    return True, CapabilityGrant(
        capability=p["capability"], resource=p.get("resource", ""),
        nonce=nonce, issued_at=float(p.get("issued_at", 0)),
        expires_at=float(p["expires_at"]))
