"""Hivemind 2.0 — o orquestrador da mente colmeia.

Recebe uma tarefa, recruta os bots adequados e os executa em cadeia,
cada um lendo e escrevendo no mesmo contexto compartilhado (blackboard).
Eventos são publicados no EventBus em tempo real para o streaming /live.

O ciclo de cada bot é P-D-C-A; o hive encadeia esses ciclos numa
colaboração onde a saída de um vira a entrada do próximo, sem que os
bots precisem se conhecer diretamente — eles se comunicam pela memória.
"""
from __future__ import annotations

from typing import Any, Optional

from backend.bots.base import Bot
from backend.core import BotEvent, Phase, Task, TaskStatus
from backend.events.event_bus import EventType as NervEvent
from backend.events.event_bus import get_event_bus as _nervous_bus
from backend.hivemind.hive_memory import MemoryMixin
from backend.hivemind.lifecycle import ColonyLifecycle
from backend.hivemind.recruiter import Recruiter
from backend.hivemind.stigmergy import PheromoneField
from backend.hivemind.swarm_mixin import SwarmMixin
from backend.memory.event_bus import EventBus
from backend.memory.long_term_memory import LongTermMemory
from backend.memory.shared_memory import SharedMemory


class Hivemind(MemoryMixin, SwarmMixin):
    """Coordena os bots para resolver uma tarefa colaborativamente."""

    def __init__(
        self,
        memory: SharedMemory,
        roster: list[Bot],
        bus: Optional[EventBus] = None,
        ltm: Optional[LongTermMemory] = None,
        pheromones: Optional[PheromoneField] = None,
        lifecycle: Optional[ColonyLifecycle] = None,
    ) -> None:
        self.memory = memory
        self.bus = bus
        self.ltm = ltm  # memória de longo prazo compartilhada (Fase 3)
        self.recruiter = Recruiter(roster)
        # Enxame: feromônios (estigmergia) + gestão de energia dos bots.
        self.pheromones = pheromones or PheromoneField()
        self.lifecycle = lifecycle or ColonyLifecycle()
        # Superorganismo: castas, economia e polimorfismo (aditivos, leves).
        # Observam a colônia sem interferir no pipeline — cada bot é
        # registrado na sua casta e ganha uma conta na economia interna.
        from backend.hivemind.castes import CasteSystem
        from backend.hivemind.economy import BotEconomy
        from backend.hivemind.polymorphism import Polymorphism
        self.castes = CasteSystem()
        self.economy = BotEconomy()
        self.polymorphism = Polymorphism()
        # Evolução máxima: estados, homeostase, cultura e meta-cognição.
        # Tudo aditivo — observam e regulam sem alterar o pipeline central.
        from backend.cognitive.meta_supervisor import MetaSupervisor
        from backend.hivemind.colony_state import ColonyStateMachine
        from backend.hivemind.culture import ColonyCulture
        from backend.hivemind.homeostasis import Homeostasis
        self.colony_state = ColonyStateMachine()
        self.homeostasis = Homeostasis()
        self.culture = ColonyCulture()
        self.meta = MetaSupervisor()
        # Rastreador de recrutamento: "quem chamou quem" (transparência §3.3).
        from backend.hivemind.recruitment_tracker import RecruitmentTracker
        self.recruitment = RecruitmentTracker()
        # Fallback cognitivo (lazy) + fila de eventos a emitir ao vivo.
        self._cog_fb: Any = None
        # Córtex determinístico (lazy): cálculo exato ANTES da busca (7.2).
        self._cortex: Any = None
        self._pending_events: list[BotEvent] = []
        for bot in roster:
            self.lifecycle.register(bot.name)
            self.castes.register(bot.name, "worker")
            self.polymorphism.register(bot.name)

    async def _emit(self, event: BotEvent) -> None:
        """Callback injetado nos bots para publicar eventos no bus."""
        if self.bus is not None:
            await self.bus.publish(event.task_id, event.to_dict())

    async def solve(self, task: Task) -> Task:
        """Resolve uma tarefa do início ao fim, atualizando seu estado."""
        task.touch(TaskStatus.PLANNING)
        self.memory.save_task(task)
        # Sistema nervoso: anuncia a tarefa (aditivo, não afeta o fluxo).
        _nervous_bus().publish(NervEvent.TASK_CREATED, {"id": task.id, "goal": task.goal})

        needs = self.recruiter.infer_needs(task.goal)
        bots = self.recruiter.recruit(needs)
        _nervous_bus().publish(NervEvent.BOT_RECRUITED,
                               {"task": task.id, "bots": [b.name for b in bots]})

        # Injeta o emissor de eventos em cada bot recrutado.
        for bot in bots:
            bot._emit = self._emit  # noqa: SLF001 - injeção interna proposital

        intent = self._record_recruitment(task, bots)
        await self._announce(
            task.id,
            f"Colmeia leu a intenção '{intent}' e recrutou: "
            f"{', '.join(b.name for b in bots)}",
        )

        task.touch(TaskStatus.RUNNING)
        self.memory.save_task(task)

        payload: dict[str, Any] = {"goal": task.goal, "query": task.goal}
        # Antes da tarefa: recupera conhecimento prévio relevante (Fase 3).
        n_recalled = await self._recall_prior(task, payload)
        if n_recalled:
            await self._announce(
                task.id, f"Colmeia recordou {n_recalled} memórias úteis"
            )

        try:
            await self._run_pipeline(task, bots, intent, payload)
        except Exception as exc:  # noqa: BLE001
            task.error = str(exc)
            task.touch(TaskStatus.FAILED)
        finally:
            self.memory.save_task(task)
            if self.bus is not None:
                await self.bus.close(task.id)
        return task

    def _record_recruitment(self, task: Task, bots: list) -> str:
        """Registra 'quem chamou quem' (§3.3) e devolve a intenção lida.

        A Rainha recruta cada casta (motivo=intenção) e cada bot passa o bastão
        ao próximo — a cadeia real da missão, gravada no contexto compartilhado.
        """
        intent = self.recruiter.intent_of(task.goal)
        for b in bots:
            self.recruitment.record("rainha", b.name, intent)
        for a, b in zip(bots, bots[1:]):
            self.recruitment.record(a.name, b.name, "passou o bastão")
        self.memory.set_context(task.id, "recruitment",
                                self.recruitment.get_chain())
        return intent

    async def _run_pipeline(self, task: Task, bots: list, intent: str,
                            payload: dict[str, Any]) -> None:
        """Executa a cadeia de bots e consolida o desfecho de sucesso."""
        for bot in bots:
            self._run_bot_hooks_pre(bot.name)
            last_output = await bot.run(task.id, payload)
            ok = last_output.get("ok", True)
            self._run_bot_hooks_post(intent, bot.name, ok)
            if not ok:
                await self._announce(
                    task.id,
                    f"{bot.name} não teve sucesso; colmeia prossegue",
                )
        task.result = self._compile_result(task.id)
        for ev in self._pending_events:  # emite anúncios do fallback
            await self._emit(ev)
        self._pending_events.clear()
        task.touch(TaskStatus.DONE)
        self._remember_outcome(task)
        self._record_trust(bots, success=True)  # confiança conquistada
        self.lifecycle.maintain()  # hiberna ociosos (poupa recursos)

    def _compile_result(self, task_id: str) -> dict[str, Any]:
        """Reúne o produto final a partir do contexto compartilhado.

        Além da resposta de pesquisa (decisão + fontes), inclui o app
        criado pelo CreatorBot e a percepção do PerceptorBot quando
        presentes — para que qualquer intenção produza um resultado útil.
        """
        decision = self.memory.get_context(task_id, "decision") or {}
        lesson = self.memory.get_context(task_id, "lesson") or {}
        created = self.memory.get_context(task_id, "created_app")
        perception = self.memory.get_context(task_id, "perception")

        answer, confidence, cognition, computation, plan = \
            self._resolve_answer(task_id, decision, created)

        sources_list = self.memory.get_context(task_id, "sources") or []
        # Clareza da busca (9.2 · Bloco D): a resposta da web passa pelo
        # compositor — síntese limpa + selo de proveniência + fontes — em vez
        # do despejo cru do decisor (a "confusão" que o dono relatou). Só
        # quando a resposta veio da web (há fontes e não foi cálculo/plano).
        if sources_list and not computation and not plan and answer \
                and "Sem evidências suficientes" not in answer:
            from backend.cognitive.response_composer import get_composer
            domains = self._domains_of(sources_list, dedup=True)
            answer = get_composer().web(answer, len(sources_list), domains)
        result: dict[str, Any] = {
            "answer": answer,
            "confidence": confidence,
            "sources": sources_list,
            "learning": lesson,
        }
        recruitment = self.memory.get_context(task_id, "recruitment")
        if recruitment:
            result["recruitment"] = recruitment   # quem chamou quem (§3.3)
        if computation:
            result["computation"] = computation
        if plan:
            result["plan"] = plan
        if cognition:
            result["cognition"] = cognition
        if created:
            result["created_app"] = created
        if perception:
            result["perception"] = perception
        # Proveniência (aditivo): de ONDE veio a resposta e qual o desfecho
        # REAL da tentativa de busca externa. Nunca maquia — declara a fonte.
        result["provenance"] = self._build_provenance(
            task_id, result["sources"], cognition, created, answer,
            computation, plan
        )
        # Trajeto da missão (7.2): o que CADA bot fez, obstáculos reais e o
        # que a colônia aprendeu — para o chat mostrar o caminho todo.
        result["trace"] = self._compile_trace(task_id, result)
        # Trilha cognitiva TIPADA (9.19 · FASE 1): os MESMOS eventos, agora num
        # contrato único (kind/actor/confidence/evidence) — aditivo ao texto.
        from backend.cognitive.cognitive_trace import CognitiveTrace
        events = self.memory.get_events(task_id) or []
        result["cognitive_trace"] = CognitiveTrace.from_bot_events(events).to_dict()
        # Cadeia de fallback EXPLÍCITA (9.19 · FASE 1): de qual degrau a missão
        # saiu (PRIMARY→…→HUMAN) e se precisa escalar ao humano — lido do sinal
        # real de proveniência, aditivo. Torna explícita a degradação implícita.
        from backend.cognitive.fallback_chain import FallbackChain
        prov = result.get("provenance") or {}
        fallback = FallbackChain.classify(
            prov.get("source"), result.get("confidence"),
            evidence_count=len(prov.get("urls") or []),
        )
        result["fallback"] = fallback.to_dict()
        # Laço vivo (FASE 6 · integração): alimenta o calibrador de confiança com
        # esta missão. "Acerto" = sinal de auto-consistência da colônia (resposta
        # ancorada e sem escalar ao humano) — NÃO é verdade externa; é a colônia
        # aprendendo se a confiança que declara bate com o próprio grounding.
        self._feed_calibrator(result.get("confidence"), prov.get("source"),
                              fallback.escalate_human)
        return result

    @staticmethod
    def _feed_calibrator(confidence, source, escalate_human) -> None:
        """Registra (confiança prevista, acerto auto-consistente) no calibrador vivo."""
        if not isinstance(confidence, (int, float)):
            return
        from backend.evaluation.confidence_calibration import get_calibrator
        grounded = source not in (None, "none")
        get_calibrator().record(float(confidence), correct=bool(grounded and not escalate_human))

    def _resolve_answer(
        self, task_id: str, decision: dict[str, Any], created: Any
    ) -> tuple:
        """Decide a resposta/confiança e a fonte cognitiva a partir das rotas.

        Ordem de autoridade: cálculo exato (córtex determinístico) › plano
        raciocinado › app criado › cérebro próprio (fallback cognitivo). Devolve
        (answer, confidence, cognition, computation, plan) para o compilador usar.
        """
        computation = self._deterministic(task_id)
        plan = None if computation else self._planner(task_id)
        answer = decision.get("answer")
        confidence = decision.get("confidence")
        _GENERIC = "Sem evidências suficientes"
        cognition: dict[str, Any] | None = None
        if computation:
            answer = computation["answer_text"]
            confidence = computation["confidence"]
        elif plan:
            answer = plan["answer_text"]
            confidence = plan["confidence"]
        elif created and (not answer or _GENERIC in answer):
            summary = created.get("summary", {})
            answer = (
                f"App criado: {summary.get('type')} "
                f"({summary.get('files')} arquivos, "
                f"{summary.get('tests')} testes)."
            )
        elif not created and (not answer or _GENERIC in answer):
            # Sem evidência externa e sem app: recorre ao cérebro próprio.
            cognition = self._cognitive_fallback(task_id)
            if cognition:
                answer = cognition["answer"]
                confidence = cognition["confidence"]
        return answer, confidence, cognition, computation, plan

    @staticmethod
    def _domains_of(sources: list, dedup: bool = False) -> list[str]:
        """Extrai os domínios (host) das fontes com URL. `dedup` remove repetidos."""
        out: list[str] = []
        for s in sources:
            url = (s or {}).get("url", "") if isinstance(s, dict) else ""
            if "://" in url:
                dom = url.split("://", 1)[1].split("/", 1)[0]
                if not dedup or dom not in out:
                    out.append(dom)
        return out

    def _compile_trace(
        self, task_id: str, result: dict[str, Any]
    ) -> dict[str, Any]:
        """Monta o trajeto real da missão a partir dos eventos e do desfecho.

        Nada inventado: agrupa os eventos por bot (o que cada um fez), coleta
        os obstáculos reais (bot sem sucesso, web bloqueada) e o que a colônia
        aprendeu (lacunas, memórias recordadas, fonte usada).
        """
        events = self.memory.get_events(task_id) or []
        bots, errors = self._group_events(events)
        prov = result.get("provenance") or {}
        # Obstáculo real de rede (403/erro) entra no trajeto, com honestidade.
        web = prov.get("web") or ""
        if web and ("bloqueado" in web or "erro" in web):
            errors.append({"bot": "exploradores",
                           "detail": f"busca externa {web}"})
        return {
            "bots": bots,
            "errors": errors,
            "learnings": self._collect_learnings(result, prov),
            "source": prov.get("source"),
            "path_reason": result.get("recruitment") or [],
            "conclusion": result.get("answer"),
        }

    @staticmethod
    def _group_events(events: list) -> tuple:
        """Agrupa os eventos por bot (o que cada um fez) e coleta os erros reais."""
        import re as _re
        per_bot: dict[str, dict[str, Any]] = {}
        order: list[str] = []
        errors: list[dict[str, str]] = []

        def _slot(name: str) -> dict[str, Any]:
            name = "colônia" if name == "hive" else name
            if name not in per_bot:
                per_bot[name] = {"bot": name, "did": [], "ok": True}
                order.append(name)
            return per_bot[name]

        for e in events:
            bot = e.get("bot") or "colônia"
            msg = e.get("message") or ""
            slot = _slot(bot)
            if msg:
                slot["did"].append(msg)
            low = msg.lower()
            # "X não teve sucesso" é relatado pela colônia — atribui ao bot X.
            m = _re.match(r"(\w+) não teve sucesso", msg)
            if m:
                failed = _slot(m.group(1))
                failed["ok"] = False
                errors.append({"bot": m.group(1), "detail": msg})
            elif "falhou" in low or "erro:" in low:
                slot["ok"] = False
                errors.append({"bot": slot["bot"], "detail": msg})
        return [per_bot[b] for b in order], errors

    @staticmethod
    def _collect_learnings(
        result: dict[str, Any], prov: dict[str, Any]
    ) -> list[str]:
        """Sinais reais do que a colônia aprendeu (lição, lacunas, fonte usada)."""
        learnings: list[str] = []
        lesson = result.get("learning") or {}
        if isinstance(lesson, dict) and lesson.get("lesson"):
            learnings.append(str(lesson["lesson"]))
        cog = result.get("cognition") or {}
        for gap in (cog.get("gaps") or [])[:3]:
            learnings.append(f"lacuna identificada: {gap}")
        src = prov.get("source")
        if src == "computation":
            learnings.append("resolvido por cálculo exato — sem precisar de fontes")
        elif src == "none":
            learnings.append("sem evidência suficiente offline — limitação declarada")
        elif src in ("memory", "seed_knowledge", "seed_knowledge+memory"):
            learnings.append(f"respondido a partir de {src}")
        return learnings

    def _build_provenance(
        self,
        task_id: str,
        sources: list,
        cognition: dict[str, Any] | None,
        created: Any,
        answer: str | None = None,
        computation: dict[str, Any] | None = None,
        plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Classifica a origem da resposta e o status real da busca web.

        Valores de `source`: web_search (URLs reais), memory (recordado do
        grafo), seed_knowledge (inato), reasoning (inferência própria sem
        conhecimento), none (não conseguiu). Aditivo e honesto: se a web foi
        bloqueada (403) ou não trouxe nada, isso fica explícito em `web`.
        """
        web_report = self.memory.get_context(task_id, "web_report") or []
        domains = self._domains_of(sources)     # sem dedup (comportamento original)
        web_status = self._web_status(sources, web_report)
        direct = self._direct_provenance(web_report, computation, plan)
        if direct is not None:                  # cálculo/plano: autoritativo, sem web
            return direct
        if sources:
            source, confidence, gaps, castes = \
                "web_search", 0.9, [], ["rainha", "exploradoras"]
        elif created:
            source, confidence, gaps, castes = \
                "reasoning", None, [], ["rainha", "exploradoras"]
        elif cognition:
            source, confidence, gaps, castes = \
                self._classify_cognition(cognition, answer)
        else:
            source, confidence, gaps, castes = \
                "none", None, [], ["rainha", "exploradoras"]
        return {
            "source": source,
            "web": web_status,
            "web_attempts": web_report,
            "urls": domains,
            "confidence": confidence,
            "castes": castes,
            "gaps": gaps,
            "epistemic": self._epistemic(source, confidence),
        }

    @staticmethod
    def _epistemic(source: str, confidence: float | None) -> str:
        """Rótulo epistêmico honesto da resposta (anti-alucinação · FASE 1).

        • verified  — evidência real: cálculo exato ou fontes externas na web.
        • uncertain — sem base (source none) ou confiança muito baixa (<0.35).
        • inferred  — inferência própria (raciocínio/memória/inato) sem
          verificação externa. Nunca transforma inferência em fato.
        """
        if source in ("computation", "web_search"):
            return "verified"
        if source == "none":
            return "uncertain"
        if confidence is not None and confidence < 0.35:
            return "uncertain"
        return "inferred"

    @staticmethod
    def _direct_provenance(
        web_report: list, computation: dict[str, Any] | None,
        plan: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Proveniência das rotas determinísticas (cálculo/plano) — sem web.

        Autoritativa: não precisou de fonte externa nem de fato inato.
        """
        if computation:
            return {
                "source": "computation",
                "web": "web: nao necessario",
                "web_attempts": web_report,
                "urls": [],
                "confidence": computation.get("confidence", 1.0),
                "castes": ["rainha", "operarias"],
                "gaps": [],
                "steps": computation.get("steps", []),
                "kind": computation.get("kind"),
                "epistemic": "verified",     # cálculo exato = evidência dura
            }
        if plan:
            return {
                "source": "reasoning",
                "web": "web: nao necessario",
                "web_attempts": web_report,
                "urls": [],
                "confidence": plan.get("confidence", 0.6),
                "castes": ["rainha", "exploradoras"],
                "gaps": [],
                "steps": plan.get("steps", []),
                "kind": "plan",
                "epistemic": "inferred",     # raciocínio próprio, sem verificação
            }
        return None

    @staticmethod
    def _web_status(sources: list, web_report: list) -> str:
        """Status honesto e real da tentativa de busca externa."""
        codes = [r.get("status") for r in web_report]
        if sources:
            return "web: 200 ok"
        if not web_report:
            return "web: nao tentado"
        if any(isinstance(c, int) and 400 <= c < 500 for c in codes):
            code = next(c for c in codes if isinstance(c, int) and 400 <= c < 500)
            return f"web: {code} bloqueado"
        if all(c == "sem_resultado" for c in codes):
            return "web: sem resultado"
        return "web: erro/offline"

    @staticmethod
    def _classify_cognition(cognition: dict[str, Any], answer: str | None) -> tuple:
        """Classifica a fonte quando a resposta veio do cérebro próprio.

        memory (grafo) · seed_knowledge (inato) · seed_knowledge+memory ·
        reasoning (pura inferência) · none (confiança baixa/limitação declarada).
        """
        confidence = cognition.get("confidence")
        gaps = cognition.get("gaps", []) or []
        castes = cognition.get("castes", ["rainha", "exploradoras"])
        mem = cognition.get("memory_used", 0)
        seed = cognition.get("seed_used", 0)
        if mem and not seed:
            source = "memory"
        elif seed and not mem:
            source = "seed_knowledge"
        elif seed and mem:
            source = "seed_knowledge+memory"
        else:
            source = "reasoning"  # nenhum fato: pura inferência
        # Confiança muito baixa e sem qualquer base: declarou limitação.
        if not mem and not seed and (confidence or 0) < 0.35:
            source = "none"
        # Honestidade: se a resposta é o template de "sem evidências", a colônia
        # declarou limitação, ainda que tenha juntado algum fato.
        if answer and "Não tenho evidências suficientes" in answer:
            source = "none"
        return source, confidence, gaps, castes

    def _record_trust(self, bots: list, success: bool) -> None:
        """Registra confiança conquistada/perdida por bot (durável §4.1).

        Aditivo e tolerante a falhas: nunca derruba o pipeline se o store
        de confiança não estiver disponível.
        """
        try:
            from backend.permissions.trust_store import get_trust, save_trust
            t = get_trust()
            for b in bots:
                t.record_success(b.name) if success else t.record_failure(b.name)
            save_trust()
        except Exception:  # noqa: BLE001 - persistência é best-effort
            pass

    def _deterministic(self, task_id: str) -> dict[str, Any] | None:
        """Córtex determinístico: resolve cálculos exatos antes da busca.

        Se o objetivo é calculável (raiz, aritmética, %, potência), devolve o
        resultado exato + passos e enfileira um evento real para a timeline
        viva. Caso contrário, `None` — e o pipeline segue normalmente.
        """
        task = self.memory.get_task(task_id) or {}
        goal = task.get("goal", "")
        if not goal:
            return None
        if self._cortex is None:
            from backend.reasoning.deterministic import DeterministicCortex
            self._cortex = DeterministicCortex()
        comp = self._cortex.solve(goal)
        if not comp:
            return None
        data = comp.to_dict()
        data["answer_text"] = f"Resultado (cálculo exato): {comp.answer}"
        event = BotEvent(
            task_id=task_id, bot="hive", phase=Phase.ACT,
            message=(f"Córtex resolveu por cálculo exato ({comp.kind}): "
                     f"{comp.answer}"),
            data={"steps": comp.steps, "kind": comp.kind},
        )
        self.memory.add_event(event)
        self._pending_events.append(event)
        return data

    def _planner(self, task_id: str) -> dict[str, Any] | None:
        """Planejador: transforma 'faça um plano/N passos' em plano raciocinado."""
        task = self.memory.get_task(task_id) or {}
        goal = task.get("goal", "")
        if not goal:
            return None
        if getattr(self, "_task_planner", None) is None:
            from backend.reasoning.planner import TaskPlanner
            self._task_planner = TaskPlanner()
        plan = self._task_planner.plan(goal)
        if not plan:
            return None
        data = plan.to_dict()
        data["answer_text"] = plan.answer
        event = BotEvent(
            task_id=task_id, bot="hive", phase=Phase.ACT,
            message=(f"Planejador raciocinou um plano de {len(plan.steps)} "
                     "passos (sem fontes externas)"),
            data={"steps": plan.steps},
        )
        self.memory.add_event(event)
        self._pending_events.append(event)
        return data

    def _cognitive_fallback(self, task_id: str) -> dict[str, Any] | None:
        """Aciona o cérebro próprio quando a busca externa nada trouxe.

        Reúne o conhecimento recordado + o inato e roda o pipeline das 9
        camadas. Registra o evento na memória da tarefa (sync) e enfileira
        um anúncio ao vivo, para o fluxo/console mostrarem o desvio real.
        """
        task = self.memory.get_task(task_id) or {}
        goal = task.get("goal", "")
        if not goal:
            return None
        if self._cog_fb is None:
            from backend.hivemind.cognitive_fallback import CognitiveFallback
            self._cog_fb = CognitiveFallback()
        prior = self.memory.get_context(task_id, "prior_knowledge") or []
        cognition = self._cog_fb.answer(goal, prior)
        msg = (
            "Busca externa sem evidências — colmeia recorreu ao próprio "
            f"cérebro ({cognition['knowledge_used']} fatos, "
            f"confiança {cognition['confidence']:.2f})"
        )
        event = BotEvent(
            task_id=task_id, bot="hive", phase=Phase.ACT, message=msg,
            data={"layers": cognition["layers"], "castes": cognition["castes"]},
        )
        self.memory.add_event(event)
        self._pending_events.append(event)
        return cognition

    async def _announce(self, task_id: str, message: str) -> None:
        """Emite um evento em nome da colmeia (não de um bot específico)."""
        event = BotEvent(
            task_id=task_id, bot="hive", phase=Phase.PLAN, message=message
        )
        self.memory.add_event(event)
        await self._emit(event)
