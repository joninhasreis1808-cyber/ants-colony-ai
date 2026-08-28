# Mapa: o que o Ant's já tem × o que a Visão 7.0 propõe

> **Por que este documento existe:** o próprio Relatório Mestre manda "primeiro
> mapear o que já existe e encaixar os novos componentes nos módulos atuais" e
> "nunca substituir uma implementação funcional só porque a nova parece mais
> elegante". Este é esse mapa — honesto, ancorado em arquivos reais do `backend/`
> e `web/`. Legenda: ✅ já existe · 🟡 existe parcial · ⬜ fronteira (a construir).

## Conclusão de cabeçalho (a parte importante)

O **esqueleto de seis componentes** que o Relatório recomenda construir **primeiro**
— Task Graph, EventBus, Shared Blackboard, Tool Registry, Verifier,
Checkpoint/Recovery — **já existe** no Ant's atual. Ou seja: a fundação da Visão 7.0
está, em grande medida, **pronta**. A evolução daqui é sobretudo (a) **amadurecer e
conectar** o que existe e (b) abrir **poucas fronteiras genuinamente novas** — com
destaque para o **Local Agent** (o "corpo") e a **Browser Perception**.

| Esqueleto (Fase recomendada de partida) | Status | Onde já vive |
|---|---|---|
| Task Graph | ✅ | `backend/hivemind/task_graph.py`, `backend/core.py` (Task) |
| EventBus | ✅ | `backend/events/event_bus.py`, `middleware.py`, `audit.py` |
| Shared Blackboard | ✅ | `backend/hivemind/blackboard.py`, `colony_state.py`, `cognitive/global_workspace.py` |
| Tool Registry | ✅ | `backend/tools/registry.py` (+ `capabilities.py`, Scope Guard) |
| Verifier | ✅ | `backend/cognitive/verifier.py`, `cognition/critic.py`, `action/verify_cycle.py` |
| Checkpoint / Recovery | ✅ | `backend/hivemind/mission.py` (checkpoints), `monitoring/recovery.py`, `hivemind/regeneration.py` |

## Crosswalk completo (itens 1–100 do Relatório)

### Inteligência e cognição
| Visão | Status | Onde / observação |
|---|---|---|
| Inteligência distribuída (não bots soltos) | ✅ | `hivemind/` + Mente Colmeia; castas em `castes.py` |
| Task Graph com nós ricos | ✅ | `hivemind/task_graph.py` — nós com `priority/confidence/evidence` (9.19 · FASE 1); planner popula confiança com o score real da rota |
| Cognitive Trace (eventos estruturados) | ✅ | `cognitive/cognitive_trace.py` — `TraceStep`/`CognitiveTrace` tipados dos BotEvents reais; `hive` anexa `result['cognitive_trace']` (9.19 · FASE 1) |
| Modos FAST/DELIBERATE/CRITICAL | ✅ | `cognitive/deliberation_mode.py` — política tipada (simulate/require_confirmation) ligada ao gate de risco; `ActionGate.Decision.mode` carimba o modo real (9.19 · FASE 2) |
| Route Explorer (todas as rotas + score) | ✅ | `cognition/cartographer.py` (7 rotas, score, bias da experiência) |
| Fallback em cadeia | ✅ | `cognitive/fallback_chain.py` — escada tipada PRIMARY→SECONDARY→COGNITIVE→HUMAN, escala ao humano sem base; `hive` anexa `result['fallback']` (9.19 · FASE 1) |
| Planner / Researcher / Hypothesizer / Simulator / Executor / Critic / Verifier / Learner / Meta-supervisor | ✅ | `backend/cognitive/*` tem todos esses módulos + `cognition/planner.py` |
| Deliberação e simulação antes de agir | 🟡 | `cognitive/simulator.py` existe; ligar ao gate de risco/permissão |
| Confidence calibration (predito × real) | ⬜ | confiança existe; laço de calibração a criar |

