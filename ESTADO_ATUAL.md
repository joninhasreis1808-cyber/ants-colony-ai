# ESTADO ATUAL — Ant's 6.1

> Documento de fatos verificados (não suposições). Gerado a partir do
> código no branch `claude/new-session-qf8twg` (commit da remoção de mockup).

## 1. Testes

```
python -m pytest tests/ -q
=> 347 passed, 5 skipped   (total 352)
```

Os 5 `skipped` dependem de bibliotecas opcionais pesadas não instaladas
(chromadb / sentence-transformers / sklearn / playwright). O núcleo roda 100%
offline sem elas.

## 2. MD5 dos 4 JS legados (contrato — inalterados)

```
e1cc6df5be37d6e0502b1063767601bd  web/js/chat.js
ed95b37ebbf0b926daa685dfe09419c1  web/js/bots.js
de5d8499d12efd869baa138497996e10  web/js/memory.js
18b0d5a834fda16f613633a250db053d  web/js/factory.js
```

## 3. Módulos do `backend/` (por pasta, contagem real de arquivos .py)

- **raiz**: `core.py` (tipos + manifesto de camadas), `lazy_loader.py`
- **events/** (3): `event_bus.py`, `middleware.py`, `audit.py` — sistema nervoso central
- **hivemind/** (29): `hive.py`, `recruiter.py`, `castes.py`, `pheromone.py`, `hormones.py`, `metabolism.py`, `circadian.py`, `homeostasis.py`, `colony_state.py`, `colony_dna.py`, `culture.py`, `quorum.py`, `mycelium.py`, `stigmergy.py`, `stigmergy_field.py`, `economy.py`, `plasticity.py`, `polymorphism.py`, `morphogenesis.py`, `regeneration.py`, `lifecycle.py`, `energy.py`, `reputation.py`, `personality.py`, `recruitment_tracker.py`, `cognitive_router.py`, `swarm_mixin.py`, `hive_memory.py`, `factory.py`
- **cognitive/** (16): `orchestrator.py`, `planner.py`, `researcher.py`, `hypothesizer.py`, `critic.py`, `verifier.py`, `specialist.py`, `simulator.py`, `executor.py`, `learner.py`, `advanced_reasoning.py`, `global_workspace.py`, `meta_supervisor.py`, `queen_council.py`, `explainer.py`, `failure_predictor.py`
- **reasoning/** (2): `engine.py`, `inference.py`
- **nlp/** (2): `processor.py`, `embeddings.py`
- **memory/** (25): `long_term_memory.py`, `retriever.py`, `consolidator.py`, `forgetter.py`, `attention.py`, `encoder.py`, `embedder.py`, `semantic_memory.py`, `procedural.py`, `knowledge_graph.py`, `hybrid_store.py`, `distributed_store.py`, `vector_backend.py`, `shared_memory.py`, `world_cache.py`, `cache_manager.py`, `sleep_cycle.py`, `schemas.py`, `reports.py`, `store_retrieval.py`, `event_bus.py`, `error_memory.py`, `compactor.py`, `ancestral.py`, `response_cache.py`
- **intelligence/** (9): `permanent_missions.py`, `permanent_goals.py`, `observer.py`, `discovery.py`, `predictor.py`, `temporal.py`, `scheduler.py`, `limitations.py`, `recommender.py`
- **agents/** (3): `investigator.py`, `architect_agent.py`, `autonomous_bot.py`
- **security/** (2): `immune_system.py`, `rate_limiter.py`
- **learning/** (1): `feedback_learner.py`
- **evaluation/** (2): `algorithm_selection.py`, `strategy_competition.py`
- **monitoring/** (5): `observability.py`, `metrics.py`, `logger.py`, `self_diagnosis.py`, `recovery.py`
- **providers/** (7): `router.py`, `base.py`, `local_provider.py`, `playwright_provider.py`, `duckduckgo.py`, `brave.py`, `tavily.py`
- **perception/** (8): `text_interpreter.py`, `image_analyzer.py`, `ocr_engine.py`, `document_reader.py`, `equation_solver.py`, `readers.py`, `models.py`, `vision_models.py`
- **action/** (8): `file_operator.py`, `app_launcher.py`, `web_navigator.py`, `form_filler.py`, `device_controller.py`, `smart_navigator.py`, `computer_use.py`, `computer_use_handlers.py`
- **permissions/** (4): `permission_manager.py`, `permission_levels.py`, `trust_based_autonomy.py`, `audit_logger.py`
- **app_factory/** (15): `factory_orchestrator.py`, `architect.py`, `requirement_analyzer.py`, `code_generator.py`, `template_engine.py`, `templates_data.py`, `templates_extra.py`, `tester.py`, `quality_analyzer.py`, `deployer.py`, `sandbox.py`, `documenter.py`, `results.py`, `schemas.py`, `enums.py`
- **bots/** (8): `base.py`, `perceptor.py`, `navigator.py`, `extractor.py`, `interpreter.py`, `decider.py`, `creator_bot.py`, `learner.py`
- **api/** (3): `main.py`, `deps.py`, `app.py`

## 4. Rotas expostas (verificadas via OpenAPI)

| Método | Rota |
|---|---|
| GET | `/health` |
| GET | `/metrics` · `/events/history` · `/events/summary` |
| POST | `/hive/task` — GET `/hive/status/{task_id}` — GET `/hive/swarm` |
| WS | `/hive/live/{task_id}` (streaming; usado por chat.js/bots.js) |
| POST | `/mind/think` · `/mind/reason` · `/mind/infer` · `/mind/assess` |
| GET | `/colony/state` · `/colony/meta` · `/colony/observability` — POST `/colony/homeostasis` |
| GET | `/organism/vitals` · `/organism/dna` — POST `/organism/feedback` · `/organism/immune/analyze` |
| GET/POST | `/organism/missions` |
| GET | `/bio/pheromones` · `/bio/mycelium/status` · `/bio/regeneration/{bot_id}` — POST `/bio/pheromones/deposit` · `/bio/quorum/propose` · `/bio/quorum/vote` · `/bio/recommend` |
| POST | `/memory/remember` · `/memory/recall` · `/memory/sleep` — GET `/memory/context` · `/memory/health` |
| POST | `/factory/create` · `/factory/quick` · `/factory/deploy/{project_id}` — GET `/factory/templates` · `/factory/projects` · `/factory/projects/{project_id}` |
| POST | `/perceive/text` · `/perceive/equation` · `/perceive/image` · `/perceive/ocr` · `/perceive/document` |
| POST | `/action/file` · `/action/app` · `/action/navigate` |
| GET | `/permissions/{user_id}` · `/permissions/audit/{user_id}` — POST `/permissions/grant` · `/permissions/revoke` |

`/health` responde `status: healthy` com **25 módulos** e `bots_active: 5`.

## 5. Contrato de IDs legados (a interface DEVE preservar)

```
app.js     → theme-toggle, conn, health-info, toast
chat.js    → chat-send, chat-input, messages
bots.js    → task-send, bot-grid, bot-log, task-input
memory.js  → mem-search, mem-sleep, mem-stats, mem-query, mem-list
factory.js → fac-create, fac-desc, fac-template, fac-result
```

Na interface do design, esses IDs existem como **espelhos ocultos** ou via
wrappers `display:contents` (`#chat-messages > #messages`, `#bots-grid >
#bot-grid`, `#memory-list > #mem-list`), e `web/js/scripts.js` faz as pontes
campo-visível → ID-legado. Os 4 JS originais **não foram alterados** (MD5 acima).

## 6. O que funciona hoje / o que ainda não está ligado (honesto)

**Ligado a dados reais (verificado no Chromium + via HTTP):**
- **Chat / Missão** → `POST /hive/task` + `GET /hive/status/{id}` (o "Fluxo da colônia" anima lendo o status real).
- **Cognição** → `POST /mind/think`: preenche "o que ela pensa", lacunas e as 9 barras (derivadas de `confidence`/`hypotheses`/`gaps` reais).
- **Recursos** → `/health` (bots, uptime), `/organism/vitals` (hormônios, apetite a risco, fase circadiana), `/events/summary` (throughput), `/colony/state`.
- **Rainha** → decisões reais de `/events/history`, feedback `POST /organism/feedback` (mostra o peso ajustado), DNA `/organism/dna`, meta `/colony/meta`.
- **Missões** → `GET /organism/missions`. **Linha do Tempo / Console** → `/events/history`.
- **Factory** → `POST /factory/create` gera app real (ex.: api_rest, 6 arquivos, 5 testes).
- **Fallback:** qualquer falha de endpoint mostra **"colônia adormecida"** e **"—"** — nunca números falsos.
- **Prova no console:** ao enviar tarefa, `api_bridge.js` loga `POST /hive/task → 200` e `GET /hive/status/… → 200`.

**Limitações reais (sem otimismo inventado):**
- **Memória:** `POST /memory/remember` retorna `stored:false` e o recall fica vazio **sem** o store vetorial opcional (chromadb + sentence-transformers). Os endpoints funcionam; a **persistência** exige essas libs opcionais.
- **Chat sem internet:** o motor de raciocínio é offline e conservador — sem rede (ou conhecimento fornecido) responde "sem evidências suficientes". Num deploy com rede ele pesquisa. (No sandbox, a busca externa é bloqueada.)
- **Aba Colônia (rede/hierarquia):** o diagrama de castas usa a **topologia** do módulo `live_dashboard.js` (estrutura das 6 castas). As contagens por casta ainda **não** vêm de um endpoint por-casta (não existe um; `/hive/swarm` dá estados de bots). O SVG é ilustrativo da estrutura, não contagem viva.
- **Aba Ambiente:** os itens sem endpoint real (arquivos indexados, processos, nós/relações do grafo) aparecem como **"—"** de propósito (não há rota que exponha esses números).
- **Barras cognitivas:** refletem o resultado real de `/mind/think`, porém **mapeadas** (não há endpoint de ativação por-camada).

## 7. Deploy no Render (importante)

O serviço **precisa ser Web Service + Docker**, não Static Site.

- `render.yaml` (raiz): `runtime: docker`, `dockerfilePath: ./deploy/Dockerfile`, `healthCheckPath: /health`.
- `deploy/Dockerfile`: `CMD uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8765}` (Render injeta `$PORT`).
- `Procfile` (fallback runtime nativo): `web: uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`.

⚠️ **Static Site NÃO funciona**: ele serve só os arquivos de `web/`, sem backend
FastAPI. Aí todo `fetch` falha e a interface mostra "colônia adormecida"
(antes da correção, mostrava mockup). Para ver dados reais, use Web Service.

Verifique: abra `https://SEU-APP.onrender.com/health` — deve retornar o JSON
com `status: healthy` e 25 módulos. Se retornar a página HTML/404, é Static Site.

---

## Adendo 6.3 (verificado)

- **Testes:** 378 passed, 5 skipped. **MD5 dos 4 JS legados inalterados.**
- **Linha do Tempo unificada:** absorveu Console e Missões em 3 seções
  (Fluxo/Missões · Registro Vivo · Console) via `web/js/timeline_hub.js` —
  fonte única de eventos, sem polling duplicado. Abas Console/Missões removidas.
- **UI Kernel** (`web/js/ui_kernel.js`): a IA modifica a interface por comandos
  declarativos de um conjunto fechado e seguro (nunca HTML arbitrário).
- **Endpoints novos:** `GET /hive/recruitment/{task_id}`, `GET /organism/trust`, `GET /organism/traditions`.
- **Persistência:** DNA, tradições, feedback e **trust** sobrevivem a restart
  (KV/SQLite) — provado via reinício HTTP real.
- **Explicabilidade:** botão "Como cheguei nisso?" com motivo real.
- Detalhes e provas: `ANTS_6.3_MUDANCAS.md` e `AUDITORIA_6.3.md`.

---

## Adendo 6.4 — unificação (fatos verificados no Chromium)

- **Um único chat**, dentro da aba **Colônia** (tela inicial). Abas "Chat" e
  "Linha do Tempo" **removidas** da navegação. Contagem real: 1 `#messages`,
  1 `#chat-input`, 1 `#chat-send` no projeto.
- **Linha do Tempo = célula viva embutida no chat**: 3 seções fundidas
  (Fluxo & Missões · Registro Vivo · Console) + missões permanentes +
  "Como cheguei nisso?", alimentadas por uma fonte única de eventos
  (`GET /hive/status/{id}` → `ants:task-tick`).
- **IA↔interface real:** 3 perguntas → `POST /hive/task` real, o fluxo acende
  etapa a etapa, resposta **offline** do cérebro próprio com **confiança 0.727**.
- **Persistência por restart real:** trust, tradições e DNA idênticos após
  reiniciar o servidor (2 processos, mesmo `ANTS_DB`).
- **382 testes** · MD5 dos 4 JS legados inalterados · zero mockup funcional.
- Interface: os únicos "emojis" em JS não-legado estão na TABELA de limpeza do
  `scripts.js`, que **remove** os emojis emitidos pelo `chat.js` imutável — nunca
  são renderizados.
