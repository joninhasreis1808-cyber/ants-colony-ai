# Relatório Mestre — Ant's 7.0 (Visão Arquitetural)

> **Status deste documento:** norte estratégico / visão. **Não é uma ordem de
> implementação.** Nada aqui deve ser implementado "de uma vez" nem por reescrita.
> Cada componente entra por **proposta → aprovação → incremento testado →
> verificação**, encaixando-se nos módulos que já existem (ver
> [`MAPA_ATUAL_x_VISAO.md`](./MAPA_ATUAL_x_VISAO.md)). Conteúdo curado pelo dono;
> preservado aqui na íntegra e organizado.

A recomendação de partida **não** é reescrever o Ant's: é tratar a versão atual
como **núcleo estável** e fazer uma **evolução arquitetural controlada** —
transformar o Ant's de "um sistema multiagente com funcionalidades" em uma
**plataforma de agente pessoal autônomo**, onde a Mente Colmeia:

```
decide → planeja → divide → executa → observa → verifica → corrige → aprende → atualiza a interface em tempo real
```

## Correção técnica essencial: cérebro remoto × corpo local

O **Render não controla, sozinho, o computador ou o celular** do usuário — um
servidor hospedado é **remoto**. Para o Ant's tocar arquivos, apps, tela, teclado,
mouse etc., é preciso um **Agente Local / Native Bridge** instalado no dispositivo.

- **Render** pode ser o **cérebro remoto**.
- **O app nativo/PWA local é o corpo.**

### Arquitetura final recomendada

```text
                         ┌─────────────────────────┐
                         │       USUÁRIO           │
                         └────────────┬────────────┘
                                      ▼
                         ┌─────────────────────────┐
                         │      INTERFACE ANT'S    │
                         │ Web / PWA / Tauri       │
                         └────────────┬────────────┘
                              Event Stream
                                      ▼
                 ╔════════════════════════════════════╗
                 ║          MENTE COLMEIA              ║
                 ║ Rainha → Planner → Conselho         ║
                 ║        ↓                            ║
                 ║ Task Graph → Castas → Ferramentas   ║
                 ║        ↓                            ║
                 ║ Observer → Critic → Verifier        ║
                 ║        ↓                            ║
                 ║ Learner → Memória → Cultura         ║
                 ╚══════════════════╤═════════════════╝
                 ┌──────────────────┼──────────────────┐
                 ▼                  ▼                  ▼
           Browser Agent       Local Agent          Files
           Playwright          Tauri/Native         Database
                 │                  │                  │
                 ▼                  ▼                  ▼
              Internet          Dispositivo        Memória
                                    ▼
                             Sistema operacional
```

Opcional — **n8n como Tool Bridge** (nunca o cérebro, apenas ponte de ferramentas):

```text
        ┌──────────────┐
        │     n8n      │  APIs / Email / Webhooks / SaaS
        │ TOOL BRIDGE  │
        └──────────────┘
```

---

## 1. O princípio mais importante

Mudar a filosofia interna de *"tenho vários bots que executam tarefas"* para
*"tenho uma única inteligência distribuída que utiliza organismos
especializados."* Os bots não são 10 IAs independentes conversando aleatoriamente;
eles **compartilham**: estado, objetivos, contexto, memória, percepção, recursos,
eventos, resultados, confiança, prioridades, erros, conhecimento e cultura.

```text
                 MENTE COLMEIA
       ┌───────────────┼────────────────┐
    Operário       Explorador       Jardineiro
       └───────────────┼────────────────┘
                MEMÓRIA GLOBAL → ESTADO DA TAREFA → KNOWLEDGE GRAPH
```

Isso cria uma **memória de trabalho coletiva**.

## 2. Task Graph

Toda solicitação vira um **grafo de tarefa**. Ex.: *"Pesquise notebooks bons até
R$ 4.000, compare e faça uma tabela"* não inicia um bot — cria:

```text
TASK-001
├── Interpretar objetivo
├── Definir restrições (preço<=4000, notebook, Brasil)
├── Pesquisar (fonte A, B, C)
├── Normalizar dados
├── Comparar
├── Detectar contradições
├── Verificar preços
└── Produzir resposta
```

Cada nó:

```json
{"id":"task_node_17","status":"running","owner":"explorer_03","priority":0.82,
 "confidence":0.71,"dependencies":["task_node_4"],"resources":["browser"],
 "started_at":"...","finished_at":null,"result":null,"evidence":[]}
```