### Colônia, agentes e recursos
| Visão | Status | Onde / observação |
|---|---|---|
| Conselho / decisão coletiva (quórum) | ✅ | `cognitive/queen_council.py`, `hivemind/collective.py`, `quorum.py` |
| Spawn dinâmico + AgentPool | 🟡 | `hivemind/recruiter.py`, `recruitment_tracker.py`, `lifecycle.py`, `labor.py` |
| Reputação de bots | ✅ | `hivemind/reputation.py` |
| Especialização adaptativa / caste switching | ✅ | `hivemind/polymorphism.py`, `morphogenesis.py`, `plasticity.py` |
| Cultura / tradições | ✅ | `hivemind/culture.py`, `culture_store.py` |
| Metabolismo, energia, economia, orçamento | ✅ | `hivemind/metabolism.py`, `energy.py`, `economy.py` |
| Homeostase | ✅ | `hivemind/homeostasis.py` |
| Sistema imunológico + quarentena | ✅ | `backend/security/immune_system.py` |
| Scheduler / circadian / sleep | ✅ | `intelligence/scheduler.py`, `hivemind/circadian.py`, `memory/sleep_cycle.py` |
| Estigmergia (feromônio) | ✅ | `hivemind/pheromone.py`, `stigmergy.py`, `attention.py` |

### Memória e conhecimento
| Visão | Status | Onde / observação |
|---|---|---|
| Memória hierárquica L0–L6 | 🟡 | `memory/` tem working/semantic/procedural/LTM/consolidator/forgetter; níveis a nomear |
| Memória com evidência + provenance | 🟡 | `search/verifier.py`, `web/js/provenance_seal.js`; schema de proveniência a padronizar |
| Anti-alucinação (verified/inferred/uncertain) | 🟡 | composição de resposta honesta existe; rótulos internos a formalizar |
| Knowledge Graph vivo | ✅ | `memory/knowledge_graph.py` |
| Contradição + hipóteses | 🟡 | `cognition/critic.py` (contradição), `cognitive/hypothesizer.py`; unir num fluxo |
| Causal Graph | ⬜ | a construir |
| Garbage collector cognitivo | ✅ | `memory/forgetter.py`, `compactor.py`, `consolidator.py` |

### Ferramentas, ação e autonomia
| Visão | Status | Onde / observação |
|---|---|---|
| Padrão universal de Tool + Registry + Discovery | ✅ | `tools/registry.py`, `capabilities.py` (name/schema/risk/scope) |
| Browser Controller | 🟡 | `action/web_navigator.py`, `smart_navigator.py`, `providers/playwright_provider.py` |
| Browser Perception (PAGE MODEL, relearn) | ✅ | `perception/page_model.py` — `PageModel.from_html` (forms/inputs/buttons/links/landmarks + fingerprint estrutural); `needs_relearn` dispara em mudança de DOM; `WebNavigator.perceive()` (9.19 · FASE 4) |
| Filesystem / screenshot / process tools | 🟡 | `tools/file_tools.py`, `write_tools.py`; `action/device_files.py`, `screen_reader.py`, `computer_use.py` |
| Factory 2.0 (app como missão + sandbox + testes) | ✅ | `backend/app_factory/*` (architect, code_generator, tester, sandbox, quality_analyzer) |
| n8n Tool Bridge | ⬜ | opcional; ainda não existe |
| Pause/Resume/Cancel/Retry + rollback + recovery | 🟡 | autonomia + checkpoints existem; cancelamento propagado e rollback a completar |
| Níveis de autonomia 0–5 | 🟡 | `permissions/trust_based_autonomy.py`, `hivemind/autonomy.py` (governador) |
| Loop / deadlock / progress detectors | 🟡 | governador detecta sem-progresso; deadlock/loop dedicados a criar |

### Segurança e privacidade
| Visão | Status | Onde / observação |
|---|---|---|
| Capability-based permissions | ✅ | `permissions/device_scopes.py`, `permission_levels.py`, `tools/capabilities.py` |
| Path restrictions / command allowlist | ✅ | `permissions/path_guard.py`, `action/command_guard.py` |
| Guarda do dono (token) | ✅ | `api/security.py` (loopback-aberto; público exige token) |
| Prompt injection / conteúdo não confiável | ✅ | `security/content_sanitizer.py` |
| Audit log | ✅ | `permissions/audit_logger.py`, `events/audit.py`, `monitoring/device_audit.py` |
| Secret Vault dedicado | 🟡 | hoje via env/`ANTS_API_TOKEN`; cofre por-capability a criar |
| Rate limit / panic | ✅ | `security/rate_limiter.py`, `panic.py` |
| Consentimento explícito p/ ação perigosa | 🟡 | gate de escopo + dry-run existe; UI de consentimento a formalizar |

