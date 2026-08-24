"""Executor de missão com FERRAMENTAS reais (9.12 · Passo 1; 9.15 · escrita gated).

Fecha o ciclo: o executor de missões (FASE B5) deixa de só "narrar" e passa a AGIR
chamando ferramentas do ToolRegistry (FASE D) — sempre pela porta gated
(capacidade + escopo + dry-run). Cada passo do plano pode estar ligado a uma
ferramenta; quando está, a colônia a executa de verdade e injeta o resultado real
na resposta. Quando a ferramenta é recusada (escopo não concedido), o passo
registra a recusa HONESTA e segue com o que dá — nunca inventa nem excede a
permissão do dono.

Poderes de ação (Manus):
  • `resolver` → `compute` (cálculo exato, puro, sem escopo);
  • `explorar`/`buscar` (online) → Pesquisa Profunda (rede real);
  • `agir` (rota device_action) → `write_file` GATED: escreve um arquivo quando o
    objetivo pede ("escreva … no arquivo …"). Dupla trava: exige o escopo
    `write_files` E `confirm=true`; sem os dois, faz uma PRÉVIA (dry-run) honesta,
    nunca grava sozinha, e o path_guard barra caminhos proibidos mesmo autorizado.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Optional

# Ligações passo→ferramenta simples. args_of(goal, board) monta os argumentos.
_BINDINGS: dict[str, tuple[str, Callable[[str, Any], dict]]] = {
    "resolver": ("compute", lambda goal, board: {"expression": goal}),
}

# Extensões que denunciam um caminho de arquivo num objetivo em linguagem natural.
_PATH_RE = re.compile(r"(/?[\w.\-/]+\.[A-Za-z0-9]{1,6})")
_QUOTE_RE = re.compile(r"[\"“'«]([^\"”'»]{1,20000})[\"”'»]")
_VERB_CONTENT_RE = re.compile(
    r"(?:escrev\w*|grav\w*|salv\w*|conte[uú]do|texto)[:\s]+(.+?)"
    r"(?:\s+(?:no|na|em|para|dentro)\s+|\s+arquivo\b|$)", re.I)


def parse_write_request(goal: str) -> Optional[dict]:
    """Extrai {path, content} de um objetivo de escrita, ou None se não houver
    caminho reconhecível. Determinístico; heurística honesta (não adivinha)."""
    text = goal or ""

    # 1) conteúdo: primeiro trecho entre aspas tem prioridade.
    content = None
    mq = _QUOTE_RE.search(text)
    scan = text
    if mq:
        content = mq.group(1)
        scan = text[:mq.start()] + " " + text[mq.end():]   # tira as aspas do scan

    # 2) caminho: token com extensão; senão "arquivo X".
    path = None
    mp = _PATH_RE.search(scan)
    if mp:
        path = mp.group(1)
    else:
        ma = re.search(r"arquivo\s+([\w.\-/]+)", scan, re.I)
        if ma:
            path = ma.group(1)
    if not path:
        return None

    # 3) conteúdo sem aspas: pega o trecho após o verbo de escrita.
    if content is None:
        mv = _VERB_CONTENT_RE.search(text)
        content = mv.group(1).strip() if mv else ""
    return {"path": path, "content": content}


def make_tool_executor(goal: str, deep: bool, online: bool,
                       confirm: bool = False):
    """Executor real da missão: usa ferramentas gated + pesquisa profunda.

    `confirm` (do dono) libera a escrita de verdade; sem ele, a escrita é prévia."""
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

        # 2) AÇÃO REAL: escrever arquivo (rota device_action, passo 'agir'). Gated.
        if nid == "agir":
            parsed = parse_write_request(board.goal)
            if parsed:
                args = dict(parsed, confirm=bool(confirm))
                res = registry.run("write_file", args)
                r = res.get("result") or {}
                rec = {"tool": "write_file", "allowed": res.get("allowed"),
                       "ok": res.get("ok"), "reason": res.get("reason"),
                       "path": parsed["path"], "confirm": bool(confirm)}
                if res.get("allowed") is False:          # sem escopo/caminho barrado
                    msg = f"escrita recusada: {res.get('reason', '')}"
                elif res.get("ok") and r.get("written"):
                    msg = f"arquivo gravado: {r['path']} ({r.get('bytes', 0)} bytes)"
                elif res.get("ok") and r.get("dry_run"):
                    msg = (f"prévia — escreveria {r['path']} "
                           f"({r.get('bytes', 0)} bytes); envie confirm para gravar")
                else:
                    msg = f"escrita não concluída: {res.get('reason', r)}"
                cache["action"] = msg                    # vira a resposta final
                return True, msg, {"tool": rec}
            # sem caminho reconhecível → orquestração honesta (não inventa)

        # 2b) 'confirmar' da rota device_action ecoa o desfecho real da ação.
        if nid == "confirmar" and cache.get("action"):
            return True, cache["action"], {}

        # 3) Rotas de pesquisa: delega à Pesquisa Profunda (rede real).
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

        # 4) Síntese: injeta a resposta real coletada na pesquisa.
        if nid in ("sintetizar", "responder", "resolver") and cache.get("answer"):
            return True, cache["answer"], {"sources": cache.get("sources", [])}

        # 5) Demais passos: orquestração honesta.
        return True, f"{node.description} — concluído", {}

    return executor
