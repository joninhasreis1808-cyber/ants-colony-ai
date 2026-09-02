"""Pesquisa Profunda (9.5 · Fase B) — a colônia investiga um tema em ETAPAS.

Não é uma busca só: a Rainha (córtex) quebra o tema em sub-perguntas, as
Exploradoras pesquisam cada uma pela cascata real, as Operárias compilam e
deduplicam fontes, os Soldados checam suficiência, e a Rainha sintetiza (córtex
ou compositor de regras). Cada passo emite um EVENTO REAL — a Câmera ao Vivo
mostra o trajeto mais fundo. Offline-first: sem web/córtex, declara limitação
honesta (Regra 6), nunca inventa.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

_PREFIX = re.compile(
    r"^\s*(pesquis(?:e|ar|a)\s+(?:a\s+fundo|profund[ao]?)|pesquisa\s+profunda"
    r"|investigu?e?\s+a\s+fundo)\s+(sobre\s+|o\s+tema\s+)?", re.I)


def _topic(goal: str) -> str:
    return _PREFIX.sub("", goal or "").strip().rstrip("?.") or (goal or "").strip()


def _domain(url: str) -> str:
    try:
        return urlparse(url).hostname or ""
    except Exception:  # noqa: BLE001
        return ""


async def run(task: Any, memory: Any, bus: Any, router: Any) -> None:
    """Executa a pesquisa profunda, emitindo eventos por casta."""
    from backend.cognition.reasoner import backend_name, get_reasoner
    from backend.cognitive.response_composer import get_composer
    from backend.core import BotEvent, Phase, TaskStatus

    reasoner, composer = get_reasoner(), get_composer()
    topic = _topic(task.goal)

    async def emit(bot: str, phase: Any, msg: str, data: dict | None = None) -> None:
        ev = BotEvent(task_id=task.id, bot=bot, phase=phase, message=msg, data=data or {})
        memory.add_event(ev)
        if bus is not None:
            await bus.publish(task.id, ev.to_dict())

    # 1) Rainha planeja (córtex quebra em sub-perguntas)
    await emit("rainha", Phase.PLAN,
               f"Mente Colmeia planejou a pesquisa profunda (córtex: {backend_name()})")
    subs = await reasoner.plan_subqueries(topic, 4)
    await emit("rainha", Phase.PLAN, f"{len(subs)} sub-perguntas definidas",
               {"subqueries": subs})

    # 2) Exploradoras pesquisam cada sub-pergunta pela cascata real
    evidence: list[str] = []
    sources: list[dict] = []
    seen_urls: set[str] = set()
    attempts_all: list[str] = []
    for idx, sq in enumerate(subs, 1):
        await emit("exploradoras", Phase.DO,
                   f"Pesquisando ({idx}/{len(subs)}): {sq}", {"query": sq})
        try:
            results, attempts = await router.search(sq, limit=4)
        except Exception:  # noqa: BLE001 - busca falhou (ex.: 403 no sandbox)
            results, attempts = [], []
        attempts_all += attempts
        for r in results:
            if r.url and r.url in seen_urls:
                continue                      # dedup por URL
            if r.url:
                seen_urls.add(r.url)
            evidence.append(r.snippet or r.title or "")
            sources.append({"title": r.title, "url": r.url, "snippet": r.snippet})
        await emit("exploradoras", Phase.CHECK,
                   f"{len(results)} fonte(s) para a sub-pergunta {idx}", {"n": len(results)})

    # 3) Operárias compilam e deduplicam por domínio
    domains: list[str] = []
    for s in sources:
        d = _domain(s.get("url", ""))
        if d and d not in domains:
            domains.append(d)
    await emit("operarias", Phase.DO,
               f"Compilou {len(sources)} fonte(s) de {len(domains)} domínio(s)",
               {"domains": domains})

    # 4) Soldados verificam suficiência (honestidade)
    enough = len([e for e in evidence if e]) >= 2
    await emit("soldados", Phase.CHECK,
               "Evidência suficiente para sintetizar" if enough
               else "Evidência insuficiente — a colônia será honesta")

    # 5) Rainha sintetiza (córtex; senão compositor; senão limitação honesta)
    answer, source_kind, conf = None, "web_search", 0.9
    cortex_use = None
    if enough:
        # B6: a sintese do cortex externo passa pela GUARDA antes de virar
        # resposta. Ela pode refinar o texto; nao pode acrescentar fato. Numero
        # que nao esta em nenhuma evidencia derruba a sintese inteira, e a
        # colonia volta para a composicao deterministica.
        from backend.cognition.cortex_guard import guarded_synthesis
        syn = await reasoner.synthesize(topic, evidence)
        aprovada, cortex_use = guarded_synthesis(syn, evidence)
        base = aprovada or ". ".join(e for e in evidence[:3] if e)
        answer = composer.web(base, len(sources), domains)
    if not answer:
        answer = composer.limitation(
            "a busca web não trouxe evidências neste ambiente (na sua máquina, "
            "com rede, a colônia pesquisa de verdade)")
        source_kind, conf = "none", 0.2
    await emit("rainha", Phase.ACT,
               "Síntese pronta" if enough else "Declarou limitação honesta",
               {"reasoning_backend": backend_name()})

    web_status = ("web: 200 ok" if sources else
                  ("web: bloqueado/sem resultado" if attempts_all else "web: nao tentado"))
    task.result = {
        "answer": answer, "confidence": conf, "sources": sources, "learning": {},
        "provenance": {
            "source": source_kind, "cached": False, "web": web_status,
            "web_attempts": attempts_all, "urls": [s["url"] for s in sources],
            "confidence": conf,
            "castes": ["rainha", "exploradoras", "operarias", "soldados"],
            "gaps": [] if enough else ["evidência externa insuficiente"],
            "subqueries": subs, "reasoning_backend": backend_name(),
            "cortex": cortex_use.to_dict() if cortex_use else None,
        },
        "trace": {
            "bots": [{"bot": "rainha", "ok": True, "did": ["planejou e sintetizou"]},
                     {"bot": "exploradoras", "ok": bool(sources),
                      "did": [f"pesquisou {len(subs)} sub-perguntas"]},
                     {"bot": "operarias", "ok": True, "did": ["compilou e deduplicou"]},
                     {"bot": "soldados", "ok": True, "did": ["verificou suficiência"]}],
            "errors": [], "learnings": [], "source": source_kind,
            "conclusion": answer,
        },
        "deep_research": {"topic": topic, "subqueries": subs,
                          "evidence_count": len([e for e in evidence if e]),
                          "domains": domains, "backend": backend_name()},
    }
    task.touch(TaskStatus.DONE)
    memory.save_task(task)
    if bus is not None:
        await bus.close(task.id)
