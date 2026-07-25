"""Guarda de caminhos (8.0 · B.2).

A colônia só lê/escreve dentro de pastas explicitamente autorizadas pelo
usuário (whitelist). Sobre isso há uma **blacklist imutável** de caminhos
críticos (raiz do SO, System32, /etc, /bin, ~/.ssh, chaveiros) que é recusada
**mesmo que o usuário tente autorizar**. Todo caminho é normalizado (resolve
symlinks e `..`) para impedir escape da whitelist.
"""
from __future__ import annotations

import os
from pathlib import Path

# Blacklist DURA — nunca liberável, nem por pedido do usuário (§B.2/B.10).
_BLACKLIST = (
    "/etc", "/bin", "/sbin", "/usr/bin", "/usr/sbin", "/boot", "/dev",
    "/proc", "/sys", "/root", "/var/lib", "/System", "/Library",
    "C:\\Windows", "C:\\Windows\\System32", "C:\\Program Files",
)
# Sufixos/nomes sensíveis recusados em qualquer lugar (credenciais/chaves).
_SENSITIVE = (".ssh", ".gnupg", ".aws", ".config/gcloud", "keychain",
              "id_rsa", "id_ed25519", ".env", "shadow", "sam")


def _norm(path: str) -> str:
    """Resolve symlinks e `..`, devolvendo caminho absoluto canônico."""
    try:
        return str(Path(os.path.expanduser(path)).resolve(strict=False))
    except Exception:  # noqa: BLE001 - caminho inválido → string crua absoluta
        return os.path.abspath(os.path.expanduser(path))


def is_blacklisted(path: str) -> bool:
    """Caminho crítico (raiz do SO, credenciais)? Recusado sempre."""
    p = _norm(path)
    low = p.lower()
    for bad in _BLACKLIST:
        b = _norm(bad).lower()
        if low == b or low.startswith(b + os.sep) or low.startswith(b + "/"):
            return True
    return any(tok in low for tok in _SENSITIVE)


class PathGuard:
    """Whitelist de pastas autorizadas + blacklist imutável."""

    def __init__(self) -> None:
        self._allowed: set[str] = set()

    def allow(self, path: str) -> bool:
        """Autoriza uma pasta — a menos que esteja na blacklist dura."""
        p = _norm(path)
        if is_blacklisted(p):
            return False           # recusa MESMO com o usuário pedindo
        self._allowed.add(p)
        return True

    def disallow(self, path: str) -> None:
        self._allowed.discard(_norm(path))

    def clear(self) -> None:
        self._allowed.clear()

    def allowed_dirs(self) -> list[str]:
        return sorted(self._allowed)

    def is_allowed(self, path: str) -> bool:
        """Caminho está dentro de alguma pasta autorizada e fora da blacklist?"""
        p = _norm(path)
        if is_blacklisted(p):
            return False
        for base in self._allowed:
            if p == base or p.startswith(base + os.sep) or p.startswith(base + "/"):
                return True
        return False

    def check(self, path: str) -> dict:
        """Veredito auditável para um caminho (para logs e UI honesta)."""
        p = _norm(path)
        if is_blacklisted(p):
            return {"allowed": False, "path": p, "reason": "blacklist imutável"}
        if self.is_allowed(p):
            return {"allowed": True, "path": p, "reason": "dentro da whitelist"}
        return {"allowed": False, "path": p,
                "reason": "fora das pastas autorizadas"}


_INSTANCE: PathGuard | None = None


def get_path_guard() -> PathGuard:
    """Singleton de processo da guarda de caminhos."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = PathGuard()
    return _INSTANCE
