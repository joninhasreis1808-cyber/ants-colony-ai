# Ant's — Contrato completo do backend (API_CONTRACT)

> Extração fiel do que o backend expõe HOJE, para construir uma interface nova
> **sem tocar no cérebro**. Exemplos são **respostas reais** capturadas de um
> `uvicorn` rodando local (porta 8877). Onde a web externa aparece bloqueada
> (`403 ProxyError`) é limitação do ambiente de captura (sandbox), não do código
> — na máquina do dono a busca real funciona.

- **Base URL:** a mesma origem que serve a interface (ex.: `http://127.0.0.1:8000`).
- **84 rotas REST** + **1 WebSocket** (`/hive/live/{task_id}`) + **1 SSE**
  (`/hive/status/{task_id}/stream`).
- **Formato:** JSON em requisição e resposta (exceto `/metrics`, texto Prometheus).
- **Versão do backend:** `2.0.0` (campo `version` em `/health`).
- **Autenticação (9.3):** por padrão **loopback aberto** — local não exige nada.
  Se o deploy for público (`ANTS_PUBLIC=1` + `ANTS_API_TOKEN`), as rotas que
  **mudam estado ou tocam o dispositivo** exigem `Authorization: Bearer <token>`
  ou `X-Ants-Token: <token>` (senão **401**). Detalhe em §9.

## Índice
1. Núcleo (`/health`, `/ping`, `/metrics`)
2. HiveMind (`/hive`) — o fluxo de uma tarefa (o mais importante p/ a UI)
3. Mente / raciocínio (`/mind`)
4. Colônia / estados (`/colony`)
5. Organismo / telemetria (`/organism`)
6. Percepção (`/perceive`)
7. Memória (`/memory`)
8. Factory (`/factory`)
9. Permissões (`/permissions`) e Segurança
10. Device / ações no dispositivo (`/device`, `/action`)
11. Bio-inspirado (`/bio`)
12. Eventos / observabilidade (`/events`)

---

## 1 · Núcleo

### `GET /health` — saúde e módulos ativos
Resposta real:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "modules": { "hivemind": true, "perception": true, "action": true,
    "permissions": true, "memory": true, "factory": true, "bio_inspired": true,
    "computer_use": true, "autonomy": true, "superorganism": true,
    "cognitive": true, "reasoning": true, "colony_states": true,
    "meta_cognition": true, "homeostasis": true, "observability": true,
    "metabolism": true, "immune_system": true, "hormones": true,
    "circadian": true, "colony_dna": true, "trust_autonomy": true,
    "observer": true, "nervous_system": true, "metrics": true },
  "bots_active": 5,
  "memories_stored": 0,
  "tasks_submitted": 2,
  "providers": ["wikipedia", "duckduckgo"],
  "uptime_seconds": 12.3,
  "auth": { "mode": "open", "token_configurado": false, "publico": false }
}
```
Uso na UI: indicador "conectado/adormecida", contadores de topo, e conferência
da postura de segurança (`auth`). Nunca revela o token.

### `GET /ping` — keep-alive ultraleve
`{"pong": "ok"}` — para monitores/uptime (não toca módulo algum).

### `GET /metrics` — métricas Prometheus (texto, não JSON)
```
# HELP ants_events_total Total de eventos por tipo
# TYPE ants_events_total counter
ants_events_total{type="ACTION_COMPLETED"} 59
ants_events_total{type="ACTION_STARTED"} 60
```

---

## 2 · HiveMind (`/hive`) — o fluxo de uma tarefa

Este é o coração para a UI: envie um objetivo, acompanhe o trabalho ao vivo,
receba a resposta com proveniência.

### 2.1 · `POST /hive/task` — enviar um objetivo
Requisição: `{ "goal": "string*" }`
Resposta real (eco imediato, <300ms — a tarefa roda em background):
```json
{
  "task_id": "task_06327231a09c",
  "status": "pending",
  "echo": "Recebi — recrutando 4 casta(s): exploradoras, operárias, rainha, cuidadoras.",
  "intent": "reason",
  "castes": ["exploradoras", "operárias", "rainha", "cuidadoras"]
}
```
- `task_id`: use para acompanhar (polling, SSE ou WS).
- `echo`: feedback humano imediato (mostre no chat já).
- `intent`: intenção lida (`reason`, `computation`, `action_device`,
  `capability_query`, `question`…).
- `castes`: castas recrutadas (para o "quem trabalha nisto").
- Erro: **400** se `goal` vazio.

### 2.2 · `GET /hive/status/{task_id}` — estado + eventos (polling)
Resposta real (resumida):
```json
{
  "id": "task_06327231a09c",
  "goal": "quanto e 37 * 12",
  "status": "done",                 // pending | running | done | failed
  "result": { … ver 2.5 … },        // null enquanto não termina
  "error": null,
  "created_at": 1786745836.37,
  "updated_at": 1786745837.10,
  "events": [ … ver 2.4 … ]
}
```
Como saber que terminou: `status ∈ {done, completed, failed}` **ou** `result != null`.

### 2.3 · `GET /hive/status/{task_id}/stream` — SSE (mesma verdade, empurrada)
`Content-Type: text/event-stream`. Cada frame é o **objeto de status inteiro**
(igual ao 2.2), e ao fim vem um evento `end`:
```
data: {"id":"task_…","status":"running","events":[…]}

