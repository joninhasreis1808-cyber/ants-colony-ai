# AUTOAVALIAÇÃO — FASE B (IA) · Roteiro de Maestria v9.25

> **Base medida:** `main` commit `5c8420f` · **1084 passed, 5 skipped**
> **Escopo:** B1–B6, seis tarefas, seis PRs (#72, #73, #74, #75, #76, #77).
> Tudo abaixo foi **medido neste commit**, não lembrado.

---

## Aviso de honestidade (o mesmo da FASE A, e ele continua valendo)

**Não tenho o texto literal das 15 perguntas da PARTE VI.** O upload do roteiro
v9.25 sumiu com as reversões de contêiner. As perguntas abaixo são
**reconstruídas** das 6 regras do `PROTOCOLO_COWORK` (literais no repositório) e
dos 9 invariantes. Se o dono reenviar o roteiro, refaço contra o texto literal.

---

## A correção de processo que esta fase trouxe

A autoavaliação da FASE A descobriu, **depois do fato**, que três de sete peças
estavam órfãs — existiam, eram testadas, e nenhum fluxo de produção as chamava.
Nesta fase a checagem foi feita **antes** de declarar a fase fechada:

| Peça | Chamada por |
|---|---|
| B1 · `memory_rag` | `hive.py` |
| B2 · `cross_check` | `hive.py`, `search/verifier.py`, `epistemic_label.py` |
| B3 · `correctness_signal` | `hive.py` |
| B3 · `human_feedback` | `hive.py` |
| B4 · `epistemic_label` | `hive.py` |
| B5 · `feedback_bias` | `hive.py`, `cognition/planner.py` |
| B6 · `cortex_guard` | `hivemind/deep_research.py` |

**Nenhuma órfã.** E o caminho do chat (o que o dono usa) produz as quatro seções
novas numa missão real: `grounding`, `cross_check`, `calibration`, `epistemic`.

---

## Cinco defeitos PRÉ-EXISTENTES achados e corrigidos na causa

Nenhum foi introduzido nesta fase. Todos apareceram porque uma peça saiu da
prateleira e entrou em uso:

1. **A atenção deflacionava toda memória gravada.** `calculate_attention` mutava
   o estado (marcava como visto), e `remember()` a chamava duas vezes: a memória
   passava no portão com 0.485 e era **gravada com 0.35** — mais perto do piso de
   poda e longe do limiar de reforço do sono. (B1)
2. **`calibrate()` não era chamado por ninguém.** O calibrador media a própria
   miopia e guardava na gaveta; a confiança exibida seguia crua. (B3)
3. **O feedback do dono não saía do `/mind`.** Ele podia dizer "nunca use
   web_search" e as missões continuavam usando. (B5)
4. **A síntese do LLM virava resposta sem verificação nem aviso**, com confiança
   0.9. O I3 era convenção, não freio. (B6)
5. **O orçamento do A3 descartava a única camada com memória real** — achado na
   ligação das peças órfãs, antes desta fase (PR #70).

---

## As 6 regras do PROTOCOLO_COWORK

| # | Regra | Veredito | Evidência |
|---|---|---|---|
| 1 | Diagnóstico antes de correção | **cumprida** | Cada incremento abriu lendo o código. O B5 começou constatando que o `FeedbackLearner` só era consultado pelo `/mind`; o B6, lendo as três linhas do `deep_research` que deixavam o LLM escrever a resposta. |
| 2 | Prova executável | **cumprida** | 106 testes novos. A prova do B2 planta uma memória dizendo "2+2 dá 5" e exige que a colônia responda **4** e ainda assim mostre o desacordo. |
| 3 | Rede de segurança sagrada | **cumprida** | 996 → 1084, verde antes e depois de cada PR, em ordem fixa e aleatória. **Nenhum teste enfraquecido para caber** — no B3, quando um teste antigo colidiu com minha mudança, adaptei o meu código. |
| 4 | Um commit por tarefa | **cumprida** | 6 tarefas, 6 PRs, 6 squash-merges. |
| 5 | Declarar o não verificado | **cumprida** | Seção final, e em cada PR. |
| 6 | Interface nunca inventa | **cumprida** | O rótulo epistêmico diz "não medido" em cada eixo sem sinal; o RAG se cala com o número no motivo; o córtex aprovado **também** fica declarado. |

## Os 9 invariantes

| # | Invariante | Veredito | Evidência medida |
|---|---|---|---|
| I1 | Custo zero | **preservado** | `git diff` em `requirements.txt` na fase: **vazio**. |
| I2 | Offline-first | **preservado** | Os módulos novos usam `re`, `math`, `hashlib`, `dataclasses`. O único com rede é o córtex — opcional e desligado. |
| I3 | Sem LLM como cérebro | **preservado e REFORÇADO** | Medido: `backend_name()` devolve `"rules"`, `available_llm()` é `False`. E agora há freio **mecânico**: número ausente das evidências derruba a síntese. |
| I4 | Sem build step | **preservado** | Nada em `web/`. |
| I5 | 4 JS legados imutáveis | **preservado** | MD5 batem com o baseline do `ci.yml`; `git diff` em `web/` na fase: **vazio**. |
| I6 | Segurança do corpo | **preservado** | `git diff` em `backend/local_agent/` e `app/`: **vazio**. |
| I7 | Autoevolução só em DADOS | **preservado** | Nenhum `exec`/`eval`/escrita de `.py`. |
| I8 | Interface nunca inventa dado | **preservado** | Ver regra 6. |
| I9 | Rito de engenharia | **cumprido** | Nos 6. |

---

## O que NÃO foi verificado

1. **Nada da FASE B rodou em produção.** Tudo é teste local + CI.
2. **O córtex plugável nunca foi exercitado com um LLM de verdade.** A guarda é
   testada com textos injetados; nenhuma chamada real a Ollama ou API aconteceu
   neste ambiente. **Não sei como um modelo real se comporta contra ela.**
3. **O detector de contradição do B2 não pega semântica** — "subiu" contra
   "desceu" passa. Está declarado no código e no rótulo, mas é um buraco real.
4. **A guarda do B6 não pega afirmação falsa sem número.** Idem: declarado, e
   ainda assim um buraco real.
5. **O veto do B5 não cobre o caminho do chat**, onde a rota é emergente. Só o
   `own_memory` é vetável ali.
6. **A calibração nunca teve volume real.** As correções foram exercitadas com
   amostras sintéticas.
7. **A interface continua sem mostrar nada disso.** O `epistemic` existe no
   resultado e nenhum arquivo em `web/js/` o lê. É escopo da FASE C.
8. **O app Tauri não foi compilado nem executado** (limite de ambiente, já
   declarado em rodadas anteriores).

---

## Recomendação

O item 7 acima é o mais urgente. A FASE B produziu exatamente o campo que a
interface precisa — um rótulo único, legível, com manchete e limites — e ele
**não aparece na tela**. Seguir para a FASE C agora converte trabalho já feito em
valor visível, em vez de empilhar mais backend que o dono não consegue ver.
