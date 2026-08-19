# Ordem de serviço — Ant's v9.3 → v9.4

> **Instrução de uso:** cole este arquivo no Claude (chat) e peça o plano de execução para
> o Claude Code. Tudo aqui é acionável: caminho, linha, patch e critério de aceite
> verificável. Nada depende de conversa anterior.

**Versão:** 2.0 · **Data:** 17/08/2026 · **Base:** commit `f94edf8` (9.3)

---

## Contexto mínimo

| Item | Valor |
|---|---|
| Repositório | `github.com/joninhasreis1808-cyber/ants-colony-ai` |
| Branch | `main` |
| Commit base | `f94edf8` (9.3 · Segurança) |
| Stack | Python 3.11 · FastAPI · Uvicorn · Docker · JS puro (sem build) |
| Testes | `pytest -q` → **534 passed** — linha de base obrigatória |
| Deploy | Render, plano gratuito, `WEB_CONCURRENCY=1`, autoDeploy na `main` |
| Serviço oficial | **`ants-yeys`** (hoje rodando `d0b5510`, versão 9.2) |
| Prioridade declarada do dono | **usar o projeto no computador (Tauri)** |

**Regras que valem para todas as tarefas** (fonte: `PROTOCOLO_COWORK.md`, na raiz do repo):

1. Diagnóstico antes de correção — reproduza a medição antes de aplicar
2. `pytest -q` roda antes e depois; quem adiciona teste declara o novo total
3. Um commit por tarefa, nunca commit-monstro
4. Todo relatório termina declarando o que **não** foi verificado
5. Interface nunca inventa texto — sem fonte real, declare o vazio honestamente

---

## TAREFA 0 — Adotar o protocolo (fazer primeiro, custa 1 minuto)

O arquivo `PROTOCOLO_COWORK.md` foi criado na raiz. Confirme que está versionado e
referencie-o no `README.md`. É o contrato que mantém a transparência entre sessões.

**Aceite:** arquivo commitado; `README.md` aponta para ele.

---

## TAREFA 1 — Correção de largura no celular

**Prioridade: máxima entre as de front-end.**

### Diagnóstico já feito

Viewport de 390px, medido ao vivo no DOM:

```
header.topbar   → 624px      (tela: 390px)
main.content    → 624px
nav.bottomnav   → 624px
elementos cortados à direita: 98
document.body.scrollWidth === innerWidth → sem rolagem; o conteúdo é CORTADO
```

**Causa raiz.** `#app.ant-shell` (`web/css/design_system.css:27-30`) é `display:grid`,
`height:100dvh`, `overflow:hidden`. Filhos de grid nascem com `min-width:auto` e não
encolhem abaixo do conteúdo mínimo. A `.topbar` é flex e seus filhos somam:

```
brand 99 + state-ind 121 + mode-switch 218 + span 106 = 544
+ gap 12 × 4 = 48
+ padding 16 × 2 = 32
= 624px  ← exatamente a largura medida
```

### Patch

**Arquivo:** `web/css/design_system.css` — acrescentar ao final (394 linhas; nada acima muda)

```css

/* ─── 9.4 · Adaptação a telas pequenas ────────────────────────────────
   Itens de grid nascem com min-width:auto e não encolhem abaixo do
   conteúdo mínimo. A .topbar cravava um piso de 624px que o
   overflow:hidden do shell cortava. Liberar o encolhimento derruba o
   piso. Medido: 98 elementos cortados → 0. Desktop intocado.        */
@media (max-width: 760px){
  .ant-shell > *      { min-width: 0; }
  .topbar             { flex-wrap: wrap; row-gap: 8px; }
  .topbar .state-ind  { white-space: normal; }
  .mode-switch        { flex-wrap: wrap; }
  main.content        { overflow-x: hidden; }
}
```

### Aceite

| Medida (390 × 844) | Antes | Exigido |
|---|---|---|
| `header.topbar` | 624px | ≤ 390px |
| `main.content` | 624px | ≤ 390px |
| `nav.bottomnav` | 624px | ≤ 390px |
| Elementos com `right > innerWidth + 2` | 98 | **0** |
| `pytest -q` | 534 | 534 |

Em 1440px nada pode mudar.

```js
const cortados = await page.evaluate(() =>
  [...document.querySelectorAll('body *')]
    .filter(e => { const r = e.getBoundingClientRect();
                   return r.width > 0 && r.right > innerWidth + 2; }).length);
// exigir: cortados === 0
```

---

## TAREFA 2 — Câmera ao Vivo (JÁ IMPLEMENTADA — revisar e integrar)