data: {"id":"task_…","status":"done","result":{…},"events":[…]}

event: end
data: {}
```

### 2.4 · Estrutura de um evento (o registro vivo)
Cada item de `events[]` (evento REAL capturado):
```json
{
  "id": "evt_6cfa5d6847f2",
  "task_id": "task_06327231a09c",
  "bot": "navigator",
  "phase": "do",                    // plan | do | check | act (ciclo P-D-C-A)
  "message": "Providers tentados: wikipedia, duckduckgo",
  "data": { "attempts": ["wikipedia", "duckduckgo"] },
  "ts": 1786745870.08
}
```
Sequência típica (intenção `reason`): a Colmeia anuncia o recrutamento →
cada bot (`navigator → extractor → interpreter → decider → learner`) emite
`plan → do → check → act` → a Colmeia fecha com o desfecho (ex.: "Córtex
resolveu por cálculo exato"). Derive o progresso da **fase do último evento**
(é o que a nova UI deve fazer; ver GUIA §Progresso).

### 2.5 · Estrutura da resposta final (`result`)
Objeto real completo (cálculo `37*12`):
```json
{
  "answer": "Resultado (cálculo exato): 444",
  "confidence": 1.0,
  "sources": [],                    // [{title,url,snippet}] quando veio da web
  "learning": { "confidence": 0.0, "learned_from_sources": 0,
                "global_avg_confidence": 0.0, "tasks_seen": 1 },
  "recruitment": [ { "caller": "rainha", "called": "navigator",
                     "reason": "reason", "ts": 0.0 }, … ],  // quem chamou quem
  "computation": { "ok": true, "answer": "444", "kind": "arithmetic",
                   "steps": [ "Reconheci a expressão…", "…SymPy…", "Resultado: 444" ],
                   "confidence": 1.0, "answer_text": "Resultado (cálculo exato): 444" },
  "provenance": {
    "source": "computation",        // ver tabela abaixo
    "web": "web: nao necessario",   // status honesto da tentativa externa
    "web_attempts": [ { "provider": "wikipedia", "status": 403, "error": "ProxyError" }, … ],
    "urls": [], "confidence": 1.0, "castes": ["rainha", "operarias"],
    "gaps": [], "steps": [ … ], "kind": "arithmetic"
  },
  "trace": {
    "bots": [ { "bot": "navigator", "did": [ "…","…" ], "ok": false }, … ],
    "errors": [ { "bot": "navigator", "detail": "…não teve sucesso…" } ],
    "learnings": [ "resolvido por cálculo exato — sem precisar de fontes" ],
    "source": "computation",
    "path_reason": [ … igual a recruitment … ],
    "conclusion": "Resultado (cálculo exato): 444"
  }
}
```
Blocos **condicionais** em `result` (aparecem conforme o caminho):
`computation` (cálculo exato), `plan` (raciocínio/plano), `cognition` (cérebro
próprio quando não há fonte), `created_app` (Factory), `perception`.

**Proveniência — valores de `provenance.source`:**
| source | significado |
|--------|-------------|
| `computation` | cálculo exato (SymPy), autoritativo |
| `web_search` | fontes externas reais (`sources[]` + `urls`) |
| `memory` | recuperado do que já aprendeu |
| `seed_knowledge` | conhecimento inato do domínio |
| `knowledge_base` | base de fatos curada (9.1) |
| `reasoning` | inferência própria, sem fonte externa |
| `none` | não conseguiu — declara a limitação honestamente |
O campo `provenance.web` conta a verdade da tentativa externa: `web: 200 ok`,
`web: {code} bloqueado`, `web: sem resultado`, `web: nao necessario`, etc.

### 2.6 · `GET /hive/status/{task_id}/stream` via WebSocket — `WS /hive/live/{task_id}`
Empurra cada evento assim que nasce (o que os JS legados `chat.js`/`bots.js` usam):
```json
{ "type": "event", "event": { "bot": "navigator", "phase": "do", "message": "…", … } }
```
e ao fim `{ "type": "end" }`. Depois do `end`, busque o `result` em
`GET /hive/status/{id}`.

### 2.7 · `POST /hive/search` — busca em cascata direta (sem pipeline de bots)
Req: `{ "query": "string*", "limit": 5 }`. Resposta real:
```json
{ "answer": "Não encontrei evidência suficiente para responder.",
  "source": "none", "confidence": 0.15, "cached": false, "urls": [],
  "steps": ["Consultei o conhecimento inato (seed).", "Nenhuma fonte resolveu — declarei a limitação."] }
