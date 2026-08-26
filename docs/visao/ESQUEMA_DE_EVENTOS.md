# Esquema de Eventos do Ant's (FASE 1 · contrato único)

> Padronização do esqueleto (ROTEIRO FASE 1): a Mente Colmeia se comunica por
> **eventos observáveis**, não por chamadas diretas. Este é o contrato único das
> três camadas de eventos — a "voz" do organismo. Ancorado no código real; um
> teste-invariante (`tests/test_event_schema_918.py`) impede este documento de
> divergir da implementação.

## Fonte única da verdade: `ColonyState`

O **backend é a autoridade do estado**; a interface apenas **renderiza**. O estado
vivo da colônia (`dormant/observing/exploring/building/verifying/learning/
defending/executing`) vem de `GET /colony/state` (máquina em
`backend/hivemind/colony_state.py`). A UI nunca inventa estado — reflete estes
eventos e este estado.

## Camada 1 — Sistema nervoso (`backend/events/event_bus.py` · `EventType`)

Eventos internos publicados no EventBus (auditáveis, base para observabilidade e
para o streaming ao vivo). Constantes atuais:

| Grupo | Eventos |
|-------|---------|
| Tarefa/plano | `TASK_CREATED`, `PLAN_CREATED` |
| Pesquisa | `RESEARCH_STARTED`, `RESEARCH_COMPLETED` |
| Cognição | `HYPOTHESIS_CREATED`, `HYPOTHESIS_REJECTED`, `VERIFICATION_COMPLETED`, `DECISION_TAKEN` |
| Ação (device) | `ACTION_STARTED`, `ACTION_COMPLETED`, `ACTION_FAILED`, `ACTION_PLANNED`, `ACTION_APPROVED`, `ACTION_EXECUTED`, `ACTION_VERIFIED` |
| Bots | `BOT_RECRUITED`, `BOT_RELEASED` |
| Superorganismo | `FEROMONE_DEPOSITED`, `HORMONE_RELEASED`, `COLONY_STATE_CHANGED` |
| Memória | `MEMORY_STORED`, `MEMORY_RECALLED`, `CACHE_HIT`, `CACHE_MISS` |
| Segurança | `ERROR_OCCURRED`, `THREAT_DETECTED` |
| Aprendizado | `FEEDBACK_RECEIVED`, `LEARNING_REGISTERED` |
| Curinga | `ALL` (`"*"` — assina todos) |

## Camada 2 — Ciclo do bot (`backend/core.py` · `Phase`, `BotEvent`)

Cada bot roda o ciclo **P-D-C-A**; cada passo emite um `BotEvent` (`task_id`, `bot`,
`phase`, `message`, `data`). É o que a Câmera ao Vivo e a barra de progresso leem.

- **Fases (`Phase`):** `plan` → `do` → `check` → `act`.
- **Estado da tarefa (`TaskStatus`):** `pending` → `planning` → `running` →
  `done` | `failed`.

## Camada 3 — Interface (eventos `ants:*` no front)

A ponte IA→UI é por **eventos tipados** (nunca HTML cru). Eventos reais em uso:

| Evento | Emitido por | Para quê |
|--------|-------------|----------|
| `ants:health` | `app.js` (fonte única) | distribui `/health` a rodapé/painéis/mente |
| `ants:task-tick` | `api_bridge.js` | progresso e Câmera ao Vivo (fase real) |
| `ants:task-done` | `api_bridge.js` | desfecho da missão (dispara o selo de proveniência) |
| `ants:tab` | navegação | troca de seção |
| `ants:online` | `api_bridge.js` | online/adormecida |
| `ants:netcall` | `api_bridge.js` | log de cada chamada à API |
| `ants:awake` | `awaken.js` | colônia despertou (fim da hibernação) |
| `ants:ui` | UI Kernel | comandos tipados da IA à interface |
| `ants:token` | `api_bridge.js` | chave do dono definida/limpa |
| `ants:bridge-ready` | `ants_bridge.js` | ponte IA↔UI pronta |

## Regra de ouro

A UI **observa** estes eventos e **comanda** por endpoints reais + UI Kernel; ela
não decide lógica de negócio nem inventa dados. Todo dado/animação/progresso
exibido nasce de um evento real desta tabela ou de um endpoint verificado.
