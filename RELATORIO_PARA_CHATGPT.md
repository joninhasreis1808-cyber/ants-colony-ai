# Ant's — Dossiê de contexto para consulta ao ChatGPT

> **Instrução de uso:** cole este arquivo inteiro no ChatGPT e peça as respostas da
> Seção 8. O documento é autossuficiente — quem o lê não precisa do repositório nem de
> conversa anterior. Se o ChatGPT pedir contexto, ele não leu; mande ler de novo.

**Versão:** 2.0 · **Data:** 17/08/2026 · **Base:** commit `f94edf8` (9.3)

---

## 1. O projeto

**Ant's — Colônia de Bots** (`ants-colony-ai`). Aplicação web que se apresenta como
"superorganismo digital": em vez de um chatbot único, o sistema é uma colônia de castas
especializadas coordenadas por mecanismo inspirado em feromônios.

O usuário descreve um objetivo em linguagem natural. A colônia lê a intenção, recruta as
castas apropriadas, e cada bot executa um ciclo `plan → do → check → act`, passando o
bastão ao próximo. A resposta sai com selo de proveniência.

**Valor declarado do projeto, visível nos nomes de arquivo** (`AUDITORIA_HONESTIDADE_9.0.md`,
`DIAGNOSTICO_10_PERGUNTAS.md`): a interface não deve mostrar dado falso. Painéis sem fonte
real foram removidos em vez de preenchidos com enfeite.

**Objetivo principal do dono:** usar o projeto no computador (aplicativo nativo via Tauri).

---

## 2. Arquitetura e números verificados

### Back-end
- **Python 3.11 · FastAPI · Uvicorn** — 22.464 linhas, **84 rotas**
- **Docker** no **Render**, plano gratuito, `WEB_CONCURRENCY=1` (um único worker)
- **25 módulos** ativos no `/health`
- **Provedores de busca:** Wikipedia, DuckDuckGo, Brave, Tavily (cascata com fallback)
- **534 testes** passando em 21,9s

### Front-end
- **JavaScript puro, sem framework, sem build step** — 30 arquivos, ~186 KB
- 4 folhas de estilo (~57 KB), `index.html` de 36 KB
- PWA com service worker (stale-while-revalidate)
- 7 seções: Colônia, Cognição, Ambiente, Recursos, Rainha, Factory, Ajustes

### Nativo
- **Tauri (Rust)** em `app/src-tauri/` — o alvo principal do dono

---

## 3. O pipeline de bots — verificado em execução

Missão real disparada e observada por dentro. Pergunta: *"me explique em detalhes quem é
o Batman"*. Resultado: **22 eventos**, cinco bots, cadeia completa.

| Bot | Casta | Papel |
|---|---|---|
| `navigator` | exploradoras | procura fontes na web |
| `extractor` | operárias | extrai texto das fontes |
| `interpreter` | operárias | interpreta o extraído |
| `decider` | rainha | decide a resposta final |
| `learner` | cuidadoras | guarda o aprendizado |

Cadeia de recrutamento registrada pelo próprio sistema:

```
rainha → navigator, extractor, interpreter, decider, learner   (recrutamento)
navigator → extractor → interpreter → decider → learner        (passagem de bastão)
```

Com provedor de busca funcional, a resposta saiu correta, com **confiança 0.9**, duas
fontes citadas e proveniência `web: 200 ok`.

**Veredito: o pipeline funciona e é rastreável.** Isto não é opinião — é o trajeto real
lido do backend.

---

## 4. Descoberta importante: o cache invisível

Medição direta, mesmo servidor, três disparos:

```
"quem é o Batman"  (1ª vez) → 22 eventos → 5 bots trabalham
"quem é o Batman"  (2ª vez) →  1 evento  → NENHUM bot é recrutado
pergunta inédita            → 22 eventos → 5 bots trabalham
```

Existe um cache de respostas (`backend/memory/answer_cache.py`). Na repetição, a colônia
responde da memória e **nenhum bot roda**. Para quem olha a tela, o sistema parece morto.

