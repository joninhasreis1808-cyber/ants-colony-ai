"""Computer Use controlado — o dispositivo sob permissão explícita.

Dá à colônia a capacidade de agir no dispositivo (ler/escrever arquivos,
listar diretórios, buscar, executar comandos), sempre sob permissão
explícita e com forte contenção: cada capacidade exige autorização (nível
de permissão adequado); comandos passam por uma whitelist; execução com
timeout e escopo de diretório; e toda ação vai para um log auditável.

Liberdade com responsabilidade: a IA age, mas o usuário vê e controla
tudo. Os handlers das capacidades vivem em `computer_use_handlers.py`.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from backend.action import computer_use_handlers as H
from backend.action.computer_use_handlers import Result


class Capability(str, Enum):
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    LIST_DIR = "list_dir"
    SEARCH_FILES = "search_files"
    EXECUTE_CMD = "execute_cmd"
    CLIPBOARD = "clipboard"


# Nível mínimo por capacidade (casa com permission_levels.Level).
_MIN_LEVEL = {
    Capability.READ_FILE: 3, Capability.LIST_DIR: 3,
    Capability.SEARCH_FILES: 3, Capability.CLIPBOARD: 3,
    Capability.WRITE_FILE: 4, Capability.EXECUTE_CMD: 4,
}


@dataclass
class Authorization:
    user: str
    capability: Capability
    granted: bool
    reason: str = ""


class ComputerUse:
    """Executa ações no dispositivo sob permissão, whitelist e escopo."""

    def __init__(
        self, scope_dir: str, permission_manager=None,
        audit_logger=None, timeout: float = 30.0,
    ) -> None:
        self._scope = Path(scope_dir).resolve()
        self._scope.mkdir(parents=True, exist_ok=True)
        self._pm = permission_manager
        self._audit = audit_logger
        self._timeout = timeout
        self._granted: set[tuple[str, Capability]] = set()

    def request_permission(
        self, user: str, capability: Capability
    ) -> Authorization:
        """Concede uma capacidade se o nível do usuário permitir."""
        min_level = _MIN_LEVEL.get(capability, 5)
        level = self._pm.get_level(user) if self._pm else 5
        ok = level >= min_level
        if ok:
            self._granted.add((user, capability))
        self._log(user, f"request:{capability.value}", ok)
        return Authorization(
            user, capability, ok,
            "" if ok else f"exige nível {min_level}, usuário tem {level}",
        )

    def revoke_permission(self, user: str, capability: Capability) -> None:
        """Revoga uma capacidade concedida."""
        self._granted.discard((user, capability))
        self._log(user, f"revoke:{capability.value}", True)

    def execute(
        self, user: str, capability: Capability, params: dict
    ) -> Result:
        """Executa uma capacidade autorizada, dentro do escopo e whitelist."""
        if (user, capability) not in self._granted:
            self._log(user, f"denied:{capability.value}", False)
            return Result(False, error="permissão não concedida")
        try:
            result = self._dispatch(capability, params)
        except Exception as exc:  # noqa: BLE001
            result = Result(False, error=str(exc))
        self._log(user, f"exec:{capability.value}", result.ok)
        return result

    def _dispatch(self, capability: Capability, params: dict) -> Result:
        if capability is Capability.READ_FILE:
            return H.read_file(self._scope, params)
        if capability is Capability.WRITE_FILE:
            return H.write_file(self._scope, params)
        if capability is Capability.LIST_DIR:
            return H.list_dir(self._scope, params)
        if capability is Capability.SEARCH_FILES:
            return H.search_files(self._scope, params)
        if capability is Capability.EXECUTE_CMD:
            return H.execute_cmd(self._scope, params, self._timeout)
        if capability is Capability.CLIPBOARD:
            return H.clipboard(self._scope, params)
        return Result(False, error="capacidade desconhecida")

    def _log(self, user: str, action: str, ok: bool) -> None:
        if self._audit is not None:
            try:
                self._audit.log(user, action, "computer_use",
                                "granted" if ok else "denied")
            except Exception:
                pass