Permite: pausar, continuar, cancelar, retomar, substituir um bot, repetir só uma
etapa, paralelizar, detectar gargalos e mostrar tudo na interface.

## 3. Cognitive Trace (não "cadeia de pensamento privada")

Não armazenar/expor uma cadeia de pensamento privada completa. Registrar **eventos
estruturados**:

```text
16:42:03 Planner    → objetivo interpretado
16:42:05 Researcher → identificou 4 lacunas
16:42:07 Explorer-02→ encontrou fonte A
16:42:10 Verifier   → fonte A: confiança 87%
16:42:12 Explorer-03→ encontrou contradição
16:42:14 Queen      → abriu nova rota de pesquisa
```

Melhor para transparência, debugging, interface, segurança, performance e
auditoria.

## 4. Modo deliberativo (três velocidades)

- **FAST** — perguntas simples, cálculos, comandos conhecidos, recuperação de memória.
- **DELIBERATE** — pesquisa, programação, tarefas multi-etapa, alterações no dispositivo.
- **CRITICAL** — apagar arquivos, mudar configurações, comandos perigosos, instalar
  software, operações financeiras, mudanças irreversíveis.

```python
if risk < 0.20: mode = FAST
elif risk < 0.70: mode = DELIBERATE
else: mode = CRITICAL
```

## 5. Sistema de rotas (Route Explorer)

"Ela deve encontrar todas as rotas possíveis." Cada rota recebe probabilidade de
sucesso, custo, tempo, risco, confiabilidade e recursos.

```text
Score = sucesso + confiabilidade + evidência − custo − risco − tempo
```

A Rainha escolhe a melhor — **não necessariamente a primeira**.

## 6. Sistema de fallback

```text
PRIMARY → FALLBACK 1 → FALLBACK 2 → ALTERNATIVE → HUMAN APPROVAL
```

Ex.: Pesquisar site → Playwright → (bloqueou) outra fonte → API pública → cache →
memória → pedir ajuda. Torna o sistema muito mais resiliente.

## 7. Mente Colmeia compartilhada (Shared Blackboard)

Estrutura coletiva (não chat entre bots):

```text
COLONY STATE: goal, current_task, known_facts, unknown_facts, hypotheses,
resources, warnings, active_routes, completed_actions, failed_actions,
evidence, confidence
```

## 8. EventBus (sistema nervoso)

```text
TASK_CREATED · BOT_SPAWNED · BOT_STARTED · BOT_FINISHED · BOT_FAILED ·
RESOURCE_REQUESTED · RESOURCE_GRANTED · EVIDENCE_FOUND · CONTRADICTION_FOUND ·
HYPOTHESIS_CREATED · HYPOTHESIS_REJECTED · MEMORY_CREATED · MEMORY_REINFORCED ·
MEMORY_DECAYED · PERMISSION_REQUESTED · PERMISSION_GRANTED · PERMISSION_DENIED ·
TASK_PAUSED · TASK_RESUMED · TASK_COMPLETED
```

A interface **escuta** — sem polling de tudo.

## 9. Comunicação entre castas

Rainha (coordenação), Conselho (decisões coletivas), Exploradores (descoberta),
Operários (execução), Soldados (segurança), Jardineiros (qualidade/conhecimento),
Cuidadores (treino/manutenção), Sentinelas (monitoramento), Arquivistas
(memória/histórico), Engenheiros (ferramentas), Curadores (verificação de
evidências), Mensageiros (transporte de eventos). **Agentes virtuais leves**, não
processos pesados.

## 10. Spawn dinâmico

Em vez de 100 bots sempre ligados: dormindo → tarefa chega → Rainha calcula
necessidade → spawn (2 exploradores, 1 verificador, 1 operário) → terminou →
hiberna.

## 11. Pool de agentes

`criar → executar → congelar → reutilizar` (em vez de criar→destruir→criar→destruir).

## 12. Metabolismo computacional

Cada agente: `energy, cpu_cost, memory_cost, priority, reputation, success_rate`.
Colônia com orçamento (`COLONY_BUDGET`: CPU 35%, RAM 400MB, NET 20MB/min, BROWSER
3 sessions). Se ultrapassar → **Homeostase**.

## 13. Homeostase

Perguntar sempre: CPU alta? RAM alta? tarefas redundantes? bots ociosos? pesquisas
duplicadas? loops? E agir (hibernar agentes → compactar memória → reduzir cache →
continuar).

## 14–15. Sistema imunológico + Quarentena

