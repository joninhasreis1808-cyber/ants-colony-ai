# AUTOAVALIAÇÃO FINAL — FASES C, D, E, F · Roteiro de Maestria v9.25

> **Base medida:** `main` commit `bb77679` · **1171 passed, 5 skipped**
> **Atualizado em:** `365abc7` · item 4 resolvido · `6b9e0c3` · item 2 resolvido
> **Suite atual:** **1183 passed, 5 skipped**
> **Corrigido:** a base da jornada era **879**, não 887 (ver abaixo).
> **Achado após o fechamento (`4cdd5ba`):** oitavo defeito pré-existente —
> A3 e B1 nunca rodavam na rota real. Ver seção abaixo.
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

## Correção: a base da jornada era 879, não 887

Este documento afirmava `887 → 1171`. O 887 nunca foi medido — foi lembrado, e
estava errado por 8. Rodei o pytest nos dois commits que poderiam ser a base:

    8939e32  (#60, véspera da jornada)  →  879 passed, 5 skipped
    996c68b  (#61, FASE 0)              →  879 passed, 5 skipped

E a auditoria da própria FASE 0 já dizia 879, em três lugares do
`CURRENT_STATE.md`. Eram três testemunhas contra o número que eu escrevi, e
nenhuma delas foi consultada quando escrevi.

Aproveitei para conferir **todos** os outros marcos citados nas três
autoavaliações, em vez de corrigir só o que me incomodou:

| Commit | Marco | Afirmado | Medido |
|---|---|---|---|
| `8939e32` | véspera da jornada | 887 | **879** ❌ |
| `72a6341` | fim do A7 | 962 | **962** ✅ |
| `c70d7d3` | órfãs ligadas | 978 | **978** ✅ |
| `5c8420f` | fim do B6 | 1084 | **1084** ✅ |
| `bb77679` | FASE F | 1171 | **1171** ✅ |

Só o número que eu não tinha medido estava errado. O crescimento real da
jornada é **879 → 1183**, e a regra 3 continua cumprida: nenhum teste foi
enfraquecido para caber.

**Segundo número lembrado, encontrado na mesma tabela:** este documento dizia
"24 PRs", em dois lugares. O `git log` diz **25** no commit que ele descreve
(`bb77679`, PRs #61–#85) e **30** na jornada inteira até `e18397b`. Corrigido
para 30, que é o escopo que o documento passou a cobrir depois das duas
atualizações. A lição é a mesma das duas vezes: **um número que eu não medi é
um palpite com cara de fato.**

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
| 3 | Rede de segurança sagrada | **cumprida** | 879 → 1171. **Nenhum teste enfraquecido para caber** — quando um teste antigo colidiu com minha mudança (B3), adaptei o meu código. |
| 4 | Um commit por tarefa | **cumprida** | **30** PRs até `e18397b`, um por tarefa, todos com CI verde (contados no `git log`, não lembrados). |
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
| I9 | Rito de engenharia | **cumprido** | Nos 30. |

---

## O resultado que eu destacaria acima do número de testes

**Oito defeitos pré-existentes**, nenhum introduzido nesta jornada, nenhum
visível em revisão de código. Todos apareceram pelo mesmo motivo: **uma peça saiu
da prateleira e entrou em uso.**

1. A atenção **deflacionava toda memória gravada** (0.485 no portão, 0.35 no disco)
2. **`calibrate()` não era chamado por ninguém**
3. O feedback do dono **não saía do `/mind`**
4. A síntese do LLM **virava resposta sem verificação**, com confiança 0.9
5. O orçamento do A3 **descartava a única camada com memória real**
6. O token `--dim` **reprovava em contraste em todo fundo, nos dois temas**
7. O rótulo epistêmico **sumia** nas respostas de cache e pesquisa profunda
8. **A3 e B1 nunca rodavam na rota real** — `/hive/task` construía a colmeia
   sem `ltm=`, então `self.ltm` era `None` em toda missão de produção desde que
   as duas peças foram escritas. Consequência maior que A3/B1 sozinhas: a
   colônia **nunca gravou um desfecho de missão** na memória de longo prazo em
   produção — A6 (sono automático) sempre operou sobre um armazém vazio.

O sétimo e o oitavo só apareceram fora do código isolado: o sétimo na validação
ponta a ponta, o oitavo numa auditoria que rodou missões pela ROTA HTTP real em
vez de `build_hive()` chamado à mão — exatamente como todo teste de A3/B1, e a
própria checagem de órfãs desta FASE, já tinham feito. "Ligado a um fluxo" e
"o fluxo real recebe o objeto de que a peça precisa" não são a mesma prova.
Corrigido em `4cdd5ba`, com prova pela rota HTTP real (não só unitária) e
travado por teste: `tests/test_ltm_wiring_producao.py`.

---

## O que NÃO foi verificado

1. **O serviço real no Render — parcialmente melhor, ainda não fechado.** O
   proxy de saída deste ambiente continua negando o CONNECT direto ao host
   (confirmado de novo agora: `curl` ao domínio público devolve 403 do
   gateway). Mas as ferramentas do Render MCP reconectaram nesta sessão, e por
   elas confirmei, ao vivo: o serviço `ants-c2ik` está ativo (plano free,
   região Oregon), o deploy do commit `4cdd5ba` (correção do item 8 acima)
   ficou **live em 33s**, e os logs mostram `GET /health` respondendo `200`
   a cada 5s — o serviço está de pé e saudável agora. O que continua sem
   verificação é a experiência de fora: latência real vista por um usuário,
   comportamento na hibernação do free tier, e uma missão completa rodada
   pela URL pública — o MCP dá visão de operador, não a mesma prova que
   rodar `/hive/task` de fora daria.
2. ~~**O app Tauri não foi compilado nem executado.**~~ **Resolvido**
   (commit `6b9e0c3`). Este limite era de ambiente, e caiu quando as libs de
   sistema do GTK/WebKit puderam ser instaladas. Feito de verdade: `cargo test`
   28/28 no núcleo de segurança, sidecar empacotado (111M) verificado sozinho,
   app compilado (228M, as 6 capacidades do corpo presentes), app **executado**
   sob Xvfb lançando o sidecar em porta dinâmica com segredo de ponte efêmero, e
   uma **missão real rodada dentro do app nativo**. Rodar revelou um defeito que
   nenhum teste pegava: o corpo se declarava `native: false` para a rota do Local
   Agent, porque duas leituras de runtime olhavam variáveis diferentes.
   Corrigido e travado por teste.

   **Ressalva:** rodou sob **Xvfb**, um X virtual — não numa máquina de verdade
   com GPU, gerenciador de janelas e sessão de usuário. A janela abriu e o laço
   funcionou; a experiência de uso real continua não verificada.
3. **O córtex plugável nunca foi exercitado contra um LLM real.** A guarda é
   testada com textos injetados.
4. ~~**Restam 23 blocos que engolem exceção em silêncio.**~~ **Resolvido**
   (commit `365abc7`). Duas correções ao que este documento afirmava: o número
   exato pelo AST era **24**, não 23 — a contagem por `grep` inflava; e eles
   foram diagnosticados **um a um**, não convertidos em bloco. **19** escondiam
   falha real e foram declarados (entre eles o botão de pânico, a persistência
   de permissões e o lançamento de missão). **3** do extractor viraram
   `ImportError` mudo (ausência esperada das libs opcionais na imagem de nuvem)
   + exceção real declarada. **2** ficam mudos de propósito, com o motivo
   escrito no código: `WebSocketDisconnect` (aba fechada é normal) e o parser de
   números do crítico (fluxo do laço). Um registro cheio de ruído é tão inútil
   quanto um vazio.
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
