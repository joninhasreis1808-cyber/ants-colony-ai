"""Executor do Local Agent (9.18 · FASE 5 · 1ª capacidade: LEITURA).

Abre a PRIMEIRA capacidade real do corpo local — `CAN_READ_FILES` — pela porta
certa, com defesa em profundidade:

  grant assinado (capability_tokens) ─┐
  escopo do dono (`read_files`)       ├─ os quatro precisam passar; senão, recusa
  path_guard (whitelist de pastas)    │  honesta e auditada.
  capacidade explicitamente ABERTA    ─┘

Só a LEITURA está aberta; qualquer outra capacidade responde "ainda não aberta"
(o ROTEIRO manda abrir uma por vez). Nenhuma escrita/execução aqui.

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

# Capacidades já ABERTAS (uma por vez, com cautela). Leitura primeiro.
_OPEN = frozenset({"CAN_READ_FILES"})

# Trilha de auditoria (toda tentativa entra aqui — Regra: nada sem registro).
_AUDIT: list[dict] = []


def audit_log() -> list[dict]:
    """Cópia da trilha de auditoria das ações do corpo local."""
    return list(_AUDIT)


def _audit(capability: str, resource: str, outcome: str, reason: str = "") -> None:
    _AUDIT.append({"ts": time.time(), "capability": capability,
                   "resource": resource, "outcome": outcome, "reason": reason})


def execute_local(token: str, *, secret: Optional[bytes] = None,
                  seen: Optional[set] = None) -> dict[str, Any]:
    """Valida o grant assinado e executa a capacidade — só leitura, tudo gated.

    Devolve sempre um dict honesto: {ok, allowed, capability?, result?, reason?}.
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

    # CAN_READ_FILES → ferramenta gated do ToolRegistry (escopo + path_guard).
    from backend.tools.registry import get_tool_registry
    res = get_tool_registry().run("read_file", {"path": resource})
    outcome = "lido" if res.get("ok") else (
        "recusado" if res.get("allowed") is False else "erro")
    _audit(cap, resource, outcome, str(res.get("reason") or ""))
    return {"ok": bool(res.get("ok")), "allowed": res.get("allowed"),
            "capability": cap, "grant": grant.to_dict(),
            "result": res.get("result"), "reason": res.get("reason")}
