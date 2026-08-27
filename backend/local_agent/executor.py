"""Executor do Local Agent (9.18 · FASE 5 · 1ª capacidade: LEITURA).

Abre a PRIMEIRA capacidade real do corpo local — `CAN_READ_FILES` — pela porta
certa, com defesa em profundidade:

  grant assinado (capability_tokens) ─┐
  escopo do dono (`read_files`)       ├─ os quatro precisam passar; senão, recusa
  path_guard (whitelist de pastas)    │  honesta e auditada.
  capacidade explicitamente ABERTA    ─┘

LEITURA e ESCRITA estão abertas (a escrita é dry-run salvo confirm:true); qualquer
outra capacidade responde "ainda não aberta" (o ROTEIRO manda abrir uma por vez).
Nenhuma execução de comando/tela/input aqui.

Nota honesta de arquitetura: enquanto não existe o app nativo (Tauri), este
executor roda no servidor como PONTE de referência — lê o filesystem do próprio
container, sob todas as travas. Quando o Local Agent nativo existir, o mesmo
fluxo grant→verify→ler roda NO DISPOSITIVO. Isto prova o contrato de segurança
ponta a ponta sem dar ao servidor nenhum poder novo além da leitura já gated.
"""
from __future__ import annotations

import time
from typing import Any, Optional

from backend.local_agent.capability_tokens import verify_command

# Capacidades já ABERTAS (uma por vez, com cautela). Leitura e escrita gated.
_OPEN = frozenset({"CAN_READ_FILES", "CAN_WRITE_FILES"})

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
    """Valida o grant assinado e executa a capacidade aberta, tudo gated.

    `args` traz o payload por capacidade (escrita: {content, confirm}). Leitura o
    ignora. Devolve sempre um dict honesto: {ok, allowed, capability?, result?,
    reason?}.
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

    # Cada capacidade → ferramenta gated do ToolRegistry (escopo + path_guard;
    # escrita é dry-run salvo confirm:true). Grant assinado já validado acima.
    from backend.tools.registry import get_tool_registry
    a = args or {}
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
