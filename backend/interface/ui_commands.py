"""UI Command API tipada (9.19 · FASE 5b) — a Mente comanda a UI, não edita HTML.

O Relatório Mestre pede uma "UI Command API tipada (IA não edita HTML)": o
front já tem o `web/js/ui_kernel.js` com um conjunto FECHADO de ações; faltava o
**contrato do lado do backend**, para a Mente Colmeia emitir SÓ comandos válidos
e tipados — nunca HTML arbitrário. Este módulo é essa fonte única: o mesmo
vocabulário do kernel, validado aqui antes de virar um evento `ants:ui`.

Defesa: `build()` valida por ação e recusa o desconhecido/malformado; o que sai
daqui é sempre um comando que o kernel sabe aplicar. Puro stdlib, sem I/O.
"""
from __future__ import annotations

from typing import Any

# Conjunto FECHADO de ações — espelha exatamente `ACTIONS` do ui_kernel.js.
ACTIONS = frozenset({
    "highlight", "update_progress", "open_section", "close_section",
    "append_timeline", "set_state", "toast",
})

# Estados válidos — espelham a máquina do colony_state / STATES do kernel.
STATES = frozenset({
    "dormant", "observing", "exploring", "building",
    "verifying", "learning", "defending", "executing",
})

# Alvos válidos de open_section (mesmo mapa do kernel).
_SECTIONS = frozenset({"console", "missions", "registro", "timeline"})


class UICommandError(ValueError):
    """Comando de UI inválido — recusado antes de sair para a interface."""


def validate(cmd: dict[str, Any]) -> tuple[bool, str]:
    """Veredito auditável: este comando é aceito pelo kernel? Por quê (não)?"""
    if not isinstance(cmd, dict):
        return False, "comando não é objeto"
    action = cmd.get("action")
    if action not in ACTIONS:
        return False, f"ação desconhecida: {action!r}"
    if action == "update_progress":
        p = cmd.get("progress")
        if not isinstance(p, (int, float)) or not (0 <= p <= 100):
            return False, "progress deve estar em [0,100]"
    elif action == "set_state":
        if cmd.get("target") not in STATES:
            return False, f"estado inválido: {cmd.get('target')!r}"
    elif action == "open_section":
        if cmd.get("target") not in _SECTIONS:
            return False, f"seção inválida: {cmd.get('target')!r}"
    elif action == "toast":
        if not str(cmd.get("text") or cmd.get("message") or "").strip():
            return False, "toast sem texto"
    elif action == "append_timeline":
        if not str(cmd.get("text") or "").strip():
            return False, "append_timeline sem texto"
    return True, "ok"


def build(action: str, **params: Any) -> dict[str, Any]:
    """Monta um comando de UI tipado e VALIDADO (levanta se inválido).

    É o único caminho recomendado para a Mente falar com a UI: garante que só
    comandos do conjunto fechado, bem-formados, chegam ao kernel.
    """
    cmd = {"action": action, **params}
    ok, reason = validate(cmd)
    if not ok:
        raise UICommandError(reason)
    return cmd


# Açúcares tipados (descoberta e uso seguros pela Mente) ---------------------

def highlight(target: str, reason: str = "") -> dict[str, Any]:
    return build("highlight", target=target, reason=reason)


def update_progress(progress: float) -> dict[str, Any]:
    return build("update_progress", progress=progress)


def open_section(target: str) -> dict[str, Any]:
    return build("open_section", target=target)


def close_section() -> dict[str, Any]:
    return build("close_section")


def append_timeline(text: str, caste: str = "", ts: float | None = None) -> dict[str, Any]:
    return build("append_timeline", text=text, caste=caste, ts=ts)


def set_state(target: str) -> dict[str, Any]:
    return build("set_state", target=target)


def toast(text: str) -> dict[str, Any]:
    return build("toast", text=text)
