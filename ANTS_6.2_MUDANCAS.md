# Ant's 6.2 — o que mudou (e o que ainda não)

> Documento honesto. Prefiro a verdade a um relatório bonito. Abaixo, o que
> foi entregue **com prova**, o que ficou **parcial** e o que **não foi feito**.

## Contrato preservado

- **Testes:** `347 passed, 5 skipped` (base 6.1) → **`362 passed, 5 skipped`** (6.2).
  Todas as adições são aditivas; nenhum teste existente foi quebrado.
- **MD5 dos 4 JS legados — inalterados:**
  ```
  e1cc6df5be37d6e0502b1063767601bd  web/js/chat.js
  ed95b37ebbf0b926daa685dfe09419c1  web/js/bots.js
  de5d8499d12efd869baa138497996e10  web/js/memory.js
  18b0d5a834fda16f613633a250db053d  web/js/factory.js
  ```
- **Zero mockup:** `grep Math.random|SAMPLE web/js/` só acha comentários de
  honestidade ("nunca inventar").

## Entregue e provado

### §3.1 — Chat responde offline com o cérebro próprio ✅
Quando a busca externa não traz evidências, a colmeia recorre ao
`CognitiveOrchestrator` alimentado por **conhecimento inato real**
(`backend/memory/seed_knowledge.py`, curado à mão — não números inventados)
+ memória recordada. Resposta traz texto útil, `confidence`, camadas/castas
participantes, `gaps` e nota de honestidade quando a confiança é baixa.
- Arquivos: `backend/memory/seed_knowledge.py`,
  `backend/hivemind/cognitive_fallback.py`, `backend/hivemind/hive.py`.
- **Prova:** `POST /hive/task {"goal":"o que são feromônios..."}` offline →
  resposta real, **confiança 0.727** (antes: "Sem evidências suficientes", 0.0).
- Testes: `tests/test_cognitive_fallback.py` (6).

### §3.2 — Deploy no Render ✅
- `GET /ping` ultraleve (2 ms, não toca módulos) para keep-alive.
- `DEPLOY.md` à prova de erro: Web Service + Docker, verificação de `/health`,
  aviso de hibernação do free tier.
- `render.yaml` / `deploy/Dockerfile` / `Procfile` já corretos (`uvicorn $PORT`).
- Teste: `tests/test_hive_api.py::test_api_ping_endpoint`.

### §4.3 — Ciclo do aprendizado fechado ✅
O feedback do usuário agora **altera de verdade** as escolhas seguintes do
orquestrador. `FeedbackLearner` virou singleton de processo compartilhado; a
rota `/organism/feedback` e `CognitiveOrchestrator.choose_strategy()` leem os
mesmos pesos. Estratégia `forbid` nunca é escolhida.
- Arquivos: `backend/learning/feedback_store.py`,
  `backend/cognitive/orchestrator.py`, `backend/api/routes/organism.py`.
- Teste que prova: `tests/test_feedback_loop.py` (4).

### §4.1 — Persistência que sobrevive a reinícios ✅ (feedback + memória)
- `backend/memory/kv_store.py`: KV durável em SQLite (sem TTL).
- `FeedbackLearner` ganha `to_state`/`load_state`; o store carrega no boot e
  salva a cada feedback. **Provado via restart HTTP real**: peso `documentacao_oficial`
  1.3 → (restart) → 1.6, e `reddit_primeiro` continua bloqueado.
- Tarefas/eventos já persistiam via `SharedMemory("ants.db")`.
- Testes: `tests/test_persistence.py` (3).

### §3.3 / §3.5 — Progresso e conexão honestos ✅ (parcial, ver abaixo)
- `api_bridge.js`: o "Fluxo da colônia" narra os **eventos reais** do backend
  (recrutamento "quem chamou quem", desvio ao cérebro próprio).
- `scripts.js` + `index.html`: o indicador de conexão nunca fabrica
  "Conectado"; reflete o estado real (online / **Adormecida**).
- `awaken.js`: **erros com dignidade** — se `/health` não responde em 6s, o
  splash cai para "Colônia adormecida" + botão **"Tentar acordar"** (antes
  ficava preso em "Sincronizando a memória…"). Provado por screenshot.
- **Prova (Playwright):** tarefa real → `POST /hive/task` + `GET /hive/status`
  na rede; fluxo sai de 0% e chega a 100%; resposta aparece no chat **com
  confiança (0.727)**; Linha do Tempo enche com eventos reais; backend
  bloqueado → estado **"Adormecida"** e **"—"**, nunca números falsos.

