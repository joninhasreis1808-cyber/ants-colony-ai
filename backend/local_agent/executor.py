"""Executor do Local Agent (9.18 · FASE 5) — o portão de segurança do corpo local.

Duas classes de capacidade, tratadas de formas diferentes e honestas:

• ARQUIVO (`CAN_READ_FILES`, `CAN_WRITE_FILES`) — seguras de executar como PONTE de
  referência no servidor, atrás de todas as travas (grant assinado + escopo +
  path_guard; escrita é dry-run salvo confirm:true). Executadas via ToolRegistry.

• DISPOSITIVO (`CAN_SCREENSHOT`, `CAN_CONTROL_APP`, `CAN_RUN_COMMAND`) — só fazem
  sentido no app NATIVO. Aqui o executor apenas **VALIDA** toda a corrente de
  segurança (grant + escopo + allowlist de comandos + confirm) e devolve um
  **envelope autorizado**; **nunca executa** tela/app/comando no servidor. É o
  contrato completo, pronto para o Local Agent nativo plugar seus executores reais.

Defesa em profundidade: grant assinado → capacidade aberta → escopo do dono →
(comando: allowlist + confirm | arquivo: path_guard/dry-run). Qualquer capacidade
não aberta responde "ainda não aberta". Tudo auditado — nada sem registro.
"""
from __future__ import annotations

import time
from typing import Any, Optional

from backend.local_agent.capability_tokens import verify_command

# Capacidades de ARQUIVO: executadas (gated) como ponte de referência.
_FILE_CAPS = frozenset({"CAN_READ_FILES", "CAN_WRITE_FILES"})
# Capacidades de DISPOSITIVO: só validadas + delegadas ao agente nativo.
_DEVICE_CAPS = frozenset({"CAN_SCREENSHOT", "CAN_CONTROL_APP", "CAN_RUN_COMMAND",
                          "CAN_CONTROL_INPUT"})
_OPEN = _FILE_CAPS | _DEVICE_CAPS

# Capacidade de dispositivo → escopo do dono exigido (device_scopes).
_DEVICE_SCOPE = {
    "CAN_SCREENSHOT": "screen_capture",
    "CAN_CONTROL_APP": "run_apps",
    "CAN_RUN_COMMAND": "system_commands",
    "CAN_CONTROL_INPUT": "control_input",
}

# Trilha de auditoria (toda tentativa entra aqui — Regra: nada sem registro).
_AUDIT: list[dict] = []


def audit_log() -> list[dict]:
    """Cópia da trilha de auditoria das ações do corpo local."""
    return list(_AUDIT)


def _audit(capability: str, resource: str, outcome: str, reason: str = "") -> None:
    _AUDIT.append({"ts": time.time(), "capability": capability,
                   "resource": resource, "outcome": outcome, "reason": reason})


def execute_local(token: str, *, args: Optional[dict] = None,
                  secret: Optional[bytes] = None,
                  seen: Optional[set] = None) -> dict[str, Any]:
    """Valida o grant assinado e executa (arquivo) ou autoriza (dispositivo).

    `args` traz o payload por capacidade (escrita: {content, confirm}; comando:
    {command, confirm}). Devolve sempre um dict honesto.
    """
    ok, grant = verify_command(token, secret=secret, seen=seen)
    if not ok:
        _audit("?", "?", "negado", str(grant))
        return {"ok": False, "allowed": False, "reason": str(grant)}

    cap, resource = grant.capability, grant.resource
    if cap not in _OPEN:
        _audit(cap, resource, "recusado", "capacidade ainda não aberta")
        return {"ok": False, "allowed": False, "capability": cap,
                "reason": f"capacidade ainda não aberta: {cap} "
                          "(abertura uma por vez, com autorização)"}

    a = args or {}
    if cap in _FILE_CAPS:
        return _run_file(cap, resource, a, grant)
    return _authorize_device(cap, resource, a, grant)


def _run_file(cap: str, resource: str, a: dict, grant) -> dict[str, Any]:
    """Arquivo: executa via ToolRegistry (escopo + path_guard; dry-run na escrita)."""
    from backend.tools.registry import get_tool_registry
    if cap == "CAN_READ_FILES":
        tool, targs, ok_word = "read_file", {"path": resource}, "lido"
    else:  # CAN_WRITE_FILES
        tool = "write_file"
        targs = {"path": resource, "content": str(a.get("content", "")),
                 "confirm": bool(a.get("confirm"))}
        ok_word = "gravado" if a.get("confirm") else "prévia (dry-run)"
    res = get_tool_registry().run(tool, targs)
    outcome = ok_word if res.get("ok") else (
        "recusado" if res.get("allowed") is False else "erro")
    _audit(cap, resource, outcome, str(res.get("reason") or ""))
    return {"ok": bool(res.get("ok")), "allowed": res.get("allowed"),
            "capability": cap, "grant": grant.to_dict(),
            "result": res.get("result"), "reason": res.get("reason")}


def _authorize_device(cap: str, resource: str, a: dict, grant) -> dict[str, Any]:
    """Dispositivo: VALIDA a corrente e delega ao nativo — NUNCA executa aqui."""
    from backend.permissions.device_scopes import get_device_scopes
    from backend.local_agent.runtime import is_native, runtime_name

    scope = _DEVICE_SCOPE[cap]
    if not get_device_scopes().is_granted(scope):
        _audit(cap, resource, "recusado", f"escopo '{scope}' não concedido")
        return {"ok": False, "allowed": False, "capability": cap,
                "reason": f"escopo '{scope}' não concedido pelo dono"}

    argv = None
    if cap == "CAN_RUN_COMMAND":
        # Comando é o mais perigoso: allowlist explícita + confirm obrigatório.
        from backend.action.command_guard import CommandGuard
        command = a.get("command") or resource
        verdict = CommandGuard().check(command)
        if not verdict.get("allowed"):
            _audit(cap, str(command), "recusado", verdict.get("reason", ""))
            return {"ok": False, "allowed": False, "capability": cap,
                    "reason": verdict.get("reason", "comando não permitido"),
                    "argv": verdict.get("argv")}
        if not a.get("confirm"):
            _audit(cap, str(command), "recusado", "confirm obrigatório")
            return {"ok": False, "allowed": False, "capability": cap,
                    "reason": "comando exige confirm:true explícito do dono"}
        argv = verdict.get("argv")

    # Envelope AUTORIZADO — execução delegada ao Local Agent nativo. Não executado.
    _audit(cap, resource, "autorizado", f"runtime={runtime_name()}")
    env: dict[str, Any] = {
        "ok": True, "allowed": True, "authorized": True, "executed": False,
        "capability": cap, "grant": grant.to_dict(), "resource": resource,
        "runtime": runtime_name(), "native_available": is_native(),
        "note": "autorizado — execução delegada ao Local Agent nativo; "
                "o servidor NÃO age no dispositivo",
    }
    if argv is not None:
        env["argv"] = argv
    return env
