"""Guarda de comandos de sistema (8.0 · B.8 + B.10).

Regra: **whitelist explícita, nunca blacklist.** Só comandos aprovados rodam,
sempre como lista de argumentos (sem shell interpolado), com timeout. Bloqueia
qualquer tentativa de escalonamento de privilégio (sudo/runas/UAC, desativar
antivírus/firewall) — se a colônia "descobrir" um caminho, recusa e reporta.
"""
from __future__ import annotations

import shlex

# Binários permitidos por padrão (leitura/inspeção — nada destrutivo aqui).
_WHITELIST = {
    "echo", "ls", "cat", "pwd", "whoami", "date", "df", "du", "uname",
    "hostname", "python", "python3", "pip", "node", "npm", "git",
}
# Tokens de escalonamento/privilégio — recusados SEMPRE (§B.10).
_ESCALATION = {
    "sudo", "su", "runas", "doas", "pkexec", "chmod", "chown", "setcap",
    "defender", "netsh", "firewall", "gpupdate", "reg", "bcdedit",
}
_DANGER_SUBSTR = ("rm -rf", "mkfs", "dd if=", ":(){", "format ", "> /dev/sd")


class CommandGuard:
    """Valida comandos contra whitelist e anti-escalonamento."""

    def __init__(self, whitelist: set[str] | None = None) -> None:
        self._whitelist = set(whitelist) if whitelist else set(_WHITELIST)

    def allow_binary(self, name: str) -> None:
        self._whitelist.add(name)

    def to_argv(self, command: str) -> list[str]:
        """Divide em lista de argumentos (sem shell). Nunca interpola shell."""
        return shlex.split(command, posix=True)

    def check(self, command: str | list[str]) -> dict:
        """Veredito auditável: pode rodar? Por quê (não)?"""
        argv = command if isinstance(command, list) else self.to_argv(command)
        if not argv:
            return {"allowed": False, "reason": "comando vazio", "argv": []}
        raw = " ".join(argv).lower()
        binary = argv[0].split("/")[-1].split("\\")[-1].lower()
        if any(tok in raw.split() for tok in _ESCALATION) or binary in _ESCALATION:
            return {"allowed": False, "argv": argv,
                    "reason": "escalonamento de privilégio recusado (B.10)",
                    "escalation": True}
        if any(sub in raw for sub in _DANGER_SUBSTR):
            return {"allowed": False, "argv": argv,
                    "reason": "padrão destrutivo bloqueado"}
        if binary not in self._whitelist:
            return {"allowed": False, "argv": argv,
                    "reason": f"binário '{binary}' fora da whitelist"}
        return {"allowed": True, "argv": argv, "reason": "na whitelist"}

    def is_escalation(self, command: str | list[str]) -> bool:
        return bool(self.check(command).get("escalation"))


_INSTANCE: CommandGuard | None = None


def get_command_guard() -> CommandGuard:
    """Singleton de processo da guarda de comandos."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = CommandGuard()
    return _INSTANCE