### §4.2 — Resposta em duas velocidades ✅
`POST /hive/task` agora devolve um **eco imediato** com a intenção lida e as
castas recrutadas (ex.: "Recebi — recrutando 3 casta(s): operárias, rainha,
cuidadoras"), computado de forma síncrona e leve **antes** do pipeline rodar.
- **Prova:** eco chega em **~60 ms** (chamada quente; <300 ms); a resposta
  completa segue pelo polling de `/hive/status`. `api_bridge.js` mostra o eco
  no fluxo de imediato.
- Teste: `tests/test_hive_api.py::test_task_returns_immediate_echo`.

### §7 (relatório de design) — Ponte `window.Ants` REAL ✅
No protótipo de design a ponte `window.Ants` era **simulada**. Aqui ela é
**real**: novo `web/js/ants_bridge.js` (aditivo, não toca nos 4 JS protegidos)
expõe `window.Ants`/`window.AntsUI` com a mesma superfície, mas cada método
fala com o backend/DOM reais e cada evento nasce de algo que a colônia de fato
fez.
- **IA → UI:** `send`/`runFlow` disparam `POST /hive/task` REAL (via `#chat-send`);
  `say`/`setColonyState`/`goTo`/`pushConsole`/`setMetric`/`setCognition`/`toast`.
- **UI → IA:** `on('goal'|'flowComplete'|'stateChange'|'online'|'netcall'|'ready')`
  alimentado pelos CustomEvents reais de `api_bridge.js`/`live_panels.js`.
- **Reativo ("de acordo com o que a IA reagir"):** ao concluir uma tarefa real,
  a ponte emite `flowComplete` com a resposta/confiança/cognição REAIS e volta o
  estado para "observando". `guardedAction()` passa pela guarda imunológica real
  (`POST /organism/immune/analyze`) antes de qualquer ação de dispositivo.
- **Prova (Playwright):** `Ants.send("o que são feromônios…")` disparou a tarefa
  e `Ants.on('flowComplete')` recebeu `answer` + `confidence 0.727` + bloco
  `cognition` (camadas/castas/lacunas, `source: cognitive_fallback`).

### §3.4 — Auditoria de botões ✅
Feedback da Rainha (mostra o peso ajustado), chat, factory, memória e tema já
falam com o backend. **Novo:** `web/js/controls.js` liga a **autonomia**
(`#autonomy-seg`) ao `/colony/autonomy` real (carrega, salva, persiste após
reload) e **desabilita com tooltip honesto** os botões sem ação real
(Pausar / Recrutar ajuda do modal) — nunca um clique que finge.

### §4.4 / §4.5 — Observer + guarda imunológica na UI ✅
- **Observer:** `GET /organism/observer` (achados reais; vazio e honesto sem
  snapshot). UI: card não-invasivo (máx. 3×/dia, Permitir/Ignorar).
- **Guarda imune:** `/organism/immune/analyze` agora retorna
  `requires_confirmation`; `AntGuard.confirm()` mostra confirmação em
  **vermelho** antes de ações perigosas, respeitando a política de autonomia
  (cautelosa confirma tudo; autônoma só confirma o perigoso).
- Provado por Playwright (autonomia persiste; card mostra "4 duplicados").

### §4.6 / §4.7 — Hibernação honesta + explicabilidade ✅
- `lifecycle.maintain()` hiberna bots ociosos de verdade; o estado "Adormecida"
  reflete isso na UI quando não há carga.
- **Explicabilidade:** toda conclusão do fluxo traz o **motivo real** —
  ex.: *"Resposta pronta · confiança 0.757 · 0 fontes externas · 4 fatos da
  memória"*. `POST /colony/autonomy` também registra o motivo na
  observabilidade.

### §3.3 — "Quem chamou quem" via `recruitment_tracker` ✅
`hive.py` agora grava a cadeia real de recrutamento (rainha → cada casta +
o "passar o bastão" entre bots) e a inclui no resultado da tarefa. A ponte
`window.Ants` empurra a cadeia ao **Console** e ao evento `flowComplete`.
Prova HTTP: 9 links reais numa pesquisa (`rainha → navigator · research`…).

### §4.1 — DNA / tradições persistentes ✅
`ColonyDNA` agora é um singleton durável (`dna_store`, KVStore) e **cresce por
ações reais**: "📌 tornar padrão" grava um gene de **tradição**; "🚫 nunca faça"
grava uma **regra** hereditária. Prova HTTP: o gene sobrevive a um **restart
real do servidor**.

## Parcial / não feito (honestidade)

- **§3.3 (ativação por-camada da Cognição):** as 9 barras ainda são **mapeadas**
  de `/mind/think` (confiança/hipóteses/lacunas), não de um stream de ativação
  por-camada — não existe endpoint por-camada e não criei um SSE novo.
- **§4.1 (trust scores por-bot):** DNA, tradições, feedback e autonomia
  persistem ponta a ponta; os **trust scores por-bot** seguem em RAM — são
  métricas internas recomputadas nas execuções, sem rota de mutação exposta.

## Conflito de regras emoji×MD5 — RESOLVIDO ✅

`chat.js/bots.js/factory.js/memory.js` são **imutáveis por MD5** (§0.2) mas
escreviam emojis (🐜/✅/⚠️/🤖/⏳/😴) em runtime, colidindo com "zero emojis"
(§0.5). **Resolução (arquivo livre `web/js/scripts.js`):** uma camada de
exibição substitui cada emoji por um **ícone SVG coeso**, atuando **somente**
nos nós que contêm emoji, via observadores alvo e debounced (rAF) que
auto-cicatrizam quando o JS protegido reescreve `textContent` no streaming.
Conteúdo interativo (saudação, botões, `.lead`) fica intocado.

- **MD5 preservado:** os 4 hashes acima seguem idênticos após a mudança.
- **Zero emojis na tela:** varredura Playwright de todos os nós de texto
  renderizados (`getClientRects()>0 && offsetParent!==null`) retorna **[]**.
- **Bônus:** liguei os chips `data-fill` da saudação (antes decorativos) para
  enviarem um objetivo real à colônia (`POST /hive/task` — verificado).

## Service worker

`web/sw.js` faz cache dos assets; após um deploy, pode servir JS antigo até o
SW atualizar. As provas com Playwright foram feitas com o SW desativado para
refletir o código atual. Vale um "hard refresh" após deploy.