### Observabilidade, evolução e IDs
| Visão | Status | Onde / observação |
|---|---|---|
| Logs / metrics / traces / self-diagnosis | ✅ | `monitoring/observability.py`, `metrics.py`, `logger.py`, `self_diagnosis.py` |
| Benchmark / A-B de estratégias | 🟡 | `evaluation/strategy_competition.py`, `algorithm_selection.py` |
| Canary interno (5→10→25→50→100%) | ⬜ | a construir |
| Autoevolução só em DADOS (nunca código em produção) | ✅ | `hivemind/evolution.py` (propor→aprovar→aplicar, gated) |
| IDs globais + correlation ID | 🟡 | task/mission/agent/event ids existem; correlation ponta-a-ponta a padronizar |
| Autoavaliação final de missão | 🟡 | desfecho auditável existe; template OBJECTIVE/RESULT/… a padronizar |

### Interface (Colony Console)
| Visão | Status | Onde / observação |
|---|---|---|
| Colônia viva / cognição / ambiente / rainha / missões | 🟡 | `web/js/`: `mind_panel.js`, `mission_console.js`, `bot_camera.js`, `live_*`, `cognitive_center.js`, `timeline.js` |
| Live Activity por evento (sem vídeo 24/7) | ✅ | `bot_camera.js` + eventos por casta; screenshots por evento (padrão do projeto) |
| WebSocket / Event Stream | ✅ | `/hive/live/{id}` (ver `api_bridge.js`), fallback de polling |
| UI Command API tipada (IA não edita HTML) | ✅ | `interface/ui_commands.py` (contrato tipado e validado no backend) + `web/js/ui_kernel.js` (conjunto fechado); teste cruza os dois vocabulários (9.19 · FASE 5b) |
| Design System central | ✅ | `web/css/design_system.css` `:root` centraliza cor/espaço/tipografia + camada de aliases `--ant-*` para os módulos v6 |
| Feedback 👍/👎 que realmente aprende | 🟡 | `learning/feedback_learner.py`, `feedback_store.py`; ligar à Rainha |

### Cérebro remoto × corpo local (a correção técnica central)
| Visão | Status | Onde / observação |
|---|---|---|
| Render = cérebro remoto | ✅ | deploy atual (ants-c2ik) |
| Local Agent / Native Bridge (Tauri) | 🟡/⬜ | `action/computer_use.py`, `device_controller.py`, `input_controller.py`, `api/sidecar.py` existem; **a ponte segura remota↔local** é a fronteira |
| Comunicação segura (capability tokens, signed commands, nonce, TTL) | ⬜ | fronteira de segurança da ponte |
| Offline-first + degradação graciosa | ✅ | PWA + núcleo em regras; providers declaram indisponibilidade |

## Fronteiras genuinamente novas (o que realmente falta)

Em ordem sugerida, cauta e incremental — cada uma como **proposta → aprovação →
incremento testado**, sem tocar no que já funciona:

1. **Padronizar o esqueleto que já existe** (baixo risco, alto retorno): nós do
   TaskGraph com `priority/confidence/evidence`; Cognitive Trace unificado; cadeia
   de fallback explícita. — *conecta o que já está lá.*
2. **Modos de deliberação FAST/DELIBERATE/CRITICAL** ligados ao gate de
   risco/permissão e ao simulador que já existe.
3. **Local Agent seguro (o "corpo")** — a ponte remota↔local com capability tokens,
   comandos assinados, nonce e TTL. *O item mais estratégico e o mais sensível: só
   depois do esqueleto e da segurança estarem redondos.*
4. **Browser Perception** (PAGE MODEL + relearn on DOM change) sobre o
   `web_navigator`/`playwright_provider` atuais.
5. **UI Command API tipada + Design System** — formalizar como a Mente atualiza a
   interface por comandos, não por HTML.
6. **Calibração de confiança, canary interno e causal graph** — maturidade de
   autoevolução.
7. **n8n Tool Bridge** e **Secret Vault dedicado** — opcionais, quando houver
   necessidade real.

## Regras de ouro ao evoluir (resumo operacional)

- Núcleo cognitivo **offline** e **sem dependência externa**; Claude/n8n/APIs são
  ferramentas opcionais.
- Nada de reescrita: **camada de compatibilidade** quando houver incompatibilidade.
- Toda mudança: **testes + reversível**; MD5 dos 4 JS legados (`chat/bots/memory/
  factory`) permanece intocado.
- Autoevolução mexe só em **dados**, nunca em código de produção automaticamente.
- Cada fase encerra com a **autoavaliação de 15 perguntas**
  (ver `PROMPT_MESTRE_CLAUDE_CODE.md`).