**Contexto: esta tarefa já foi construída e testada. O que falta é revisão e commit.**

### O problema que ela resolve

`web/index.html:389-402` contém `#bot-vision-modal`, com os campos:

```html
<div id="bot-vision-status">Ativa</div>
<div id="bot-vision-action">Buscando fontes primárias sobre o tema…</div>
<div class="mv-box"><h5>Log em tempo real</h5><div id="bot-vision-log"></div></div>
```

`web/js/scripts.js:96-104` só preenche `name` e `caste` ao abrir. **"Ação atual" é texto
fixo, igual para todo bot em toda missão. "Log em tempo real" nunca recebe uma linha.**
Um painel rotulado "tempo real" mostrando texto decorativo — exatamente o que a
`AUDITORIA_HONESTIDADE_9.0.md` combateu no resto do sistema.

### O que foi entregue

Dois arquivos **novos** (aditivos, não alteram nenhum existente):

- `web/js/bot_camera.js`
- `web/css/bot_camera.css`

E três pontos de integração em `web/index.html`:

```html
<!-- 1. após a linha do cloud.css -->
<link rel="stylesheet" href="/css/bot_camera.css" />

<!-- 2. logo antes de <details class="colony-rede"> -->
<div id="bot-camera" style="margin:14px 0"></div>

<!-- 3. após <script src="/js/action_ui.js"></script> -->
<script src="/js/bot_camera.js"></script>
```

### Como funciona

- **Fonte de dados:** o `CustomEvent("ants:task-tick")` que o `api_bridge.js` já emite,
  cujo `detail.status.events` é a lista real do backend. **Nenhuma conexão nova é aberta.**
- Deriva o estado de cada bot só de evento real: fases percorridas, situação
  (ativo / concluído / reprovado), último evento, dado manipulado.
- **A câmera troca de alvo sozinha:** segue o primeiro bot que ainda não concluiu.
- O usuário pode **fixar** a câmera num bot clicando no roster, e voltar ao automático.

### O problema encontrado no meio do caminho, e a solução

O backend emite os 22 eventos em milissegundos; o front lê o status agregado a cada 600ms.
**Sem buffer, a câmera pulava do primeiro bot ao último** — medido: apenas `navigator` e
`learner` apareceram, os três do meio ficaram invisíveis.

Solução implementada: uma fila que libera os eventos **reais** um a um, a cada ~380ms,
acelerando (2 ou 3 por pulso) se a fila passa de 7 ou 14. Nada é inventado — só se altera
**quando** cada evento aparece, nunca **o quê**. O cabeçalho declara o modo: "ao vivo",
"reproduzindo · N na fila", ou "trajeto completo".

Medição depois da correção: **5 de 5 bots exibidos, em ordem**, com dado real
(`busca: "..."`, `2 fonte(s) recebida(s)`, `resumo de 236 caracteres`).

### Estado honesto do cache

Quando a missão termina sem nenhum evento de bot, a câmera declara:

> "Resposta recuperada da memória da colônia. Nenhum bot foi recrutado nesta missão — por
> isso não há trajeto para exibir."

Em vez de ficar muda, o que pareceria sistema quebrado.

### Aceite

- Missão com pergunta inédita: os 5 bots aparecem, um por vez, em ordem
- Missão repetida (cache): a mensagem de memória aparece; nada fica mudo
- `pytest -q` → 534 passed (já verificado)
- **Recomendado:** remover ou reconectar o `#bot-vision-modal` antigo, para não haver dois
  painéis competindo, um deles falso

---

## TAREFA 3 — Tornar visível a origem da resposta

**Prioridade: alta. Provavelmente explica a queixa "a interface não conversa com a IA".**

### Diagnóstico

Medição direta, mesmo servidor:

```
"quem é o Batman"  (1ª vez) → 22 eventos → 5 bots trabalham
"quem é o Batman"  (2ª vez) →  1 evento  → NENHUM bot é recrutado
pergunta inédita            → 22 eventos → 5 bots trabalham
```