Há ainda um segundo caminho: perguntas cobertas pela base de conhecimento própria são
respondidas pela `rainha` sozinha, sem busca externa ("Colônia respondeu da base de
conhecimento própria").

**Consequência de produto:** o usuário não tem como distinguir "respondeu do cache",
"respondeu da memória interna" e "buscou na web". Três comportamentos diferentes,
aparência idêntica.

---

## 5. Diagnóstico técnico — 9 achados verificados

Auditoria feita com a aplicação **em execução**: navegador real, medição ao vivo no DOM,
suíte de testes completa. Não é leitura estática.

| # | Achado | Severidade | Evidência |
|---|---|---|---|
| 1 | `.topbar` crava 624px de largura mínima em tela de 390px; `overflow:hidden` do shell corta o resto | **Alta** | 98 elementos medidos fora da tela, sem rolagem |
| 2 | Um único breakpoint de celular no CSS inteiro, e ele só reposiciona um rodapé | **Alta** | 8 media queries: 3 de movimento reduzido, 2 de `min-width` |
| 3 | Três das sete abas somem no menu de celular | Média | Desktop: 7 itens. Celular: 4 |
| 4 | Painel "Visão do bot" exibia texto fixo rotulado como "tempo real" | **Alta** | `#bot-vision-modal` com "Buscando fontes primárias sobre o tema…" fixo; nenhum JS o alimentava |
| 5 | Cache responde sem recrutar bot, sem avisar o usuário | Média | 22 eventos → 1 evento na repetição |
| 6 | Polling de 600ms (~100 req/min) com rota SSE pronta e sem uso | Média | `api_bridge.js:129`; existe `/hive/status/{id}/stream` e WebSocket `/hive/live/{id}` |
| 7 | `urllib` síncrono em rota async, com 1 worker | Média | `local_provider.py:69`, `timeout=30` |
| 8 | 4 funções acima de 60 linhas, todas em `hivemind/hive.py` | Baixa | Máxima: 102 linhas |
| 9 | Rodapé exibe "529 testes"; o real é 534 | Cosmética | Valor fixo em 3 pontos do `index.html` |

### A raiz do achado 1, com a aritmética

Filhos da `.topbar`, medidos ao vivo: 99 + 121 + 218 + 106 = 544px, mais 48px de
espaçamento (4 × 12) e 32px de margem interna (2 × 16) = **624px exatos**.

Itens de grid nascem com `min-width: auto` e não encolhem abaixo do conteúdo mínimo.
A topbar crava esse piso, os irmãos acompanham, e o `overflow:hidden` do shell corta.

**Correção verificada:** 6 linhas de CSS em media query de 760px levaram os elementos
cortados de **98 para 0**, sem alterar o desktop.

---

## 6. O que já foi construído nesta rodada

**Câmera ao Vivo** (`web/js/bot_camera.js` + `web/css/bot_camera.css`, aditivos).
Substitui o painel de texto fixo do achado 4. Mostra, um bot por vez: nome, casta, papel,
fase do ciclo, ação atual com o dado real na mão, e o log de eventos daquele bot. A câmera
troca de alvo sozinha quando um bot conclui; o usuário pode fixá-la clicando.

**Problema encontrado durante o desenvolvimento, e resolvido:** o backend emite os 22
eventos em milissegundos, e o front lê o status agregado a cada 600ms — a câmera pulava do
primeiro bot ao último e os do meio ficavam invisíveis. Foi necessário um buffer que
libera os eventos reais em ritmo legível (~380ms cada), acelerando se a fila cresce. O
cabeçalho declara honestamente se está "ao vivo" ou "reproduzindo".

Verificado: 5 de 5 bots exibidos, em ordem, com dado real. 534 testes seguem passando.

---

## 7. Restrições que toda recomendação precisa respeitar

Não são preferências — são limites do projeto hoje:

- **Plano gratuito do Render**: 512 MB de RAM, um worker, hibernação por inatividade
- **Front-end sem build step**. Não há webpack, vite nem npm no fluxo do front.
  Introduzir pipeline de build é decisão de arquitetura, não detalhe.
- **Sem framework de UI.** JS puro. Migrar seria reescrita.
- **Sem banco gerenciado.** Persistência em arquivo/memória.
- **Custo zero é requisito.** Sugestão paga precisa vir com preço declarado e alternativa
  gratuita.
- **534 testes** são a rede de segurança.
- **O alvo principal é o aplicativo de computador (Tauri)**, não a versão web.

---

## 8. Perguntas para o ChatGPT

Exija respostas **específicas e justificadas**. Para cada recomendação: o que resolve, o
custo real, o esforço de integração, e por que é melhor que a alternativa óbvia.

### Sobre o aplicativo de computador (prioridade máxima do dono)
1. Para empacotar uma app FastAPI + front-end estático dentro de um binário Tauri, qual a
   melhor estratégia de inicialização do processo Python? Compare: binário PyInstaller
   embutido, sidecar do Tauri, e servidor externo. Considere tempo de partida e tamanho.
2. Como distribuir esse aplicativo para Windows sem certificado de assinatura pago, sem que
   o SmartScreen bloqueie o usuário? Que caminhos existem com custo zero?
3. Qual a forma mais robusta de a app nativa descobrir uma porta livre e informá-la ao
   front, em vez de fixar uma porta que pode estar ocupada?

### Sobre transparência do comportamento da IA
4. Que padrões de interface existem para deixar claro ao usuário a **origem** de cada
   resposta (cache, memória interna, busca externa)? Cite produtos reais que resolvem isso
   bem e descreva o padrão.
5. Como projetar cache de respostas que não pareça sistema travado — invalidação, aviso
   visual, opção de forçar nova busca? Qual o padrão de mercado?

### Sobre qualidade de front-end
6. Que ferramenta gratuita detecta automaticamente quebra de layout em celular (elementos
   fora da viewport, sobreposição, alvo de toque pequeno) e roda em CI, sem exigir build
   step? Compare ao menos três.
7. Como montar teste de regressão visual em projeto de JS puro, com custo zero, lidando
   com falsos positivos de renderização?
8. Existe forma de testar WebKit/iOS de verdade em CI gratuito, ou emulação em Chromium é
   o teto realista?

### Sobre tempo real
9. Para app com **um único worker** no plano gratuito, o que é mais robusto: SSE, WebSocket
   ou long polling? Considere hibernação e reconexão. O projeto tem os três caminhos
   disponíveis e usa o pior deles.
10. Como implementar reconexão com backoff exponencial em JS puro, de forma que a interface
    nunca fique presa quando o servidor hiberna?

### Sobre observabilidade
11. Que ferramenta gratuita captura erro de JavaScript no navegador do usuário final
    (incluindo tela branca) com stack trace remoto? Compare planos gratuitos reais, não trial.
12. Como instrumentar um PWA para distinguir "service worker serviu cache velho" de "erro
    de código"?

### Sobre MCP
13. Qual o caminho mais curto para expor uma app FastAPI existente como servidor MCP remoto,
    com OAuth funcionando com clientes reais? Que bibliotecas Python existem e qual a
    maturidade delas?

### Sobre processo
14. Que prática trava "regressão recorrente" — um bug já consertado duas vezes que voltou?
    Que tipo de teste impede esse padrão especificamente?

---

## 9. O que NÃO perguntar

- Recomendação de framework de front-end (migração está fora de escopo)
- Serviço pago sem alternativa gratuita
- Reescrita de arquitetura do back-end (está limpo: 4 funções longas em 22 mil linhas)
- Ferramenta que exija build step no front sem justificar o custo dessa mudança

---

## 10. O que não foi verificado

Limite explícito desta análise, conforme a Regra 5 do `PROTOCOLO_COWORK.md`:

- **A URL pública não foi acessada.** O `robots.txt` do serviço bloqueia acesso
  automatizado. Tudo foi verificado rodando o mesmo código em ambiente local, mais os logs
  reais de produção.
- **A busca web real não foi exercida** — o ambiente de análise bloqueia Wikipedia e
  DuckDuckGo. O pipeline foi validado com provedor injetado. Os logs de produção
  confirmam que missões reais rodaram lá (`POST /hive/task 200`, WebSocket aceito).
- **Tela branca do `ants-7ylk`**: sem diagnóstico. Falta o console do navegador afetado.
- **Safari/iOS real**: testes usaram Chromium com emulação. O motor do iPhone é WebKit.
- **Nenhum teste de carga** foi feito.
- **O kit de ataque do `SEGURANCA_9.3.md`** não foi reexecutado.
