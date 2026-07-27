"""Fluxo de ação (8.1 · B) — liga o comando às Operárias do 8.0.

interpretar → checar permissão → gerar plano → (aprovar) → executar → verificar
→ relatar. Toda a segurança do 8.0 permanece: sem escopo, pede a permissão (não
"não sei"); ações destrutivas exigem aprovação; tudo é auditado.
"""
from __future__ import annotations

import itertools
from typing import Any

_IDS = itertools.count(1)
_PENDING: dict[str, Any] = {}

_VERB_PT = {
    "list": "listar os arquivos", "search": "buscar arquivos",
    "open": "abrir", "close": "fechar", "move": "mover", "rename": "renomear",
    "delete": "apagar", "copy": "copiar", "organize": "organizar a pasta",
    "click": "clicar", "type": "digitar", "screenshot": "capturar a tela",
}


def _steps(intent) -> list[str]:
    alvo = intent.target or "(alvo)"
    return [f"Verificar permissão do escopo '{intent.scope}'.",
            f"{_VERB_PT.get(intent.verb, intent.verb).capitalize()}: {alvo}.",
            "Verificar o resultado e registrar na auditoria."]


class ActionFlow:
    """Orquestra o comando de ação do chat até a execução verificada."""

    def plan(self, message: str) -> dict:
        """Interpreta e devolve: pede permissão, ou plano para aprovação."""
        from backend.action.action_interpreter import get_action_interpreter
        from backend.permissions.device_scopes import get_device_scopes
        from backend.permissions.path_guard import get_path_guard, is_blacklisted
        intent = get_action_interpreter().interpret(message)
        if not intent:
            return {"ok": False, "intent": None,
                    "answer": "Não reconheci uma ação de dispositivo nessa mensagem."}
        needs_scope = not get_device_scopes().is_granted(intent.scope)
        # Ações de arquivo/pasta também exigem a pasta autorizada (whitelist).
        path_target = intent.target if intent.target_type in ("folder", "file") else ""
        if path_target and is_blacklisted(path_target):
            return {"ok": True, "intent": intent.to_dict(),
                    "answer": f"Recusado: '{path_target}' é um caminho protegido "
                              "(blacklist imutável) — não posso tocar nele."}
        needs_path = bool(path_target) and not get_path_guard().is_allowed(path_target)
        if needs_scope or needs_path:
            partes = []
            if needs_scope:
                partes.append(f"a permissão '{intent.scope}'")
            if needs_path:
                partes.append(f"autorizar a pasta {path_target}")
            return {"ok": True, "needs_permission": True, "scope": intent.scope,
                    "intent": intent.to_dict(),
                    "grant_scope": intent.scope if needs_scope else None,
                    "grant_path": path_target if needs_path else None,
                    "answer": (f"Para {_VERB_PT.get(intent.verb, intent.verb)} eu "
                               "preciso de " + " e ".join(partes) +
                               ". Clique para conceder e repita o comando.")}
        pid = f"act_{next(_IDS)}"
        _PENDING[pid] = intent
        steps = _steps(intent)
        return {"ok": True, "needs_approval": True, "plan_id": pid,
                "steps": steps, "intent": intent.to_dict(),
                "answer": "Plano de ação:\n" + "\n".join(
                    f"{i+1}. {s}" for i, s in enumerate(steps)) +
                "\n\nAprovar para executar."}

    def execute(self, plan_id: str) -> dict:
        """Executa um plano aprovado via as Operárias, verificando o efeito."""
        intent = _PENDING.pop(plan_id, None)
        if intent is None:
            return {"ok": False, "answer": "Plano não encontrado ou já usado."}
        result = self._dispatch(intent)
        ok = result.get("executed") or ("items" in result)
        return {"ok": True, "executed": bool(ok), "intent": intent.to_dict(),
                "result": result, "answer": self._summary(intent, result)}

    def cancel(self, plan_id: str) -> dict:
        _PENDING.pop(plan_id, None)
        return {"ok": True, "answer": "Ação cancelada."}

    # ---- despacho às Operárias reais do 8.0 ----
    def _dispatch(self, intent) -> dict:
        from backend.action.device_apps import get_device_apps
        from backend.action.device_files import DeviceFiles
        v, t = intent.verb, intent.target
        if intent.target_type == "url":
            return get_device_apps().open_url(t)
        if v == "open":
            return get_device_apps().open_app(t)
        if v == "list":
            r = DeviceFiles().list_dir(t)
            if r.get("executed"):
                r["items"] = r.get("result", [])
            return r
        if v == "search":
            return DeviceFiles().search(t, intent.args.get("q", ""))
        if v == "delete":
            return DeviceFiles().delete(t, confirmed=True)
        if v == "move":
            return DeviceFiles().move(t, intent.args.get("dst", t), confirmed=True)
        if v in ("click", "type", "screenshot"):
            from backend.action.input_controller import InputController
            ic = InputController()
            return ic.click(0, 0) if v == "click" else ic.type_text(t)
        return {"executed": False, "note": f"verbo '{v}' ainda não conectado"}

    def _summary(self, intent, result: dict) -> str:
        if result.get("denied"):
            return "Recusado: " + result.get("reason", "sem permissão/whitelist")
        if result.get("declared"):
            return ("Isto exige o app nativo para executar no dispositivo "
                    "(no modo local é apenas declarado). " + result.get("note", ""))
        if "items" in result:
            items = result["items"]
            return (f"Listei {len(items)} item(ns): " +
                    ", ".join(map(str, items[:20])) + ("…" if len(items) > 20 else ""))
        if result.get("executed"):
            return "Feito: " + _VERB_PT.get(intent.verb, intent.verb) + " concluído."
        return "Não consegui concluir: " + str(result.get("error", "motivo desconhecido"))


_INSTANCE: ActionFlow | None = None


def get_action_flow() -> ActionFlow:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = ActionFlow()
    return _INSTANCE
