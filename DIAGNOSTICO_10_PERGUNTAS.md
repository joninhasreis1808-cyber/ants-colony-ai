# Diagnóstico — a colônia pesquisa de verdade ou só repete o que sabe?

> Teste honesto (`PROMPT_teste_10_perguntas_1.md`). Objetivo: descobrir, **com
> prova**, de onde vem cada resposta. Não maquiado: onde a colônia só repetiu
> conhecimento embutido, está dito com todas as letras.

Ambiente do teste: servidor rodando localmente (uvicorn in-process), navegador
real (Chromium/Playwright), 10 perguntas enviadas pelo **chat unificado dentro
da Colônia** (v6.4). Banco limpo por execução.

---

## 1. Instrumento de proveniência (aditivo — nada quebrado)

`POST /hive/task` → `GET /hive/status/{id}` agora expõe, no `result`, um campo
**`provenance`** (aditivo; `sources`, `cognition`, etc. permanecem):

```json
"provenance": {
  "source": "web_search | memory | seed_knowledge | seed_knowledge+memory | reasoning | none",
  "web": "web: 200 ok | web: 403 bloqueado | web: sem resultado | web: nao tentado | web: erro/offline",
  "web_attempts": [{"provider": "duckduckgo", "status": 403, "error": "ProxyError"}],
  "urls": ["dominio.com"],          // domínios reais quando houve web_search
  "confidence": 0.51,
  "castes": ["rainha", "exploradoras", ...],
  "gaps": ["o que faltou", ...]
}
```