`backend/memory/answer_cache.py` responde da memória na repetição. Existe ainda um terceiro
caminho: perguntas cobertas pela base própria são respondidas só pela `rainha` ("Colônia
respondeu da base de conhecimento própria").

**São três comportamentos diferentes com aparência idêntica.** O usuário não distingue.

### O que fazer

Um selo visível na resposta, com origem e ação:

| Origem | Selo | Ação oferecida |
|---|---|---|
| Cache | "resposta da memória · repetida" | "buscar de novo" |
| Base própria | "conhecimento interno da colônia" | "procurar na web" |
| Busca externa | "busca na web · N fontes" | fontes já são exibidas |

O backend já tem o dado: `result.provenance.source` traz `web_search` e correlatos.

### Aceite

- Cada resposta exibe sua origem
- Resposta de cache oferece forçar nova busca
- `pytest -q` sem regressão

---

## TAREFA 4 — Abas inalcançáveis no celular

**Prioridade: alta.**

Desktop: Colônia, Cognição, Ambiente, Recursos, Rainha, Factory, Ajustes (7).
Celular: Colônia, Cognição, Rainha, Ajustes (4).

**Ambiente, Recursos e Factory não têm caminho de acesso no telefone.**

Antes de escolher a solução, **localize onde a redução acontece** — CSS (`display:none` em
breakpoint) ou JS (montagem condicional). Não presuma.

Preferência: **menu rolável horizontalmente** com os 7 itens (sem estado novo, sem JS).
Alternativa: botão "mais" com folha inferior.

**Aceite:** as 7 seções alcançáveis por toque em 390px; alvos de 44 × 44 px; desktop
inalterado; 534 testes.

---

## TAREFA 5 — Substituir o polling de 600ms

**Prioridade: alta. Maior ganho de performance disponível.**

`web/js/api_bridge.js:129` → `const poll = setInterval(tick, 600);`
Durante uma missão: **~100 requisições por minuto por aba**.

**O projeto já tem DOIS caminhos melhores, ambos sem uso pelo caminho principal:**

- `backend/api/routes/hive.py:303` — `GET /status/{task_id}/stream` (SSE)
- `backend/api/routes/hive.py:347` — `WebSocket /live/{task_id}` (já usado por `chat.js` e
  `bots.js`, e confirmado nos logs de produção como aceito)

### O que fazer

1. Consumir o WebSocket `/hive/live/{task_id}` como fonte principal do `api_bridge`
2. **Manter o polling como fallback**, ativado só se a conexão falhar — o serviço hiberna
   no plano gratuito
3. Backoff exponencial (1s, 2s, 4s, 8s, teto 30s)
4. Encerrar em `beforeunload` e ao fim da missão

**Atenção:** a Câmera ao Vivo consome `ants:task-tick`. Se a fonte mudar, o evento deve
continuar sendo emitido com o mesmo formato, ou a câmera para de funcionar.

### Aceite

- Requisições durante missão caem de ~100/min para ≤ 5/min
- Com servidor derrubado no meio, degrada para polling sem travar
- Barra de progresso segue monotônica e chega a 100% (conquista do 9.2 — não pode regredir)
- Câmera ao Vivo continua exibindo os 5 bots
- `pytest -q` → 534

---

## TAREFA 6 — Unificar as duas chamadas de saúde

`web/js/app.js:10,52` e `web/js/health_footer.js:27,42` chamam `/health` a cada 15s,
independentemente. Duas requisições onde bastaria uma.

Solução: fonte única distribuindo por `CustomEvent("ants:health")` — padrão já usado no
projeto (`ants:awake`).

**Bônus no escopo:** dos 10 `setInterval` do front, nenhum é limpo em `beforeunload` nem
pausado com a aba em segundo plano. Usar `document.hidden` reduz bateria sem mudar
comportamento visível.

**Aceite:** uma requisição por ciclo; temporizadores pausam em segundo plano; 534 testes.

---

## TAREFA 7 — Remover chamada bloqueante do provedor local

`backend/providers/local_provider.py:69` → `urllib.request.urlopen(req, timeout=30)`

Síncrono, em rota `async`, com **um único worker**: congela a aplicação inteira por até
30s — nem o `/health` responde, e o Render considera o serviço morto.

**Mitigação atual:** `LocalProvider` não está registrado em `backend/providers/router.py`
(que instancia Brave, DuckDuckGo, Tavily e Wikipedia). O código não é alcançado hoje — mas
é armadilha para quem plugar o Ollama.

Trocar por `httpx.AsyncClient` — **já é dependência do projeto**, zero deps novas.

**Aceite:** nenhuma chamada de rede síncrona em caminho async; 534 testes; se não houver
teste cobrindo o provedor, adicionar um com servidor indisponível (declarar novo total).

---

## TAREFA 8 — Corrigir o contador de testes

Rodapé anuncia "529 testes". O real é **534**. Fixo em três lugares:

| Arquivo | Linha |
|---|---|
| `web/index.html` | 61 — `<span id="test-count">529</span>` |
| `web/index.html` | 287 — `<div class="sv" id="stat-tests">529</div>` |
| `web/index.html` | 370 — `<span class="chip">529 testes </span>` |

Corrigir **e** eliminar a classe do problema: expor a contagem via `/health` e deixar o
front consumir. No mínimo, ler de um único ponto.

**Aceite:** nenhum número fixo espalhado; valor bate com `pytest -q`.

---

## TAREFA 9 — Emojis fora do padrão declarado

Os commits declaram "zero emoji", mas existem no código:

| Arquivo | Linha | Conteúdo |
|---|---|---|
| `web/js/bots.js` | 18 | `🤖 ${name}` |
| `web/js/chat.js` | 42 | `🐜 A colmeia está trabalhando...` |

Substituir pelos ícones do sprite SVG, como o resto da interface já faz.

**Aceite:** nenhum emoji em `web/js/` fora de comentário; 534 testes.

---

## TAREFA 10 — Extrair funções longas de `hive.py`

**A mais baixa da lista. Fazer por último, ou não fazer agora.**

`backend/hivemind/hive.py` (520 linhas) concentra as 4 únicas funções acima de 60 linhas
do back-end: `_build_provenance` (102), `_compile_result` (87), `solve` (69),
`_compile_trace` (66).

Mover as três `_compile_*` / `_build_*` para `response_composer` (já existe). **Deixar
`solve` onde está** — 69 linhas é aceitável para o orquestrador, e o risco supera o ganho.

**Aceite:** 534 passed sem alterar nenhum teste; nenhuma mudança de comportamento;
`hive.py` abaixo de 300 linhas.

**Aviso honesto:** este código funciona e está testado. Refatorá-lo antes das tarefas 1 a 5
é otimizar o que não dói.

---

## Ordem recomendada

```
0 → 2 → 1 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10
```

A Câmera (2) vem cedo porque **já está pronta e testada**, e porque ela é o instrumento
que torna visível o comportamento dos bots nas tarefas seguintes.

### Formato de commit

```
9.4 · <Tarefa N>: <o que mudou>

Diagnóstico: <a medição que motivou>
Correção:    <o que foi feito>
Prova:       <medição antes → depois>
Testes:      534 passed (sem regressão)
```

---

## Antes de qualquer deploy — três alertas

**1. Há uma tela branca não diagnosticada em produção.** `ants-7ylk` roda o commit `f94edf8`
(9.3) e renderiza em branco no navegador do dono. `ants-yeys` roda `d0b5510` (9.2) e
funciona. O servidor do 9.3 responde `GET / → 200 OK` sem erro, e o mesmo commit roda
perfeitamente em local. **A causa é do lado do navegador e ainda não foi encontrada.**
Subir o 9.3 no serviço que funciona hoje, sem entender isso, arrisca quebrar o que está de pé.

**Teste barato que ainda não foi feito:** abrir o `ants-7ylk` numa aba anônima do celular.
Se funcionar, é service worker com cache velho. Se continuar branca, é código, e é preciso
o console do aparelho.

**2. O token de segurança do 9.3 não está configurado.** O `/health` de produção responde
`"mode": "open", "token_configurado": false`, com `ipAllowList: 0.0.0.0/0`. A guarda só age
com `ANTS_PUBLIC=1` e `ANTS_API_TOKEN` definidos. Sem isso, publicar o 9.3 **não muda nada
na prática** — `/device`, `/action` e `/permissions` seguem abertas.

**3. Há 8 serviços gratuitos rodando o mesmo repositório**, todos com autoDeploy na `main`:
`ants`, `ants-uoat`, `ants-xt89`, `ants-1c3s`, `ants-y1sj`, `ants-8qb4`, `ants-yeys`,
`ants-7ylk`. Dividem as horas gratuitas. Oficial confirmado pelo dono: **`ants-yeys`**.
Manter o `ants-7ylk` vivo enquanto a tela branca não for diagnosticada — é a evidência.

---

## O que não foi verificado

- **URL pública não acessada** — `robots.txt` bloqueia acesso automatizado. Tudo foi
  verificado rodando o mesmo código localmente, mais logs reais de produção.
- **Busca web real não exercida** — o ambiente de análise bloqueia Wikipedia e DuckDuckGo.
  O pipeline foi validado com provedor injetado; os logs de produção confirmam missões
  reais lá.
- **Tela branca do `ants-7ylk`** — sem diagnóstico.
- **Safari/iOS real** — testes em Chromium com emulação de celular.
- **Sem teste de carga.**
- **Kit de ataque do `SEGURANCA_9.3.md`** não reexecutado.