```
Cascata: memória → seed → base curada → Wikipedia → DuckDuckGo →
(SearXNG/Tavily/Brave se em env) → raciocínio. 2ª chamada da mesma query →
`cached: true`.

### 2.8 · `POST /hive/learn` — "Aprender isto" (ensinar a colônia)
Req: `{ "question": "string*", "answer": "string*" }`. Guarda no cache de
respostas (validade/TTL). Recuperável depois pela mesma pergunta.

### 2.9 · Formações da Rainha (visualização de castas)
- `GET /hive/formations` → `{ "formations": [ … ] }` (vazio se nenhuma ativa).
- `POST /hive/formation` req `{ "goal": "string*", "paths": 1 }` → cria uma
  formação real. Resposta real (resumo):
  ```json
  { "id": "form_3", "goal": "pesquisar sobre formigas",
    "name": "Formação pesquisar sobre formigas",
    "bots": [ { "handle": "Soldado Alfa", "caste": "soldados",
      "doing": "verificando a segurança à frente", "icon": "i-shield",
      "reputation": 0.6 }, … ] }
  ```
- `DELETE /hive/formation/{fid}` — descarta.
- `POST /hive/formation/{fid}/complete` — conclui.
- `POST /hive/formation/{fid}/reinforce` req `{ "caste": "string*" }` — reforça uma casta.
- `POST /hive/formation/{fid}/release` req `{ "caste": "string*" }` — libera uma casta.

### 2.10 · `GET /hive/recruitment/{task_id}` — cadeia "quem chamou quem" da tarefa.
### 2.11 · `GET /hive/swarm` — enxame ao vivo (feromônios + estado por bot)
```json
{ "pheromones": {}, "colony": { "navigator": { "state": "idle", "activations": 2 }, … } }
```
### 2.12 · Ações no device pelo chat (fluxo 8.1) —
`POST /hive/action/approve` e `POST /hive/action/cancel`, req `{ "plan_id": "string*" }`.
(Ver §10 para o ciclo completo permissão → plano → aprovação → execução.)

---

## 3 · Mente / raciocínio (`/mind`)

Todos recebem uma pergunta e devolvem raciocínio honesto (sem inventar).
- `POST /mind/think` req `{ "question": "string*", "knowledge": [] }`. Real:
  ```json
  { "answer": "Não tenho evidências suficientes sobre …",
    "confidence": 0.15, "domain": "geral", "hypotheses": 2,
    "gaps": ["colonia","formigas"], "critique_ok": false }
  ```
- `POST /mind/reason` e `POST /mind/assess` req `{ "question": "string*", "context": [] }`.
- `POST /mind/infer` req `{ "facts": ["…"]*, "goal": "string|null" }`.
Uso na UI: aba Cognição — hipóteses, lacunas (`gaps`), confiança, domínio.

---

## 4 · Colônia / estados (`/colony`)

- `GET /colony/state` → `{ "state": "dormant", "max_active_bots": 2, "idle_seconds": 0.0 }`.
  Estados: `dormant, observing, exploring, building, verifying, learning,
  defending, executing, emergency`. **É a fonte da "respiração" da UI.**
- `GET /colony/autonomy` / `POST /colony/autonomy` req `{ "policy": "string*" }`
  — política de autonomia da colônia.
- `POST /colony/homeostasis` req `{ cpu, ram, queue, errors, battery }` (todos
  opcionais com default) — regula a homeostase a partir de métricas do host.
- `GET /colony/meta` → `{ "observations": 0, "bottleneck": null, "most_errors":
  null, "weights": { "planner": 1.0, … } }` — meta-cognição.
- `GET /colony/observability` → panorama de observabilidade.

---

## 5 · Organismo / telemetria (`/organism`)

- `GET /organism/vitals` → hormônios + ritmo (para a aba Recursos):
  ```json
  { "hormones": { "dopamine": 0.0, "cortisol": 0.0, "oxytocin": 0.0,
      "serotonin": 0.0, "adrenaline": 0.0, "melatonin": 0.0 },
    "risk_appetite": 0.5, "circadian_phase": "active", "immune_signatures": 0 }
  ```
- `GET /organism/capabilities` → o que a IA sabe fazer AGORA (para a UI expor):
  ```json
  { "offline": [ { "name": "cálculo exato (raiz, aritmética, %, potência)",
       "available": true, "where": "server", "source": "computation" }, … ],
    "needs_web": [ … ], "declared_native": [ … ], "runtime_note": "…" }
  ```
- `GET /organism/dna` → `{ "genome_size": …, "traits": { … } }`.
- `GET /organism/traditions` → tradições/cultura acumuladas.
- `GET /organism/trust` → confiança por bot/estratégia.
- `GET /organism/missions` / `POST /organism/missions` req
  `{ "description": "string*", "frequency": 3600.0 }` — missões permanentes.
- `POST /organism/feedback` req `{ "strategy": "string*", "kind": "string*",
  "text": "" }` — feedback do usuário que ajusta as próximas respostas.
- `GET /organism/observer` / `POST /organism/observer/analyze` req
  `{ duplicates, backup_age_days, disk_usage, update_available }` — observador do host.
- `POST /organism/immune/analyze` req `{ "action": "string*" }` — sistema imune.

---

## 6 · Percepção (`/perceive`) — ler/ver/entender

- `POST /perceive/text` req `{ "text": "string*" }`. Real:
  `{ "intent": "statement", "entities": [], "summary": "…", "sentiment":
  "neutral", "language": "pt", "word_count": 5 }`.
- `POST /perceive/equation` req `{ "equation": "string*" }` — resolve equação.
- `POST /perceive/document` / `POST /perceive/image` / `POST /perceive/ocr`
  req `{ "path": "string*" }` — lê documento/imagem/OCR de um caminho.
- `POST /perceive/screen/dom` req `{ "html": "string*", "goal": "" }` — entende
  a tela pelo DOM e planeja ação.
- `POST /perceive/screen/image` req `{ "path": "string*", "goal": "", "lang":
  "por" }` — entende a tela por screenshot (OCR).

---

## 7 · Memória (`/memory`)

- `GET /memory/health` → distribuição real da memória:
  ```json
  { "action": "memory_health", "counts": { "total": 0, "strong": 0,
      "medium": 0, "weak": 0 }, "details": [],
    "extra": { "overload_risk": false, "capacity_used": 0.0, "avg_strength": 0.0 } }
  ```
- `POST /memory/recall` req `{ "query": "string*", "limit": 10 }` →
  `{ "confidence": 0.0, "memories": [], "path": [] }`.
- `POST /memory/remember` req `{ "content": "string*", "source": "system",
  "emotional_weight": 0.0, "tags": [], "related_tasks": [], "repetition_count": 0 }`.
- `GET /memory/context` → contexto ativo (memórias vivas).
- `POST /memory/sleep` → dispara o ciclo de sono (consolida/decai).

---

## 8 · Factory (`/factory`) — criação de apps

- `GET /factory/templates` → `{ "templates": [ { "name": "api_rest",
  "files": 2 }, { "name": "web_app", "files": 2 }, … 6 modelos … ] }`.
- `POST /factory/create` req `{ "description": "string*", "options": { … }|null }`
  → cria um projeto (retorna `summary` com `project_id`, `type`, `files`, `tests`).
- `POST /factory/quick` req `{ "description": "string*" }` — criação rápida.
- `GET /factory/projects` → lista de projetos criados.
- `GET /factory/projects/{project_id}` → status de um projeto.
- `POST /factory/deploy/{project_id}` req `{ "target": <DeployTarget> }`.

---

## 9 · Permissões (`/permissions`) e Segurança

- `GET /permissions/{user_id}` → `{ "user_id": "jonas", "level": 1 }`
  (níveis 0–5; anônimo começa baixo).
- `POST /permissions/grant` req `{ "user_id": "string*", "level": int* }` —
  **rota sensível** (§Segurança).
- `POST /permissions/revoke` req `{ "user_id": "string*", "permission": "string*" }`
  — **rota sensível**.
- `GET /permissions/audit/{user_id}?limit=50` → histórico auditado.

### Segurança (9.3) — quem pode chamar as rotas sensíveis
- **Padrão (local/nativo):** loopback é confiável, **nada muda**.
- **Público (`ANTS_PUBLIC=1` + `ANTS_API_TOKEN`):** as rotas que mudam estado ou
  tocam o device exigem o token (`Authorization: Bearer <token>` **ou**
  `X-Ants-Token`). Sem/errado → **401**. Sem token configurado em modo público →
  **401** (fail-closed). Token nunca vaza (nem em log, nem no `/health`).
- **Rotas protegidas:** `/permissions/grant|revoke`, `/action/file|app|navigate`,
  `/device/scopes/grant|revoke|revoke_all`, `/device/paths/allow|disallow`,
  `/device/panic|panic/reset`.
- **2ª guarda em `/action/file`:** o `path_guard` recusa escrita fora das pastas
  autorizadas ou na blacklist imutável — **mesmo** para o dono autenticado.
- Q&A e leitura (`/health`, `/hive/*`, `/colony/*`, `/organism/*`,
  `/memory/*` de leitura, `/events/*`, `/ping`) seguem **abertas**.

---

## 10 · Device e ações no dispositivo (`/device`, `/action`)

**Runtime (importante):** `GET /device/runtime` →
```json
{ "mode": "web", "can_execute_device_actions": false, "platform": "linux",
  "display_server": "headless", "label": "modo web — apenas planeja (execução no app nativo/local)" }
```
No deploy web, `mode: "web"` — a colônia **planeja** ações mas **não executa**.
A execução real acontece só no app nativo/local (`ANTS_RUNTIME=native`).

**Escopos:** `GET /device/scopes` →
```json
{ "scopes": { "read_files": {"granted": false, "expires_in": null},
    "write_files": {…}, "run_apps": {…}, "control_input": {…},
    "screen_capture": {…}, "system_commands": {…}, "network": {…} },
  "all": ["read_files","write_files","run_apps","control_input",
          "screen_capture","system_commands","network"] }
```
- `POST /device/scopes/grant` req `{ "scope": "string*", "ttl_seconds": int|null }` — **sensível**.
- `POST /device/scopes/revoke` req `{ "scope": "string*" }` — **sensível**.
- `POST /device/scopes/revoke_all` — **sensível**.

**Pastas autorizadas (whitelist):**
- `GET /device/paths` → `{ "allowed": [ … ] }`.
- `POST /device/paths/allow` req `{ "path": "string*" }` — **sensível**; recusa
  blacklist imutável (`{ "allowed": false, "reason": "caminho na blacklist imutável" }`).
- `POST /device/paths/disallow` req `{ "path": "string*" }` — **sensível**.

**Avaliação (gate) — sem executar:** `POST /device/evaluate` req
`{ "action": "string*", "target": "", "external_content": "string|null" }`. Real:
```json
{ "allowed": false, "needs_confirmation": false,
  "reason": "escopo 'screen_capture' não concedido", "scope": "screen_capture",
  "threat": "safe", "injection": false, "details": {} }
```

**Pânico / auditoria:**
- `GET /device/panic` / `POST /device/panic` req `{ "reason": "…" }` (**sensível**) /
  `POST /device/panic/reset` (**sensível**).
- `GET /device/audit?limit=100` e `GET /device/audit/export` → trilha auditável
  (leitura; hoje **abertas** — ver GUIA para a decisão pendente).

**Execução real (`/action`) — tudo sensível em modo público:**
- `POST /action/file` req `{ "user_id": "string*", "op": "create|delete",
  "path": "string*", "content": "string|null" }`. Guardas: token (público) +
  `path_guard`. Fora de pasta autorizada → **403** com mensagem clara.
- `POST /action/app` req `{ "user_id": "string*", "op": "launch|close",
  "app_name": "string*" }` — requer nível/execução; **403** sem permissão, **503**
  se binário indisponível.
- `POST /action/navigate` req `{ "user_id": "string*", "url": "string*" }` —
  **503** se navegador indisponível.

**Fluxo completo de ação (8.0/8.1):** o usuário pede no chat → intent_router
classifica `action_device` → gera um **plano** (Observar → Aprovar → Executar) →
UI mostra o plano e o botão de conceder escopo/pasta → `POST /hive/action/approve`
`{plan_id}` → execução real (só em runtime nativo) → ciclo ver→agir→verificar.

---

## 11 · Bio-inspirado (`/bio`)

- `GET /bio/pheromones` / `POST /bio/pheromones/deposit` req
  `{ "trail_id": "string*", "type": "success", "intensity": 0.2 }`.
- `POST /bio/quorum/propose` req `{ "question": "string*", "options": [ … ]* }`.
- `POST /bio/quorum/vote` req `{ "bot_id": "string*", "proposal_id": "string*",
  "choice": "string*" }`.
- `POST /bio/recommend` req `{ "history": [], "current_task": "" }`.
- `GET /bio/mycelium/status` — rede micelial (comunicação interna).
- `GET /bio/regeneration/{bot_id}` — status de regeneração de um bot.

---

## 12 · Eventos / observabilidade (`/events`)

- `GET /events/summary` → `{ "total": 61, "by_type": { "ACTION_STARTED": 31,
  "ACTION_COMPLETED": 30 } }` — o painel de rede/atividade usa isto.
- `GET /events/history?limit=N` → histórico de eventos do sistema nervoso
  (`TASK_CREATED`, `BOT_RECRUITED`, `DECISION_TAKEN`, `PLAN_CREATED`, …) —
  a aba Rainha usa para "decisões recentes".

---

## Erros comuns (padrão FastAPI)
- **400** — corpo inválido (ex.: `goal` vazio em `/hive/task`).
- **401** — não autenticado numa rota sensível em modo público (§9).
- **403** — permissão negada / caminho recusado pelo `path_guard`.
- **404** — recurso inexistente (ex.: `task_id` desconhecido).
- **422** — validação Pydantic (campo faltando/tipo errado).
- **503** — capacidade dependente de binário pesado indisponível (navegador/OCR).

## Nota de honestidade
Nenhum endpoint "finge". Quando a web externa é bloqueada, `provenance.web`
declara `403 bloqueado` e a resposta cai para cálculo/raciocínio/memória — nunca
inventa. Tudo aqui foi capturado de execução real; onde não pude chamar algo com
efeito externo (web 403 no sandbox), está dito explicitamente.
