# AUTOAVALIAÇÃO — FASE A (Mente Colmeia) · Roteiro de Maestria v9.25

> **Base medida:** `main` commit `72a6341` · **962 passed, 5 skipped**
> **Escopo:** A1–A7, sete tarefas, sete PRs (#62, #64, #63, #66, #65, #67, #68).
> Tudo abaixo foi **medido neste commit**, não lembrado.

---

## Aviso de honestidade (antes de tudo)

**Não tenho o texto literal das 15 perguntas da PARTE VI.** O arquivo
`ROTEIRO_ants_MAESTRIA_v9.25.md` foi enviado pelo dono, mas o contêiner desta
sessão foi revertido para snapshots antigos três vezes e o upload não está mais
em disco. O que está **verificado no repositório** são as 6 regras do
`PROTOCOLO_COWORK` (literais, em `AUTOAVALIACAO_ESTADO.md`) e os 9 invariantes.

6 + 9 = 15. É sugestivo — **e eu não vou afirmar que é isso.** Numa rodada
anterior eu reconstruí as 6 regras de memória e **errei**; o erro está registrado
no próprio `AUTOAVALIACAO_ESTADO.md`. Não repito o erro fingindo lembrar.

Então: as 15 perguntas abaixo são **reconstruídas** dessas duas listas
verificadas, e estão marcadas como tal. **Se o dono reenviar o roteiro, eu refaço
esta autoavaliação contra o texto literal.**

---

## O achado mais importante desta fase

Três das sete peças **existem, estão testadas, e não são chamadas por nenhum
fluxo de produção**:

| Peça | Ligada ao laço vivo? | Quem chama |
|---|---|---|
| A2 · grafo causal | **sim** | `hive._observe_causal`, a cada missão |
| A4 · A/B por rota | **sim** | `planner._apply_experiment` + `hive` + `mission_runner` |
| A5 · desempenho próprio | **sim** | `recruiter._order` + `hive`, a cada missão |
| A6 · sono que reorganiza | **sim** | `sleep_cycle.run_sleep_cycle` |
| A1 · `deliberation.py` | **não** | ninguém (o `deliberation_mode` é usado; o módulo de cenários, não) |
| A3 · `RetrievalPlanner` | **não** | ninguém — 0 chamadas fora de teste e API |
| A7 · `RealCouncil` | **não** | só o endpoint `/council`; `QueenCouncil` não é usado em produção |

Isso **não** significa que o trabalho está errado. O A3 foi entregue
explicitamente como *"taxonomia + política, recalls injetáveis"* — foi uma
decisão declarada na época, não um descuido. Mas **"existe e é testado" não é o
mesmo que "a colônia usa"**, e apresentar as sete como igualmente vivas seria
maquiar. Fica registrado como dívida nomeada.

---

## As 6 regras do PROTOCOLO_COWORK (texto literal do repositório)

| # | Regra | Veredito | Evidência medida |
|---|---|---|---|
| 1 | Diagnóstico antes de correção | **cumprida** | Cada incremento abriu lendo o código existente. O A7 começou constatando que `QueenCouncil.deliberate()` recebia votos prontos; o A6, que `observe_mission` já se declarava *"não um A/B por rota"*. |
| 2 | Prova executável, não descrição | **cumprida** | 83 testes novos na fase. A prova do A4 roda a Cartógrafa real: sem experimento a colônia escolhe `computation` (0.559 vs 0.320); com o braço no desafiante, a missão roda em `memory`. |
| 3 | A rede de segurança é sagrada | **cumprida** | 887 → 962, verde antes e depois de cada PR, em ordem fixa e aleatória. Nenhum teste enfraquecido para caber. |
| 4 | Um commit por tarefa | **cumprida** | 7 tarefas, 7 PRs, 7 squash-merges. Nenhum commit-monstro. |
| 5 | Declarar o que NÃO foi verificado | **cumprida** | Seção final deste documento, e em cada PR. |
| 6 | Interface nunca inventa texto | **cumprida** | Os 5 endpoints novos devolvem estado vazio + `note` explicando. `rate: None` (não `0`) para braço sem tentativa; `success_rate` devolve `None` para casta sem histórico. |

## Os 9 invariantes

| # | Invariante | Veredito | Evidência medida |
|---|---|---|---|
| I1 | Custo zero / free tier | **preservado** | `git diff` em `requirements.txt`/`pyproject.toml` na fase inteira: **vazio**. Nenhuma dependência nova. |
| I2 | Offline-first | **preservado** | Nenhum dos 7 módulos da fase importa `httpx`, `requests`, `urllib.request` ou `socket`. |
| I3 | Sem LLM externo como cérebro | **preservado** | Único módulo com referência a API de LLM é `cognition/reasoner.py`, que **já existia** e é o córtex plugável opt-in: sem env, `backend_name()` devolve `"rules"`. Nenhum módulo da FASE A o consulta. |
| I4 | Sem build step no front | **preservado** | `web/package.json`, `webpack`, `rollup`, `tsconfig`: **todos ausentes**. |
| I5 | 4 JS legados imutáveis | **preservado** | Os 4 MD5 batem com o baseline registrado no `ci.yml`. `git diff` em `web/` na fase inteira: **vazio**. |
| I6 | Segurança do corpo é sagrada | **preservado** | `git diff` em `backend/local_agent/` e `app/` na fase inteira: **vazio**. Nada da FASE A toca o agente local. |
| I7 | Autoevolução só em DADOS | **preservado** | Nenhum `exec`, `eval`, `__import__` ou escrita de `.py` nos módulos novos. O A4 muda `Route.bias`; o A5, a ordem de uma lista; o A6, o tipo de uma memória. Nenhuma linha de produção reescrita. |
| I8 | Interface nunca inventa dado | **preservado** | Exercitado ao vivo: `/causal`, `/self-performance`, `/experiments`, `/council`, `/calibration` respondem 200 com estado vazio honesto. O A4 recusa declarar vencedor sem `\|z\| ≥ 1.96` **e** amostra mínima **e** validade da aproximação normal. O A6 não cria abstração sem feature em comum. O A7 se abstém sem base. |
| I9 | Rito de engenharia | **cumprido** | Diagnóstico → prova executável → pytest verde → 1 PR/tarefa → não-verificado declarado, nos 7. |

---

## O que NÃO foi verificado (a seção mais importante)

1. **Nada da FASE A rodou em produção.** Tudo é teste local + CI. O serviço no
   Render não foi exercitado com estas mudanças; os endpoints devolvem vazio
   porque nenhuma missão real passou por eles neste ambiente.
2. **O A/B nunca chegou a um veredito com dados reais.** Precisa de ≥12 missões
   por braço. Nos testes, os números são sintéticos.
3. **O viés de formação do A5 é zero na produção** até acumular histórico. A
   garantia "sem histórico, viés zero" está provada — mas o *benefício* ainda
   não foi observado numa missão real.
4. **O sono do A6 nunca reorganizou memória de produção**, só memórias de teste.
5. **O conselho do A7 não decide nada na colônia.** Existe, é testado, tem
   endpoint — e nenhum fluxo o consulta.
6. **A calibração (ECE) não foi medida com volume real.**
7. **A interface não mostra nada disso.** Nenhum arquivo em `web/js/` consome os
   endpoints novos. É escopo da FASE C, mas até lá o dono não vê a FASE A pela
   tela — só pela API.
8. **O app Tauri não foi compilado nem executado nesta sessão** (limitação de
   ambiente já declarada em rodadas anteriores).
9. **O contêiner desta sessão reverteu para snapshots antigos três vezes.**
   Nenhum trabalho foi perdido porque cada incremento foi mergeado em `main`
   antes do seguinte — mas é a razão de eu não acumular trabalho local, e a
   razão de o roteiro v9.25 não estar mais em disco.

---

## Recomendação

Antes de abrir a FASE B, **ligar as três peças órfãs** (A1, A3, A7) a fluxos
reais — ou declarar explicitamente que elas ficam como capacidade disponível até
uma fase posterior. Construir mais capacidade sobre capacidade não usada aumenta
a distância entre o que o projeto **tem** e o que ele **faz**.
