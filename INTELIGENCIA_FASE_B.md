# Ant's 9.7 — FASE B: Inteligência (planejar e executar como um Manus)

A FASE A (9.6) deu à colônia a **fundação cooperativa**: ferramentas com escopo,
grafo de tarefas, quadro-negro e missões com checkpoint. A **FASE B** põe uma
**mente** em cima dessa fundação — a colônia deixa de "responder a primeira coisa
que casa" e passa a **imaginar caminhos, escolher o melhor, executar em etapas,
conferir e aprender**. Tudo determinístico, offline-first, sem nenhum LLM
embarcado como cérebro. A Mente Colmeia continua sendo a única coordenadora; as
castas continuam sendo quem age.

## O fluxo: Observe → Plan → Act → Verify → Learn

```
objetivo
   │
   ▼
[B1] Cartógrafa ── desenha TODAS as rotas possíveis e pontua cada uma
   │               (cálculo, memória, conhecimento, raciocínio, web,
   │                pesquisa profunda, dispositivo) — sem executar nada
   ▼
[B3] Experiência ─ injeta o viés do passado (rota que já deu certo sobe,
   │               a que falhou desce) e reordena
   ▼
[B2] Planejador ── decompõe o objetivo no esqueleto da rota vencedora →
   │               TaskGraph (DAG) validado
   ▼
[B5] Executor ──── percorre o grafo em ordem, emitindo um evento por casta
   │               (a Câmera ao Vivo mostra o trajeto), gravando Blackboard
   │               + Checkpoints (a missão sobrevive ao processo)
   ▼
[B4] Crítica ───── confronta fontes divergentes (viram investigação) e
   │               vigia o desvio de objetivo (reancora se derivou)
   ▼
[B3] Aprendizado ─ registra a rota vitoriosa (estratégia) ou o fracasso (erro)
```

## As peças

| # | Peça | Arquivo | O que faz |
|---|------|---------|-----------|
| B1 | **Cartógrafa** | `backend/cognition/cartographer.py` | `discover(goal, ctx)` desenha o mapa de rotas e pontua com a fórmula `P·0.35 + evidência·0.25 + confiabilidade·0.20 − custo·0.10 − risco·0.10 + bias`. `choose` pega a melhor disponível. Não executa nada. |
| B2 | **Planejador hierárquico** | `backend/cognition/planner.py` | `plan(goal)` escolhe a rota (com viés da experiência) e decompõe o objetivo no TaskGraph daquela rota. |
| B3 | **Memória de experiência** | `backend/cognition/experience.py` | `MemóriaDeErros` (penaliza rota que falhou) e `MemóriaDeEstratégias` (reforça e sugere a que funcionou). `apply_experience` injeta o viés no score. |
| B4 | **Crítica** | `backend/cognition/critic.py` | `ContradictionEngine` (polaridade + número → sub-pergunta de investigação) e `GoalGuard` (mede desvio foco×objetivo e reancora). |
| B5 | **Executor de missões** | `backend/hivemind/mission_runner.py` | `run_mission` costura tudo: planeja, executa passo a passo emitindo eventos por casta, grava Blackboard/Checkpoints, verifica desvio e aprende. |

## A porta REST

- `POST /mission` — planeja e dispara a execução **sem bloquear**; devolve o id
  real da missão, a rota escolhida e os passos.
- `POST /mission/run` — versão **síncrona**: executa a missão inteira e devolve o
  desfecho completo (rota, grafo, checkpoints, blackboard, progresso, resposta).
- `GET /mission/{id}` — desfecho auditável de uma missão executada.

Os eventos vão para a **mesma memória do `/hive`**, então a barra de progresso e a
**Câmera ao Vivo** funcionam sem nenhuma mudança de front-end — o id da missão faz
o papel do `task_id` que o `api_bridge.js` já escuta.

## Honestidade (Regra 6)

O executor **não inventa fatos**. Offline, ele orquestra e narra o plano de
verdade; a síntese com evidência da web só acontece quando há rede (na máquina do
dono). No sandbox sem rede, a pesquisa devolve uma **limitação honesta** — a
missão continua verdadeira. Nenhum passo é "encenado".

## Postura visível

`GET /health` agora traz o bloco `intelligence` (rotas da Cartógrafa, planejador,
motor de contradição, guarda de desvio, contador de aprendizado, endpoint de
missão) e o módulo `planning: true`. A interface pode exibir a inteligência real,
sem adivinhação.

## Testes

Cada peça foi testada **antes de ser usada**, no sandbox:

- `tests/test_cartographer_97.py` (7) · `tests/test_planner_hier_97.py` (6)
- `tests/test_experience_97.py` (6) · `tests/test_critic_97.py` (8)
- `tests/test_mission_runner_97.py` (5) · `tests/test_mission_api_97.py` (4)
- `tests/test_health_intelligence_97.py` (1)

Suíte total: **616 testes verdes**, MD5 dos 4 JS legados intacto (nada de tocar no
que é imutável). A FASE B não alterou nenhum comportamento anterior — só somou uma
mente à colônia.
