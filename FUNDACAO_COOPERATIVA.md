# Ant's — Fundação Cooperativa (FASE A do PLANO_MESTRE) · 9.6

> A infraestrutura para os bots **cooperarem sobre um estado compartilhado** —
> o pré-requisito de quase tudo do plano de longo prazo. Entregue como camada
> **testada e aditiva**: não altera nenhum fluxo atual; as próximas fases (B/D/E)
> constroem em cima. Nada é executado sem permissão.

## As 4 peças novas (adaptadas ao que já existia)

| Peça | Arquivo | O que faz | Reaproveita |
|------|---------|-----------|-------------|
| **ToolRegistry + Capacidades** | `backend/tools/` | catálogo único das "mãos"; valida **capacidade ≠ permissão** e o **Scope Guard** antes de executar | `device_scopes`, `path_guard` (8.0/9.3) |
| **TaskGraph** | `backend/hivemind/task_graph.py` | a missão vira um **DAG** de subtarefas (ordem, prontidão, ciclo) | — |
| **Blackboard** | `backend/hivemind/blackboard.py` | **quadro-negro** compartilhado (um bot escreve, outro percebe) | — |
| **Mission + Checkpoints** | `backend/hivemind/mission.py` | trabalho **longo** com estado e **retomada** | `core.new_id` |

Já existiam e continuam sendo a base (não reescritos): **ColonyBus**
(`event_bus`), **ColonyState** (`colony_state`), **lifecycle**,
**global_workspace**.

## Princípios respeitados
- **Capacidade ("sei fazer") ≠ permissão ("posso fazer"):** uma ferramenta é
  recusada com honestidade se falta o escopo — mesmo sabendo executá-la.
- **A Mente Colmeia nunca chama ferramenta direto:** pede ao ToolRegistry, que
  valida e audita. Ferramentas iniciais são **READ-ONLY** (`list_dir`,
  `read_file`), sempre atrás do `path_guard`. Escrita/apagar ficam para a FASE
  D/E, com dry-run + aprovação.
- **Offline-first / custo zero / Render seguro:** sem escopo concedido, o
  registro recusa tudo (o deploy atual não muda). Puro stdlib.
- **Mente Colmeia rege:** as peças são estado/infra compartilhados das castas,
  não um chefe paralelo.

## Como as próximas fases usam isto
- **FASE B (inteligência):** o córtex (9.5) planeja → gera um **TaskGraph**;
  os bots cooperam pelo **Blackboard**; a **Mission** guarda o progresso.
- **FASE D (ferramentas):** novas ferramentas entram no **ToolRegistry** (git,
  browser, terminal em sandbox…), sempre com capacidade + escopo + risco.
- **FASE E (autonomia):** o laço Observar→Planejar→Agir→Verificar roda sobre a
  Mission, com checkpoints/rollback/retomada.

## Prova
+18 testes (A1–A5): capacidade≠permissão, Scope Guard, path_guard, DAG
(ordem/prontidão/ciclo), quadro-negro cooperativo, checkpoints/retomada, e uma
**integração** que compõe as 4 peças numa missão real usando uma ferramenta.
