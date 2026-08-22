"""Executor de missão com FERRAMENTAS reais (9.12 · Passo 1) — o Manus de ponta a ponta.

Fecha o ciclo: o executor de missões (FASE B5) deixa de só "narrar" e passa a AGIR
chamando ferramentas do ToolRegistry (FASE D) — sempre pela porta gated
(capacidade + escopo + dry-run). Cada passo do plano pode estar ligado a uma
ferramenta; quando está, a colônia a executa de verdade e injeta o resultado real
na resposta. Quando a ferramenta é recusada (escopo não concedido), o passo
registra a recusa HONESTA e segue com o que dá — nunca inventa nem excede a
permissão do dono.

Também mantém a delegação à Pesquisa Profunda (rede) para as rotas de pesquisa,
como antes. Determinístico e seguro: `compute` é puro (sem escopo); as demais
ferramentas só agem com o escopo concedido.
"""
from __future__ import annotations

from typing import Any, Callable

# Ligações passo→ferramenta. args_of(goal, board) monta os argumentos.
# Extensível: novos passos (ex.: ação no dispositivo) entram aqui, sempre gated.
_BINDINGS: dict[str, tuple[str, Callable[[str, Any], dict]]] = {
    "resolver": ("compute", lambda goal, board: {"expression": goal}),
}


def make_tool_executor(goal: str, deep: bool, online: bool):
    """Executor real da missão: usa ferramentas gated + pesquisa profunda."""
    from backend.core import Task
    from backend.hivemind import deep_research
    from backend.memory.shared_memory import SharedMemory
    from backend.providers.local_provider import LocalProvider
    from backend.providers.router import ProviderRouter
    from backend.tools.registry import get_tool_registry

    cache: dict[str, Any] = {}
    registry = get_tool_registry()

    async def executor(node, board):
        nid = node.id

        # 1) Passo ligado a uma FERRAMENTA gated → executa pelo registro.
        if nid in _BINDINGS:
            tool_name, args_of = _BINDINGS[nid]
            res = registry.run(tool_name, args_of(board.goal, board))
            rec = {"tool": tool_name, "allowed": res.get("allowed"),
                   "ok": res.get("ok"), "reason": res.get("reason")}
            if res.get("ok") and isinstance(res.get("result"), dict) \
                    and res["result"].get("ok") and res["result"].get("answer") is not None:
                return True, str(res["result"]["answer"]), {"tool": rec}
            if res.get("allowed") is False:      # recusa honesta (sem escopo)
                return True, f"{node.description} — {tool_name} recusada: " \
                    f"{res.get('reason', '')}", {"tool": rec}
            # ferramenta não se aplica aqui (ex.: não é cálculo) → segue o fluxo

        # 2) Rotas de pesquisa: delega à Pesquisa Profunda (rede real).
        if nid in ("explorar", "buscar") and online:
            try:
                t = Task(goal=board.goal)
                scratch = SharedMemory(":memory:")
                scratch.save_task(t)
                await deep_research.run(t, scratch, None,
                                        ProviderRouter([LocalProvider()]))
                cache["answer"] = (t.result or {}).get("answer", "")
                cache["sources"] = (t.result or {}).get("sources", [])
                n = len(cache.get("sources") or [])
                ev = (t.result or {}).get("deep_research", {}).get("evidence_count", n)
                return True, f"{node.description} — {n} fonte(s)", {
                    "n": n, "discovery": {"sources": n, "evidence": ev}}
            except Exception as exc:             # noqa: BLE001
                return True, f"{node.description} — sem rede útil ({exc})", {}

        # 3) Síntese: injeta a resposta real coletada na pesquisa.
        if nid in ("sintetizar", "responder", "resolver") and cache.get("answer"):
            return True, cache["answer"], {"sources": cache.get("sources", [])}

        # 4) Demais passos: orquestração honesta.
        return True, f"{node.description} — concluído", {}

    return executor
