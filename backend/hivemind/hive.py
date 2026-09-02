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
        # Laço vivo (A5): a colônia registra o PRÓPRIO desempenho nesta missão —
        # rota, castas, desfecho e duração. É o que a Rainha vai consultar na
        # próxima formação. Dado puro; nenhuma linha de código se altera.
        self._observe_self_performance(task, bots)
        self.lifecycle.maintain()  # hiberna ociosos (poupa recursos)

    def _observe_self_performance(self, task: Task, bots: list) -> None:
        """Grava tempo/rota, sucesso/casta desta missão na meta-cognição (A5)."""
        try:
            from backend.cognition.experience import signature
            from backend.cognitive.self_performance import get_self_performance
            result = task.result or {}
            prov = result.get("provenance") or {}
            fb = result.get("fallback") or {}
            grounded = prov.get("source") not in (None, "none")
            escalou = bool(fb.get("escalate_human"))
            sucesso = bool(grounded and not escalou)
            duracao = max(0.0, task.updated_at - task.created_at)
            get_self_performance().record(
                signature=signature(task.goal or ""),
                route=prov.get("source") or "none",
                castes=[b.name for b in bots],
                success=sucesso,
                duration=duracao,
            )
            # Laço vivo (A4): a mesma missão é uma amostra do A/B em curso para
            # este tipo de objetivo — creditada ao braço que ela recebeu.
            from backend.evaluation.ab_experiment import get_ab_registry
            get_ab_registry().observe_mission(task.goal or "", sucesso, duracao)
        except Exception:  # noqa: BLE001 - nunca derruba a missão pelo laço vivo
            pass

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

        answer, confidence, cognition, computation, plan, grounded = \
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
        if grounded and grounded.get("sufficient"):
            # B1: as memórias que sustentam a resposta ficam CITADAS no produto
            # final — a colônia mostra de onde tirou, não pede para acreditar.
            result["grounding"] = grounded
        if created:
            result["created_app"] = created
        if perception:
            result["perception"] = perception
        # Proveniência (aditivo): de ONDE veio a resposta e qual o desfecho
        # REAL da tentativa de busca externa. Nunca maquia — declara a fonte.
        result["provenance"] = self._build_provenance(
            task_id, result["sources"], cognition, created, answer,
            computation, plan, grounded
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
        # B2 · verificação cruzada: as rotas que responderam se conferem entre
        # si. Concordância independente sobe pouco a confiança; contradição
        # numérica derruba e fica EXPOSTA — a colônia nunca escolhe calada
        # entre duas versões.
        check = self._cross_check(result, decision, computation, grounded,
                                  cognition)
        if check is not None:
            result["cross_check"] = check.to_dict()
            from backend.cognition.cross_check import apply_adjustment
            result["confidence"] = apply_adjustment(result["confidence"], check)
        # Laço vivo (FASE 6 · integração): alimenta o calibrador de confiança com
        # esta missão. "Acerto" = sinal de auto-consistência da colônia (resposta
        # ancorada e sem escalar ao humano) — NÃO é verdade externa; é a colônia
        # aprendendo se a confiança que declara bate com o próprio grounding.
        # B3 · calibração com sinais reais. A ordem importa e não é acidental:
        # o calibrador aprende com a confiança CRUA (a que a colônia declarou por
        # conta própria) e só DEPOIS corrige o número exibido. Alimentar com o
        # valor já calibrado fecharia um laço sobre si mesmo.
        self._feed_calibrator(result.get("confidence"), prov.get("source"),
                              fallback.escalate_human,
                              task_id=task_id,
                              cross_verdict=(check.verdict if check else None))
        self._apply_calibration(result)
        # B4 · rótulo epistêmico ampliado: os sinais que já existiam, espalhados
        # em seis campos, viram um rótulo único que a interface pode mostrar sem
        # ter de cruzar nada na cabeça. Nada de novo é inventado aqui.
        try:
            from backend.cognition.epistemic_label import build as _rotulo
            result["epistemic"] = _rotulo(result).to_dict()
        except Exception:  # noqa: BLE001 - o rótulo nunca derruba a missão
            pass
        # Laço vivo (FASE 6 · gatilho do canário): a missão realimenta os canários
        # das evoluções aplicadas para este tipo de objetivo — fecha o ciclo
        # propor→aprovar→aplicar→observar→promover/reverter, sozinho.
        grounded = prov.get("source") not in (None, "none")
        self._observe_evolution(task_id, bool(grounded and not fallback.escalate_human),
                                prov.get("source"))
        # Laço vivo (A2): a missão registra as relações CAUSA→EFEITO que ela
        # própria demonstrou — o grafo causal deixa de ser biblioteca e vira
        # memória viva que o Learner consulta antes de propor estratégia.
        self._observe_causal(task_id, prov, fallback, result.get("confidence"))
        return result

    def _observe_causal(self, task_id: str, prov: dict, fallback, confidence) -> None:
        """Registra no grafo causal o que ESTA missão demonstrou (nunca inventa).

        Só relações que os sinais reais sustentam: a fonte que ancorou (ou não) o
        desfecho, o degrau de fallback alcançado, e — quando a web falhou — o
        bloqueio que empurrou a colônia para a fonte alternativa.
        """
        try:
            from backend.cognition.experience import signature
            from backend.evaluation.causal_graph import get_causal_graph
            task = self.memory.get_task(task_id) or {}
            goal = task.get("goal", "")
            ctx = signature(goal) if goal else None
            source = prov.get("source") or "none"
            grounded = source != "none"
            desfecho = "desfecho:ancorado" if grounded else "desfecho:sem_base"
            conf = confidence if isinstance(confidence, (int, float)) else None
            n_urls = len(prov.get("urls") or [])
            g = get_causal_graph()
            g.observe(f"fonte:{source}", desfecho, context=ctx,
                      confidence=conf, evidence=n_urls)
            g.observe(f"fallback:{fallback.reached.value}", desfecho, context=ctx,
                      confidence=conf, evidence=n_urls)
            web = str(prov.get("web") or "")
            if "bloqueado" in web or "erro" in web:
                g.observe("web:bloqueada", f"fonte:{source}", context=ctx,
                          confidence=conf)
            if fallback.escalate_human:
                g.observe(desfecho, "escalou:humano", context=ctx, confidence=conf)
        except Exception:  # noqa: BLE001 - nunca derruba a missão pelo laço vivo
            pass

    def _observe_evolution(self, task_id: str, success: bool, source) -> None:
        """Realimenta os canários da evolução com o desfecho desta missão."""
        try:
            task = self.memory.get_task(task_id) or {}
            goal = task.get("goal", "")
            if not goal:
                return
            from backend.cognition.experience import signature
            from backend.hivemind.evolution import get_evolution_ledger
            get_evolution_ledger().observe_mission(signature(goal), success, route=source)
        except Exception:  # noqa: BLE001 - nunca derruba a missão pelo laço vivo
            pass

    @staticmethod
    def _feed_calibrator(confidence, source, escalate_human, *,
                         task_id: str = "", cross_verdict=None) -> None:
        """Alimenta o calibrador com o MELHOR sinal de acerto disponível (B3).

        Antes havia um sinal só, e o mais fraco: auto-consistência. Agora a
        colônia usa confirmação humana quando existe, verificação cruzada quando
        não, e a auto-consistência só como último recurso — declarando sempre
        qual das três camadas sustentou a observação.
        """
        if not isinstance(confidence, (int, float)):
            return
        from backend.evaluation.confidence_calibration import get_calibrator
        from backend.evaluation.correctness_signal import best_signal
        sinal = best_signal(
            human=Hivemind._human_verdict(task_id),
            cross_verdict=cross_verdict,
            grounded=source not in (None, "none"),
            escalate_human=bool(escalate_human))
        get_calibrator().record(float(confidence), correct=sinal.correct,
                                weight=sinal.weight)

    @staticmethod
    def _human_verdict(task_id: str):
        """Veredito humano JÁ registrado para esta missão (quase sempre None).

        Só existe quando o dono avaliou a missão antes de o resultado ser
        compilado — raro, mas o caminho fica aberto e é o mesmo que o endpoint
        de feedback usa depois.
        """
        try:
            from backend.evaluation.human_feedback import get_human_feedback
            return get_human_feedback().verdict(task_id)
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _apply_calibration(result: dict[str, Any]) -> None:
        """Corrige a confiança exibida pela taxa de acerto REAL da faixa (B3).

        Só corrige onde há amostra suficiente. Sem amostra, o número passa
        intacto — e a seção declara que não houve correção, em vez de sumir.
        """
        try:
            bruta = result.get("confidence")
            if not isinstance(bruta, (int, float)):
                return
            from backend.evaluation.confidence_calibration import get_calibrator
            cal = get_calibrator()
            taxa = cal.observed_rate(float(bruta))
            if taxa is None:
                result["calibration"] = {
                    "raw": bruta, "calibrated": bruta, "applied": False,
                    "reason": ("sem amostra suficiente nesta faixa - a confiança "
                               "passa intacta em vez de ser corrigida no chute")}
                return
            corrigida = round(max(0.0, min(1.0, taxa)), 4)
            result["confidence"] = corrigida
            if abs(corrigida - float(bruta)) < 5e-5:
                razao = (f"a confiança declarada bate com a realidade medida "
                         f"nesta faixa ({corrigida:.0%}) - nada a corrigir")
            else:
                razao = (f"nesta faixa a colônia acertou {corrigida:.0%} das "
                         f"vezes de verdade, e não os {float(bruta):.0%} que "
                         f"ela declarou")
            result["calibration"] = {
                "raw": bruta, "calibrated": corrigida, "applied": True,
                "reason": razao}
        except Exception:  # noqa: BLE001 - calibração nunca derruba a missão
            pass

    def _resolve_answer(
        self, task_id: str, decision: dict[str, Any], created: Any
    ) -> tuple:
        """Decide a resposta/confiança e a fonte cognitiva a partir das rotas.

        Ordem de autoridade: cálculo exato (córtex determinístico) › plano
        raciocinado › app criado › **memória própria fundamentada (B1)** ›
        cérebro próprio (fallback cognitivo).

        O RAG entra antes do fallback porque uma resposta ancorada em algo que a
        colônia REGISTROU vale mais que uma composição por regras sem lastro
        nenhum. E entra depois do cálculo e do plano porque memória é registro,
        não verificação — o teto de confiança dela diz isso.

        Devolve (answer, confidence, cognition, computation, plan, grounded).
        """
        computation = self._deterministic(task_id)
        plan = None if computation else self._planner(task_id)
        answer = decision.get("answer")
        confidence = decision.get("confidence")
        _GENERIC = "Sem evidências suficientes"
        cognition: dict[str, Any] | None = None
        # B2: a memória própria é consultada SEMPRE — barata e local. Mesmo
        # quando não é a rota escolhida, ela vira a segunda opinião da
        # verificação cruzada. Uma memória que discorda do cálculo tem que
        # aparecer, não sumir.
        grounded: dict[str, Any] | None = self._memory_rag(task_id)
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
            # B1: antes de adivinhar por regras, usa a própria memória.
            if grounded is not None and grounded.get("sufficient"):
                answer = grounded["answer"]
                confidence = grounded["confidence"]
            else:
                # Sem evidência externa, sem app e sem memória que sustente:
                # recorre ao cérebro próprio.
                cognition = self._cognitive_fallback(task_id)
                if cognition:
                    answer = cognition["answer"]
                    confidence = cognition["confidence"]
        return answer, confidence, cognition, computation, plan, grounded

    def _cross_check(self, result: dict[str, Any], decision: dict[str, Any],
                     computation, grounded, cognition):
        """Monta as afirmações de cada rota e as confronta (B2).

        Só entram rotas que REALMENTE produziram texto nesta missão. Nunca
        derruba a missão: qualquer falha devolve None e o resultado segue sem a
        seção de verificação.
        """
        try:
            from backend.cognition.cross_check import Claim, cross_check
            claims: list[Claim] = []
            if computation:
                claims.append(Claim("computation", computation["answer_text"],
                                    computation.get("confidence")))
            if result.get("sources") and decision.get("answer"):
                claims.append(Claim("web_search", decision["answer"],
                                    decision.get("confidence")))
            if grounded and grounded.get("sufficient"):
                # substância, não a moldura: "(1 registro)" é fato sobre a
                # recuperação e não afirmação sobre o mundo.
                claims.append(Claim("own_memory",
                                    grounded.get("substance") or grounded["answer"],
                                    grounded.get("confidence")))
            if cognition:
                fonte = self._classify_cognition(cognition, result.get("answer"))[0]
                claims.append(Claim(fonte, cognition.get("answer", ""),
                                    cognition.get("confidence")))
            if len(claims) < 2:
                return None            # sem segunda opinião, não há o que cruzar
            return cross_check(claims, result.get("confidence"))
        except Exception:  # noqa: BLE001 - verificação nunca derruba a missão
            return None

    def _memory_rag(self, task_id: str) -> dict[str, Any] | None:
        """B1: fundamenta na memória própria e CITA (ou devolve o silêncio).

        Nunca derruba a missão: sem LTM ou com falha de recall, devolve None e a
        colônia segue para a próxima rota.
        """
        try:
            from backend.cognition.memory_rag import get_memory_rag
            rag = get_memory_rag(self.ltm)
            if rag is None:
                return None
            goal = (self.memory.get_task(task_id) or {}).get("goal", "")
            if not goal:
                return None
            return rag.answer(goal).to_dict()
        except Exception:  # noqa: BLE001 - o RAG nunca derruba a missão
            return None

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
        grounded: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Classifica a origem da resposta e o status real da busca web.

        Valores de `source`: web_search (URLs reais), own_memory (B1 · ancorada
        em memórias próprias CITADAS), memory (recordado do grafo),
        seed_knowledge (inato), reasoning (inferência própria sem conhecimento),
        none (não conseguiu). Aditivo e honesto: se a web foi bloqueada (403) ou
        não trouxe nada, isso fica explícito em `web`.
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
        elif grounded and grounded.get("sufficient"):
            source, confidence, gaps, castes = (
                "own_memory", grounded.get("confidence"), [],
                ["rainha", "arquivistas"])
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