`ImmuneSystem` detecta loops, comportamento anormal, excesso de requisições,
ferramentas comprometidas, arquivos suspeitos, bots divergentes, comandos
perigosos. Um agente pode ser **`quarantined`** (BOT → anomalia → quarantine →
investigação → rollback) sem destruir a colônia.

## 16–18. Reputação, especialização adaptativa e cultura

- **Reputação:** `success_rate, accuracy, latency, resource_usage, mistake_rate,
  verification_rate`. A Rainha aprende ("Explorer-03 é excelente em pesquisa
  acadêmica") → seleção natural digital.
- **Especialização:** Explorer → Web Research Specialist → Academic Research
  Specialist, sem criar uma IA nova.
- **Cultura:** estratégias com `Success%` e `Uses` viram **TRADITION** após muita
  evidência.

## 19–21. Memória

- **Hierárquica:** `L0 contexto imediato · L1 trabalho · L2 episódica · L3
  semântica · L4 procedural · L5 conhecimento consolidado · L6 cultura` (mais
  distante = menos acesso, mais compressão, mais estabilidade).
- **Com evidência:** nunca só `"X é verdadeiro"`, mas
  `{claim, confidence, sources, created, last_verified, contradictions, provenance}`.
- **Anti-alucinação:** CLAIM → tem evidência? sim→confidence / não→uncertainty. A
  resposta carrega internamente `verified | inferred | uncertain | unknown`. Nunca
  transformar inferência em fato.

## 22–25. Verificação, simulação, rollback, checkpoints

- **Verifier independente:** recebe objetivo, resultado, evidências, restrições e
  pergunta: cumpre o objetivo? há contradições? há evidência? falta informação? a
  ação foi realmente executada?
- **Simulador:** PLAN → SIMULATE → EXPECTED RESULT → EXECUTE. Se `risco >
  threshold` → pedir autorização.
- **Rollback:** `before → action → after → rollback`.
- **Checkpoints:** tarefa longa com checkpoints → reabrir → restaurar → continuar.

## 26–29. Browser Agent

- **BrowserController:** abrir/fechar/trocar aba, voltar/avançar, clicar,
  preencher, selecionar, rolar, localizar elemento, ler DOM, screenshot, download,
  upload, executar JS quando autorizado, esperar carregamento, detectar
  popup/captcha/login/erro, recuperar após falha.
- **Browser Perception (PAGE MODEL):** buttons, inputs, links, forms, menus,
  dialogs, tables, images, navigation — e **raciocinar** sobre a página.
- **Memória de navegação:** aprende a rota do site (login, dashboard, settings…).
- **Detecção de mudança:** DOM changed → relearn page → find semantic equivalent →
  update route (não simplesmente falhar).

## 30–34. Local Agent, segurança da ponte e autonomia

- **LocalAgent** (app nativo) com permissões específicas: filesystem, processos,
  clipboard, screenshot, teclado, mouse, notificações, apps, navegador, rede,
  configurações permitidas — tudo via **PermissionManager**.
- **Render + dispositivo:** o servidor tem API/Mente/Memória/WebSocket/Task
  Manager/Knowledge Graph; o dispositivo tem o Local Agent → OS. **Nunca** dar ao
  servidor remoto acesso irrestrito ao computador.
- **Comunicação segura:** TLS, device identity, short-lived tokens, capability
  tokens, signed commands, nonce, timestamp. Toda ação recebida deve responder:
  quem pediu? qual tarefa? qual permissão? qual recurso? qual validade? qual
  assinatura?
- **Capabilities:** `CAN_READ_FILES, CAN_WRITE_FILES, CAN_SCREENSHOT, CAN_BROWSER,
  CAN_RUN_COMMAND, CAN_CONTROL_APP` — em vez de "tem acesso ao computador".
- **Níveis de autonomia:** 0 Observação · 1 Sugestão · 2 Execução segura
  (reversível) · 3 Autonomia controlada · 4 Autonomia avançada (pré-autorizada) ·
  5 Total (casos extremamente específicos).

## 35–50. Interface viva (Colony Console)

O chat deixa de ser só chat e vira **COLONY CONSOLE**: colônia viva (Queen,
Explorer, Worker, Gardener, Soldier + campo de comando), **Cognição** (Planner,
Researcher, Hypothesizer, Simulator, Executor, Critic, Verifier, Learner com
status e progresso), **Timeline dentro da Cognição** (camadas, agentes, eventos,
histórico da missão), **Ambiente** (dispositivo, internet, apps, arquivos, rede,
recursos, ferramentas), **Rainha** (objetivo, prioridade, estratégia, riscos,
recursos, decisões + feedback 👍/👎 que gera `USER_FEEDBACK → FeedbackProcessor →
StrategyEvaluation → Memory → Queen`), **Mission Center** (objetivo, progresso,
subtarefas, agentes, recursos) e **Live Activity Viewer** (mostra o agente ativo,
troca automática ao terminar).

Princípios de UI: **não** transmitir vídeo 24/7 — usar **screenshots por evento**
(início, mudança significativa, ação importante, erro, conclusão) via WebSocket; a
IA **não** edita HTML — emite **eventos/comandos tipados** (`UI State Engine` /
`UI Command API`: `OPEN_PANEL, FOCUS_AGENT, SHOW_TASK, SHOW_PROGRESS, SHOW_WARNING,
SHOW_APPROVAL, UPDATE_STATUS…`); **Design System** central (cores, espaçamento,
tipografia, raio, sombras, animações, ícones); animações representam estados
**reais** (spawning, thinking, searching, executing, waiting, error, sleeping); e
cor tem **significado consistente** (azul=info, verde=sucesso, amarelo=atenção,
vermelho=perigo, cinza=inativo).

## 51–54. Factory 2.0

Criar app é uma **missão**: ANALISAR → ARQUITETURA → UI → BANCO → BACKEND → TESTES
→ BUILD → VALIDAÇÃO, com **App Preview** e ações (Visualizar/Editar/Testar/
Executar/Exportar). Nunca tratar "código gerado" como "app pronto": `generate →
lint → type check → unit tests → integration tests → security scan → build → smoke
test`, tudo em **sandbox**.

## 55–58. Sistema de ferramentas

Padrão universal:

```python
class Tool:
    name; description; permissions; input_schema; output_schema
    risk_level
    def execute(): ...
    def rollback(): ...
```

- **Tool Registry:** a Mente consulta quais ferramentas existem, permissões,
  disponibilidade, custo, risco.
- **Tool Discovery:** registrar ferramentas sem mexer no cérebro
  (`register_tool()`), mas passando por schema/permission/security validation +
  teste.
- **n8n como Tool Bridge:** `Ant's → Tool Registry → N8N Tool → Webhook → workflow
  → JSON → Verifier` (nunca "n8n decide tudo").

## 59–61. Núcleo próprio, offline-first e degradação graciosa

Claude/n8n/APIs são **ferramentas opcionais**, não inteligência fundamental. O
núcleo (UI, memória, planner, reasoning, knowledge graph, task engine, segurança,
local tools) funciona **sem internet**; com rede, "a internet vira uma capacidade
adicional". Se cair: ONLINE → falha → OFFLINE MODE → continua tarefas locais, e a
interface informa que a pesquisa web está indisponível mas o local segue.

## 62–67. Recursos, prioridade, cancelamento e detectores

- **Resource Scheduler:** toda tarefa recebe orçamentos de CPU/RAM/rede/tempo/browser.
- **Prioridade:** CRITICAL/HIGH/NORMAL/LOW/BACKGROUND.
- **Cancelamento real:** PAUSAR/CONTINUAR/CANCELAR/REINICIAR propagando Queen → Task
  Manager → agents → tools → browser.
- **Deadlock detector** (ciclo de dependência), **Loop detector**
  (`STRATEGY_STALLED` sem progresso → nova estratégia), **Progress detector**
  (`progress_delta`; 10 min sem progresso → Rainha reconsidera).

## 68–71. Calibração, benchmark, canary, A/B

- **Confidence calibration:** quando digo 90%, quantas vezes estou certo?
  (predicted → actual → calibration).
- **Benchmark interno** permanente (reasoning, memory, research, navigation,
  coding, security, planning, tool use): before/after cada mudança; se piorou →
  **ROLLBACK**.
- **Canary interno:** 5% → 10% → 25% → 50% → 100%, só se melhorar.
- **A/B de estratégias:** comparar precisão, tempo, recursos, falhas, satisfação.

## 72–78. Auto-reparo seguro e rastreabilidade

- **Auto-reparo:** failure → diagnose → patch → sandbox → tests → benchmark →
  approval → deploy. Nunca "erro → alterar produção imediatamente".
- **Git Safety Agent:** branch → snapshot → change → tests → review → merge.
- **Migração** de banco versionada; **backup/snapshot** antes de mudanças críticas.
- **Observabilidade:** logs, metrics, traces, events — reconstruir uma tarefa
  depois.
- **IDs globais** (`task_id, mission_id, agent_id, tool_id, event_id`) e
  **Correlation ID** por requisição.

## 79–87. Segurança, privacidade e personalidade

- **Prompt injection:** tratar conteúdo de página como **UNTRUSTED DATA**, nunca
  como instrução superior. **Isolar instruções** por autoridade: SYSTEM POLICY >
  USER INTENT > TOOL INSTRUCTIONS > WEB CONTENT > MEMORY.
- **Secret Vault:** chaves/senhas/tokens fora de memória textual comum, acesso por
  capability.
- **Consentimento** explícito para ações perigosas; **Audit Log** (quem, o quê,
  quando, onde, por quê, permissão, resultado); **Privacy Mode** (LOCAL ONLY);
  **data minimization** (só o arquivo, não a pasta inteira).
- **Personalidade separada** da inteligência/memória/política; **User Model**
  (preferências, hábitos, formatos, horários, nível de detalhe) com controles de
  privacidade.

## 88–92. Objetivos, missões longas e ciclo circadiano

- **Goal Manager:** "quero aprender programação" → GOAL {objetivo, prazo,
  subtarefas, métricas, progresso}.
- **Long-running missions** (minutos/horas/dias) sem manter todos os agentes ativos.
- **Scheduler:** sleep quando nada acontece, wake no horário. **Circadian Engine**
  para atividade/manutenção/consolidação/backup/limpeza/aprendizado.
- **Garbage collector cognitivo:** memórias de baixo uso → compressão →
  arquivamento (não apagar tudo).

## 93–99. Conhecimento, hipóteses e autoavaliação

- **Knowledge Graph vivo** (entidade, relacionamento, força, confiança, origem,
  tempo) e **Provenance** ("de onde veio?": memory → source → evidence → timestamp).
- **Contradição:** duas fontes divergentes → não escolher arbitrariamente → criar
  **hipótese** ("A afirma X, B afirma Y — precisa de mais evidência").
- **Sistema de hipóteses** com confiança que se atualiza; **Causal Graph** (A
  causes B causes C); **simulação Monte Carlo** com orçamento adaptativo.
- **Autoavaliação final** de cada missão: OBJECTIVE, RESULT, EVIDENCE, ERRORS,
  TIME, RESOURCES, CONFIDENCE, USER_FEEDBACK + "o que eu faria diferente na próxima
  vez?" (alimenta a cultura).

## 100. O princípio final

O Ant's não deve tentar ser *"uma IA que sabe tudo"*, mas **uma inteligência que
sabe como descobrir o que não sabe.**

---

## Arquitetura de diretórios recomendada

> Não criar cegamente. Primeiro mapear o que já existe e **encaixar** os novos
> componentes nos módulos atuais (ver `MAPA_ATUAL_x_VISAO.md`).

```text
ants/
├── core/            hive, queen, council, colony_state, event_bus, scheduler
├── cognition/       planner, researcher, hypothesizer, simulator, executor,
│                    critic, verifier, learner, meta_supervisor
├── agents/          queen, explorer, worker, soldier, gardener, caretaker,
│                    engineer, archivist, sentinel
├── memory/          working, episodic, semantic, procedural, knowledge_graph,
│                    provenance, culture
├── tools/           registry, browser, filesystem, screenshot, process,
│                    notification, factory, n8n
├── autonomy/        route_planner, fallback, checkpoints, rollback, recovery
├── security/        permissions, sandbox, secrets, audit, policy, immune_system
├── resources/       scheduler, budgets, homeostasis, monitoring
├── local_agent/     filesystem, browser, screen, input, apps
├── api/             chat, tasks, events, websocket, permissions
└── web/             colony, cognition, environment, queen, missions, resources,
                     dna, factory, settings
```

---

## Roadmap de implementação (10 fases)

Não tudo simultaneamente.

- **Fase 0 — Congelamento:** `git status/branch`, `pytest`, coverage; criar
  `baseline/` registrando testes, RAM, startup, endpoints, comportamento da UI.
- **Fase 1 — EventBus + Task Engine:** EventBus, Task, TaskNode, TaskGraph,
  TaskState, Mission, Checkpoint (plataforma orientada a eventos).
- **Fase 2 — Mente Colmeia:** Shared Blackboard, AgentPool, Agent Reputation,
  Dynamic Spawn, Caste Switching, Council, Route Planner, Fallback.
- **Fase 3 — Cognição confiável:** Deliberation, Hypothesis, Evidence, Verifier,
  Critic, Simulation, Confidence Calibration, Contradiction Detection.
- **Fase 4 — Ferramentas:** Tool Registry, Browser Agent, Filesystem Tool,
  Screenshot Tool, Process Tool, Notification Tool, Factory Tool.
- **Fase 5 — Autonomia:** Pause, Resume, Cancel, Retry, Checkpoint, Rollback,
  Recovery, long-running tasks.
- **Fase 6 — Segurança:** Capabilities, Permission Manager, Sandbox, Secret Vault,
  Prompt Injection Defense, Audit, Immune System.
- **Fase 7 — Local Agent:** Render ↕ conexão segura ↕ Tauri ↕ LocalAgent ↕ OS (o
  "corpo").
- **Fase 8 — Browser Agent:** Browser → Perception → Planner → Action →
  Observation → Verifier.
- **Fase 9 — Interface:** refletir os eventos **reais**, não inventá-los.
- **Fase 10 — Autoevolução:** Benchmark → Experiment → Evaluate → Sandbox → Canary
  → Promote/Rollback.

**Recomendação final de partida:** não começar pela interface nem pelo n8n.
Primeiro **Task Graph + EventBus + Shared Blackboard + Tool Registry + Verifier +
Checkpoint/Recovery** — o esqueleto que sustenta todo o resto.

---

## O papel do Claude Code

Usar o Claude Code como **engenheiro executor/revisor**, **não** como arquiteto
autônomo sem limites. Nunca "implemente tudo". Ver o **Prompt Mestre** completo em
[`PROMPT_MESTRE_CLAUDE_CODE.md`](./PROMPT_MESTRE_CLAUDE_CODE.md).

### Autoavaliação obrigatória ao fim de cada fase

Não perguntar "está pronto?". Exigir resposta a: (1) o que foi implementado; (2) o
que não foi; (3) arquivos alterados; (4) testes adicionados; (5) total de testes;
(6) quantos passaram; (7) regressões; (8) aumento de RAM; (9) aumento de startup;
(10) dependências novas; (11) offline ainda funciona; (12) Render ainda funciona;
(13) Tauri ainda funciona; (14) riscos que permanecem; (15) próxima melhoria mais
importante.

---

## O que NÃO fazer

- ❌ Redis agora (SQLite + memória local é mais coerente com leveza/offline).
- ❌ Dezenas de agentes sempre ativos (destrói a leveza).
- ❌ Bots "pensando" continuamente (usar eventos e tarefas).
- ❌ IA editando o frontend livremente (usar UI Command/Event API).
- ❌ Claude dentro do núcleo (ferramenta opcional).
- ❌ Streaming de tela 24/7 (screenshots/eventos bastam).
- ❌ Render executando comandos diretamente no computador (usar Local Agent
  autenticado).
- ❌ Autoevolução alterando produção automaticamente
  (proposta → sandbox → teste → benchmark → aprovação → rollout).

**Regra absoluta:** nunca substituir uma implementação funcional só porque uma nova
parece mais elegante. Primeiro compreender, depois testar, depois modificar, depois
verificar, depois promover. Se a nova arquitetura for incompatível, propor uma
**camada de compatibilidade** em vez de destruir o que existe.

---

## O ciclo completo da Mente Colmeia

```text
PERCEBER → INTERPRETAR → PLANEJAR → EXPLORAR ROTAS → SIMULAR → DECIDIR →
PEDIR PERMISSÃO SE NECESSÁRIO → EXECUTAR → OBSERVAR → VERIFICAR → CORRIGIR →
CONSOLIDAR MEMÓRIA → APRENDER → ATUALIZAR CULTURA → DORMIR
```

E a distinção fundamental: **não é preciso reproduzir internamente o modelo
Claude/Manus/ChatGPT** para reproduzir certas capacidades de produto — planejamento,
uso de ferramentas, memória, recuperação de falhas, navegação, verificação,
execução e interface podem ser próprios. O que **não** dá para obter sem um modelo
generativo grande é o mesmo nível geral de compreensão linguística só com regras,
TF-IDF, PMI e heurísticas. Logo: **aperfeiçoar brutalmente o sistema de agentes e
ferramentas** e, em paralelo, **melhorar o motor cognitivo próprio** — sem fingir
que as duas coisas são equivalentes.
