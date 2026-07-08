"""Gerenciador de permissões granulares da colmeia.

Controla o nível de cada usuário, concede/revoga acessos pontuais,
verifica se uma ação é permitida e exige confirmação para ações
sensíveis. Toda decisão é registrada no AuditLogger, dando rastreabilidade
completa. Bots herdam o nível do usuário que os aciona.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.permissions.audit_logger import AuditLogger
from backend.permissions.permission_levels import (
    Level,
    is_sensitive,
    required_level,
)


@dataclass
class PermissionResponse:
    """Resposta a uma solicitação de permissão."""

    allowed: bool
    reason: str
    needs_confirmation: bool = False


class PermissionManager:
    """Autoriza ações com base em níveis, revogações e sensibilidade."""

    def __init__(self, audit: AuditLogger | None = None) -> None:
        self._levels: dict[str, Level] = {}
        self._revoked: dict[str, set[str]] = {}
        self._audit = audit or AuditLogger()

    def grant(self, user: str, level: int) -> None:
        """Define o nível de um usuário (1..5)."""
        self._levels[user] = Level(level)
        self._audit.log(user, "permission.grant", f"level={level}", "ok")

    def revoke(self, user: str, permission: str) -> None:
        """Revoga uma ação específica para o usuário (bloqueio pontual)."""
        self._revoked.setdefault(user, set()).add(permission)
        self._audit.log(user, "permission.revoke", permission, "ok")

    def get_level(self, user: str) -> int:
        """Nível atual do usuário (BASIC por padrão)."""
        return int(self._levels.get(user, Level.BASIC))

    def check(self, user: str, action: str, resource: str = "") -> bool:
        """Verifica se o usuário pode executar a ação (sem confirmação).

        Retorna False se a ação foi revogada ou se o nível é insuficiente.
        """
        if action in self._revoked.get(user, set()):
            self._audit.log(user, action, resource, "denied:revoked")
            return False
        allowed = self.get_level(user) >= required_level(action)
        self._audit.log(
            user, action, resource, "allowed" if allowed else "denied:level"
        )
        return allowed

    def request(
        self, user: str, action: str, resource: str = ""
    ) -> PermissionResponse:
        """Solicita permissão, sinalizando necessidade de confirmação.

        Ações sensíveis permitidas ainda exigem confirmação explícita do
        usuário antes de executar.
        """
        if action in self._revoked.get(user, set()):
            return PermissionResponse(False, "Permissão revogada")
        if self.get_level(user) < required_level(action):
            need = required_level(action)
            return PermissionResponse(
                False, f"Nível insuficiente (requer {need.name})"
            )
        if is_sensitive(action):
            return PermissionResponse(
                True, "Ação sensível: confirme para prosseguir",
                needs_confirmation=True,
            )
        return PermissionResponse(True, "Permitido")

    @property
    def audit(self) -> AuditLogger:
        """Acesso ao logger de auditoria subjacente."""
        return self._audit
