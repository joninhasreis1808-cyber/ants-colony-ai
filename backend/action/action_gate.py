"""Gate central de ações de device (8.0 · B.4 + B.5 + B.9).

Toda ação real passa por aqui ANTES de executar. Ordem de segurança:
1. botão de pânico engajado → recusa tudo;
2. escopo concedido? (nenhum por padrão);
3. caminho dentro da whitelist / fora da blacklist (ações de arquivo);
4. comando na whitelist e sem escalonamento (ações de sistema);
5. guarda imunológica (`analyze_threat`) — `dangerous` reforça confirmação;
6. conteúdo externo com injeção nunca origina ação destrutiva sem humano;
7. ação destrutiva → exige confirmação mostrando o que acontecerá.

Padrão de fábrica: **Observar → Aprovar → Executar**. Nada irreversível sem
confirmação explícita, mesmo em modo autônomo.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Ações irreversíveis/destrutivas — sempre exigem confirmação humana (§B.5).
DESTRUCTIVE = {"delete", "overwrite", "move_bulk", "install",
               "system_command", "kill_process"}
# Escopo exigido por tipo de ação.
_SCOPE_OF = {
    "read": "read_files", "list": "read_files", "search": "read_files",
    "write": "write_files", "create": "write_files", "move": "write_files",
    "copy": "write_files", "rename": "write_files", "delete": "write_files",
    "overwrite": "write_files", "move_bulk": "write_files",
    "open_app": "run_apps", "kill_process": "run_apps", "install": "run_apps",
    "click": "control_input", "type": "control_input", "press_key": "control_input",
    "screenshot": "screen_capture", "system_command": "system_commands",
}


@dataclass
class Decision:
    """Veredito auditável de uma ação proposta."""

    allowed: bool
    needs_confirmation: bool
    reason: str
    scope: str = ""
    threat: str = "safe"
    injection: bool = False
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class ActionGate:
    """Decide se uma ação pode executar, precisa de OK, ou é recusada."""

    def evaluate(self, action: str, target: str = "",
                 external_content: str | None = None) -> Decision:
        from backend.action.command_guard import get_command_guard
        from backend.permissions.device_scopes import get_device_scopes
        from backend.permissions.path_guard import get_path_guard
        from backend.security.immune_system import ImmuneSystem, ThreatLevel
        from backend.security.panic import get_panic

        scope = _SCOPE_OF.get(action, "")
        if get_panic().is_engaged():
            return Decision(False, False, "botão de pânico engajado", scope)
        if not scope:
            return Decision(False, False, f"ação desconhecida: {action}")
        if not get_device_scopes().is_granted(scope):
            return Decision(False, False, f"escopo '{scope}' não concedido", scope)
        # Ações de arquivo: caminho precisa estar autorizado e fora da blacklist.
        if scope in ("read_files", "write_files") and target:
            verdict = get_path_guard().check(target)
            if not verdict["allowed"]:
                return Decision(False, False, verdict["reason"], scope,
                                details=verdict)
        # Ações de sistema: comando na whitelist e sem escalonamento.
        if action == "system_command" and target:
            cg = get_command_guard().check(target)
            if not cg["allowed"]:
                return Decision(False, False, cg["reason"], scope, details=cg)
        # Guarda imunológica.
        level = ImmuneSystem().analyze_threat(f"{action} {target}")
        threat = level.value if isinstance(level, ThreatLevel) else str(level)
        # Conteúdo externo: injeção nunca origina ação destrutiva sozinha.
        injection = False
        if external_content:
            from backend.security.content_sanitizer import get_sanitizer
            injection = get_sanitizer().is_injection(external_content)
        destructive = action in DESTRUCTIVE
        if injection and destructive:
            return Decision(False, False,
                            "conteúdo externo com injeção não pode originar "
                            "ação destrutiva", scope, threat, injection=True)
        # Ação destrutiva ou ameaça → precisa de confirmação humana explícita.
        if destructive or threat in ("suspicious", "dangerous"):
            return Decision(True, True,
                            "ação sensível — requer confirmação", scope, threat,
                            injection=injection)
        return Decision(True, False, "liberado", scope, threat,
                        injection=injection)


_INSTANCE: ActionGate | None = None


def get_action_gate() -> ActionGate:
    """Singleton de processo do gate de ações."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = ActionGate()
    return _INSTANCE
