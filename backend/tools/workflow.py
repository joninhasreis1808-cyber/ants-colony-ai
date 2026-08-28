"""Motor de Fluxos nativo (9.20 · Passo 2) — o "n8n" da Mente Colmeia.

Em vez de alugar um orquestrador externo (n8n hospedado), a colônia ganha o mesmo
alcance NATIVO e soberano: um **fluxo** é uma sequência de passos, cada passo uma
ferramenta do `ToolRegistry` com argumentos que podem referenciar **saídas de
passos anteriores** e **segredos do cofre** (por nome, resolvidos em runtime —
nunca guardados no fluxo). Como tudo passa pelo Registry, TODAS as travas já
valem (capacidade + escopo + path_guard/command_guard/dry-run). É o n8n e mais:
unificado à cognição, offline, custo zero, auditável.

Referências nos argumentos (strings):
  "$secret.NOME"    → valor do segredo NOME no Secret Vault (resolvido, não logado)
  "$steps.ID.chave" → campo do resultado do passo ID (encadeamento de dados)
  "$ctx.chave"      → valor do contexto passado ao run()
Qualquer outra string passa intacta. Puro stdlib.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class WorkflowStep:
    """Um passo do fluxo: uma ferramenta + argumentos (com referências)."""

    id: str
    tool: str
    args: dict[str, Any] = field(default_factory=dict)
    bind: Optional[str] = None      # nome sob o qual guardar o resultado (default: id)

    def to_dict(self) -> dict[str, Any]:
        # Só o TEMPLATE dos args (com $refs) — nunca valores resolvidos/segredos.
        return {"id": self.id, "tool": self.tool, "args": self.args,
                "bind": self.bind or self.id}


@dataclass
class Workflow:
    """Um fluxo nomeado: passos em ordem, com política de erro."""

    name: str
    steps: list[WorkflowStep] = field(default_factory=list)
    stop_on_error: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "stop_on_error": self.stop_on_error,
                "steps": [s.to_dict() for s in self.steps]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Workflow":
        steps = [WorkflowStep(id=s["id"], tool=s["tool"],
                              args=dict(s.get("args") or {}), bind=s.get("bind"))
                 for s in data.get("steps") or []]
        return cls(name=data.get("name", "fluxo"), steps=steps,
                   stop_on_error=bool(data.get("stop_on_error", True)))


class _SecretMissing(KeyError):
    """Segredo referenciado por um passo não existe no cofre."""


class WorkflowEngine:
    """Executa fluxos passo a passo pelo ToolRegistry, com segredos do cofre."""

    def __init__(self, registry: Any = None, vault: Any = None) -> None:
        self._registry = registry
        self._vault = vault

    def _reg(self):
        if self._registry is None:
            from backend.tools.registry import get_tool_registry
            self._registry = get_tool_registry()
        return self._registry

    def _vlt(self):
        if self._vault is None:
            from backend.security.secret_vault import get_secret_vault
            self._vault = get_secret_vault()
        return self._vault

    # -- resolução de referências ------------------------------------------
    def _resolve(self, value: Any, results: dict, context: dict) -> Any:
        if isinstance(value, dict):
            return {k: self._resolve(v, results, context) for k, v in value.items()}
        if isinstance(value, list):
            return [self._resolve(v, results, context) for v in value]
        if isinstance(value, str):
            return self._resolve_str(value, results, context)
        return value

    def _resolve_str(self, s: str, results: dict, context: dict) -> Any:
        if s.startswith("$secret."):
            name = s[len("$secret."):]
            val = self._vlt().get(name)
            if val is None:
                raise _SecretMissing(name)
            return val.decode("utf-8")
        if s.startswith("$steps."):
            parts = s[len("$steps."):].split(".")
            cur: Any = results.get(parts[0])
            for p in parts[1:]:
                cur = cur.get(p) if isinstance(cur, dict) else None
            return cur
        if s.startswith("$ctx."):
            return (context or {}).get(s[len("$ctx."):])
        return s

    # -- execução -----------------------------------------------------------
    def run(self, wf: Workflow, context: Optional[dict] = None) -> dict[str, Any]:
        """Roda o fluxo. O registro NUNCA inclui args resolvidos nem segredos."""
        results: dict[str, Any] = {}
        record: list[dict[str, Any]] = []
        reg = self._reg()
        for step in wf.steps:
            try:
                args = self._resolve(step.args, results, context or {})
            except _SecretMissing as miss:
                record.append({"id": step.id, "tool": step.tool, "ok": False,
                               "allowed": False,
                               "reason": f"segredo ausente no cofre: {miss.args[0]}"})
                if wf.stop_on_error:
                    return self._fail(wf, record, step.id)
                continue
            res = reg.run(step.tool, args)
            results[step.bind or step.id] = res.get("result")
            record.append({"id": step.id, "tool": step.tool,
                           "ok": bool(res.get("ok")),
                           "allowed": res.get("allowed"),
                           "reason": res.get("reason")})
            if wf.stop_on_error and not res.get("ok"):
                return self._fail(wf, record, step.id)
        return {"workflow": wf.name, "ok": True, "steps": record,
                "outputs": results}

    @staticmethod
    def _fail(wf: Workflow, record: list, failed_at: str) -> dict[str, Any]:
        return {"workflow": wf.name, "ok": False, "steps": record,
                "failed_at": failed_at}


_INSTANCE: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Singleton de processo do motor de fluxos."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = WorkflowEngine()
    return _INSTANCE
