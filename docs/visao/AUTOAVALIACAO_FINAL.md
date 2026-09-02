# AUTOAVALIAÇÃO FINAL — FASES C, D, E, F · Roteiro de Maestria v9.25

> **Base medida:** `main` commit `bb77679` · **1171 passed, 5 skipped**
> **Escopo:** o fechamento do roteiro. As FASES A e B têm autoavaliação própria
> (`AUTOAVALIACAO_FASE_A.md`, `AUTOAVALIACAO_FASE_B.md`).
> Tudo abaixo foi **medido neste commit**, não lembrado.

---

## Aviso de honestidade (o mesmo desde a FASE A, e ele continua valendo)

**Não tenho o texto literal das 15 perguntas da PARTE VI.** O upload do roteiro
v9.25 sumiu com as reversões de contêiner — foram **quatro** ao longo da jornada.
As perguntas são **reconstruídas** das 6 regras do `PROTOCOLO_COWORK` (literais
no repositório) e dos 9 invariantes. Se o dono reenviar o roteiro, refaço as três
autoavaliações contra o texto original.

---

## Checagem de órfãs — feita ANTES de declarar

A FASE A me ensinou isso do jeito difícil: descobri **depois** que três de sete
peças não eram chamadas por nenhum fluxo. Desde então a checagem vem primeiro.

| Peça | Fase | Ligada a |
|---|---|---|
| `epistemic_card.js` | C1 | registrado no `index.html`, consome `ants:task-done` |
| `colony_awareness.js` | C2 | registrado no `index.html`, consome 4 endpoints |
| correção do token `--dim` | C3 | `design_system.css`, todo o app |
| severidade de movimento | D | `epistemic_card` + `colony_awareness` |
| `registry.availability` | E | `ToolRegistry.list()` e `/tools/{n}/availability` |
| `silent_failures` | F | 8 arquivos do backend + `/failures` |

**Nenhuma órfã.**

---

## As 6 regras do PROTOCOLO_COWORK

| # | Regra | Veredito | Evidência |
|---|---|---|---|
| 1 | Diagnóstico antes de correção | **cumprida** | A FASE D só existiu na forma que tem porque medi antes: `prefers-reduced-motion` **já funcionava** (15 e 120 → 0 e 0), então não inventei um defeito para consertar. A FASE C3 mediu contraste e teclado com ferramenta antes de tocar em CSS. |
| 2 | Prova executável | **cumprida** | Renderização em Chromium real (C1, C2, D), axe-core em 9 cenas (C3), validação com as deps exatas de produção. |
| 3 | Rede de segurança sagrada | **cumprida** | 887 → 1171. **Nenhum teste enfraquecido para caber** — quando um teste antigo colidiu com minha mudança (B3), adaptei o meu código. |
| 4 | Um commit por tarefa | **cumprida** | 24 PRs, um por tarefa, todos com CI verde. |
| 5 | Declarar o não verificado | **cumprida** | Seção final, e em cada PR. |
| 6 | Interface nunca inventa | **cumprida** | Estado vazio que explica o que falta acontecer (C2); movimento que nunca pisca sem ter mudado (D); "não" com remédio executável (E); falha engolida que aparece (F). |

## Os 9 invariantes

| # | Invariante | Veredito | Evidência medida |
|---|---|---|---|
| I1 | Custo zero | **preservado** | `git diff` em `requirements*.txt` na jornada inteira: **vazio**. |
| I2 | Offline-first | **preservado** | Nenhum módulo novo usa rede. O único que usa é o córtex, opcional e desligado. |
| I3 | Sem LLM como cérebro | **preservado e reforçado** | `backend_name()` = `"rules"`, `available_llm()` = `False`. E o B6 tornou isso **mecânico**. |
| I4 | Sem build step | **preservado** | JS e CSS puros; nenhum `package.json` no front. |
| I5 | 4 JS legados imutáveis | **preservado** | MD5 conferidos aqui e no CI. Toda a FASE C foi feita **por fora** deles. |
| I6 | Segurança do corpo | **preservado** | `git diff` em `backend/local_agent/` e `app/`: **vazio**. |
| I7 | Autoevolução só em DADOS | **preservado** | Nenhum `exec`/`eval`/escrita de `.py`. |
| I8 | Interface nunca inventa dado | **preservado** | Ver regra 6. |
| I9 | Rito de engenharia | **cumprido** | Nos 24. |

---

## O resultado que eu destacaria acima do número de testes

**Sete defeitos pré-existentes**, nenhum introduzido nesta jornada, nenhum
visível em revisão de código. Todos apareceram pelo mesmo motivo: **uma peça saiu
da prateleira e entrou em uso.**

1. A atenção **deflacionava toda memória gravada** (0.485 no portão, 0.35 no disco)
2. **`calibrate()` não era chamado por ninguém**
3. O feedback do dono **não saía do `/mind`**
4. A síntese do LLM **virava resposta sem verificação**, com confiança 0.9
5. O orçamento do A3 **descartava a única camada com memória real**
6. O token `--dim` **reprovava em contraste em todo fundo, nos dois temas**
7. O rótulo epistêmico **sumia** nas respostas de cache e pesquisa profunda

O sétimo só apareceu na validação ponta a ponta. Meus próprios testes não o
pegaram porque verificavam backend e front **separadamente** — nenhum testava o
transporte no meio.

---

## O que NÃO foi verificado

1. **O serviço real no Render.** O proxy de saída deste ambiente nega o CONNECT
   para o host e as ferramentas do Render MCP desconectaram. Validei dependências,
   boot, rotas, autenticação em modo público, missões e interface — **não**
   latência real, hibernação do free tier, nem rede de verdade.
2. **O app Tauri não foi compilado nem executado** em nenhum momento.
3. **O córtex plugável nunca foi exercitado contra um LLM real.** A guarda é
   testada com textos injetados.
4. **Restam 23 blocos que engolem exceção em silêncio** no backend. Converti os
   12 laços vivos das FASES A/B — os que, falhando calados, desligariam recursos
   sem ninguém notar. Os outros 23 são anteriores a esta jornada e continuam
   mudos.
5. **O detector de contradição do B2 não pega semântica**; a guarda do B6 não
   pega afirmação falsa sem número. Declarados no código, e ainda assim buracos.
6. **O veto do B5 não cobre o caminho do chat**, onde a rota é emergente.
7. **A calibração nunca teve volume real.**
8. **Nenhum usuário além de mim exercitou a interface.** Acessibilidade foi
   medida com ferramenta, não com pessoas.

---

## Recomendação

O item 1 é o único que não posso resolver daqui, e é o que mais vale. Tudo o que
esta jornada construiu está apoiado em teste local e em um ambiente de
fidelidade alta — mas **fidelidade alta não é produção**.

O passo de maior retorno agora não é mais código: é **abrir a URL, rodar uma
missão e olhar**. Se algo estiver diferente do que estes documentos afirmam, é
melhor descobrir com uma missão do que com um relatório.