Como cada valor é decidido (sem inventar nada):
- **`web_search`** — o `NavigatorBot` trouxe URLs reais dos provedores. Só então.
- **`memory`** — o fato usado veio do grafo/memória recordada (`prior_knowledge`).
- **`seed_knowledge`** — o fato veio do conhecimento inato (`SeedKnowledge`).
- **`reasoning`** — nenhuma peça externa/de memória; inferência própria.
- **`none`** — a colônia **declarou a limitação** (resposta = "Não tenho
  evidências suficientes…" + nota de honestidade).
- **`web:`** — status **real** da tentativa externa. O `ProviderRouter` passou a
  registrar o desfecho de cada provider (código HTTP quando existe; para erros de
  proxy/conexão, o código é extraído do texto — ex.: `403`).

Alterações **somente no backend, 100% aditivas** (4 arquivos, +121 linhas, 0
remoções): `providers/router.py`, `bots/navigator.py`,
`hivemind/cognitive_fallback.py`, `hivemind/hive.py`. Os **4 JS legados**
(chat/bots/memory/factory) têm **MD5 idêntico**. Testes: **385 passando**
(382 + 3 novos, nada quebrado).

---

## 2. Tabela-resumo honesta

| # | Pergunta | Source real | Buscou na web? (status) | Confiança | Resposta correta/útil? |
|---|----------|-------------|--------------------------|-----------|-------------------------|
| 1 | feromônios | `seed_knowledge` | sim, mas **403 bloqueado** | 0.51 | **Parcial** — respondeu sobre *castas*, não sobre feromônios em si. |
| 2 | eleição EUA (atual) | `none` | sim, mas **403 bloqueado** | 0.15 | **Honesta** — declarou que não tem como saber offline. |
| 3 | √2809 (cálculo) | `seed_knowledge` | sim, mas **403 bloqueado** | 0.51 | **Não** — **não calculou 53**; devolveu uma frase inata solta. |
| 4 | relatividade | `none` | **não tentou** | 0.15 | **Honesta** — declarou limitação (não tem no seed). |
| 5 | cotação do dólar (atual) | `seed_knowledge` | sim, mas **403 bloqueado** | 0.50 | **Não** — frase inata irrelevante + nota de honestidade. |
| 6 | algoritmo de Dijkstra | `none` | sim, mas **403 bloqueado** | 0.15 | **Honesta** — não tem Dijkstra no seed; declarou. |
| 7 | notícias da semana (atual) | `none` | sim, mas **403 bloqueado** | 0.15 | **Honesta** — declarou que não sabe offline. |
| 8 | colônia sem chefe central | `seed_knowledge` | sim, mas **403 bloqueado** | 0.51 | **Sim** — resposta correta e no domínio (coordenação emergente). |
| 9 | CEP Av. Paulista 1578 (atual) | `seed_knowledge` | sim, mas **403 bloqueado** | 0.50 | **Não** — frase inata irrelevante + nota de honestidade. |
| 10 | plano p/ organizar downloads | `none` | sim, mas **403 bloqueado** | 0.15 | **Não** — devia raciocinar 4 passos; declarou limitação. |

### Respostas francas às 4 perguntas

**Em quantas das 10 a colônia realmente buscou fora (navegador/rede)?**
**Zero.** Em nenhuma resposta entrou informação vinda da web. Em 9 das 10 houve
**tentativa real** de busca externa (o backend chamou o DuckDuckGo), mas **todas
bateram em `403 bloqueado`** (o proxy de egresso do ambiente barra a saída — a
requisição nem chega ao buscador). A pergunta 4 nem chegou a tentar (o roteador
de intenção não recrutou o explorador para aquela frase).

**Em quantas ela só repetiu seed/memória?**
**5** (perguntas 1, 3, 5, 8, 9) foram respondidas com `seed_knowledge` — frases
inatas. Dessas, só **2 são realmente úteis** (1 parcial, 8 correta); as outras 3
(3, 5, 9) devolveram uma frase inata **desconexa** da pergunta. **Nenhuma** veio
de `memory` (o grafo estava vazio no teste). As outras **5** (2, 4, 6, 7, 10)
foram `none` — a colônia **declarou honestamente** que não tinha como responder.

**Nas perguntas atuais (2, 5, 7, 9), ela conseguiu, errou ou foi honesta?**
- **2 (eleição)** e **7 (notícias)** → **honesta**: "não tenho como saber offline".
- **5 (dólar)** e **9 (CEP)** → **erraram o alvo**: devolveram uma frase inata
  irrelevante, mas **com nota de honestidade** avisando que não verificou na web.
- Em **nenhuma** das 4 ela conseguiu o dado atual — porque a web está bloqueada.

**A busca web existe e funciona, existe mas falha, ou não está implementada?**
**Existe e está implementada, mas FALHA por bloqueio (403) neste ambiente.**
Há uma cadeia real de provedores (`Tavily → Brave → DuckDuckGo`) com
`httpx`. O DuckDuckGo (grátis, sem credencial) é sempre tentado; o proxy do
sandbox responde **403 Forbidden** ao CONNECT de saída. Com Tavily/Brave (via
chave de API) ou fora do sandbox, a busca real funcionaria — e o `provenance`
marcaria `source: web_search` com os domínios.

---

## 3. Prova capturada

- **Proveniência por pergunta:** `provenance` real de cada uma (tabela acima),
  extraída de `GET /hive/status/{id}`.
- **Screenshots** do chat unificado dentro da Colônia (10, `q01`–`q10`) mostrando
  a resposta final + confiança, e a **Linha do Tempo viva** (`Registro Vivo`)
  renderizando os eventos reais (task created → bot recruited → plan created →
  research completed → decision taken).
- **Log de rede do navegador:** as **únicas** saídas do navegador foram para
  `127.0.0.1` (117 chamadas: `/hive/task`, `/hive/status/*`, `/events/*`,
  `/colony/*`, `/organism/*`, assets) **+ 1** folha de estilo do Google Fonts
  (fonte, não busca). **Nenhuma** chamada de busca partiu do navegador.
  → A tentativa de web é **server-side** (backend → duckduckgo → 403), o que o
  `provenance.web` registra fielmente.

## Conclusão sem maquiagem

A colônia **não pesquisou na web em nenhuma das 10** — não porque não saiba
tentar, mas porque o egresso está **bloqueado (403)** aqui. Quando não tem
evidência externa, ela **não inventa**: ou repete uma frase inata do
`seed_knowledge` (útil só quando a pergunta cai no domínio de formigas/colônia —
1 e 8; desconexa fora dele — 3, 5, 9), ou **declara honestamente a limitação**
(2, 4, 6, 7, 10). O `seed_knowledge` é claramente **especializado no domínio da
própria colônia**, não em conhecimento geral: por isso √2809, Dijkstra,
relatividade e planejamento genérico ou saem errados ou são recusados. **Não há
raciocínio numérico/geral real** por trás das respostas — há recuperação de
frases inatas + uma camada honesta que admite quando não sabe.
