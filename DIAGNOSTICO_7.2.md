# Ant's 7.2 — o que mudou e a prova

> Consolida busca+raciocínio+honestidade, restaura o progresso vivo do chat,
> redesenha as castas em formações e adiciona as ferramentas de **ler/ver a
> tela**. Tudo aditivo, testado, com os 4 JS legados intactos por MD5.

## Blocos entregues

### A · Progresso vivo do chat (restaurado)
**Causa real (diagnóstico):** o motor de progresso (`api_bridge.js` →
`#research-flow`) pintava as etapas num elemento **escondido** pela unificação
6.4 (`.colony-unified #research-flow{display:none!important}`). O chat só
mostrava o balão legado "trabalhando…" imóvel. **Correção:** novo
`live_progress.js` (não-legado) renderiza as etapas **reais** passo a passo no
chat (ícone da fase + bot + o que fez, spinner→✓) a partir dos eventos que a
ponte já lê de `/hive/status`; ao concluir, colapsa num resumo clicável
("N etapas · N castas · confiança X · fonte"). SW `v11→v12` força o refresh.

### B · 6 castas-base + formações da Rainha
`castes_base.py` (exploradores, construtores, coletores, costureiros,
operárias, soldados) — versáteis, com camada de compatibilidade para as castas
antigas (não quebra testes/rotas). `formation.py`: a Rainha decide a formação
por objetivo, **batiza cada bot** (o handle limita o escopo), põe o **soldado à
frente**, paraleliza por caminho, `reinforce +1`, `release` **nunca abaixo de
1**, **soldado-sacrifício** (isola ameaça via `immune_system` e reporta), e os
**coletores compilam e enviam à Mente Colmeia** antes de concluir. Endpoints
`GET /hive/formations`, `POST /hive/formation[/{id}/reinforce|release|complete]`,
`DELETE /hive/formation/{id}` (só após concluída).

### C · Painel de Formações na Cognição
`formations_panel.js` (dados reais): por formação, nome+objetivo; por bot,
ícone SVG da casta + nome de missão + o que faz; **Recrutar +1** / **Dispensar
−1** (desabilita em 1), "Missão concluída — enviada para o Chat" e o **X** só
após conclusão.

### D · Córtex determinístico + porta de relevância
`reasoning/deterministic.py`: cálculo **exato**, offline, sem `eval` (SymPy) —
raiz, aritmética, %, potência; roteado **antes** da busca; vira
`source: computation`. `cognitive/relevance_gate.py`: não solta mais seed
inato irrelevante; em pergunta de dado atual/externo sem web, **declara
limitação** honesta (`source: none`).

### Adição do dono · ler/ver/entender a tela
`perception/screen_reader.py` + `POST /perceive/screen/dom` e
`/perceive/screen/image`: lê o DOM/HTML (localiza botões/campos/links, texto,
títulos), lê captura de tela por **OCR** (Tesseract), **compreende** o texto e
**propõe o plano de ação** guiado por objetivo. Honesto: ler/entender a tela é
**real no servidor**; **executar** clique/digitação num dispositivo é
**capacidade declarada** (app nativo). `GET /organism/capabilities` lista o que
roda offline vs. o que depende de web vs. o que é declarado.

## 10 perguntas — antes × agora (mesmo ambiente, web 403)

| # | Pergunta | Antes | Agora | Correção |
|---|----------|-------|-------|----------|
| 1 | feromônios | seed | `seed_knowledge` | mantém (correto) |
| 2 | eleição EUA | none | `none` | honesto |
| 3 | **√2809** | seed (não calculava) | **`computation` → 53** | ✔ corrigido |
| 4 | relatividade | none | `none` | honesto |
| 5 | **cotação dólar** | seed irrelevante | **`none` (declara)** | ✔ corrigido |
| 6 | Dijkstra | none | `none` | honesto |
| 7 | notícias | none | `none` | honesto |
| 8 | colônia sem chefe | seed | `seed_knowledge` | mantém (correto) |
| 9 | **CEP Paulista** | seed irrelevante | **`none` (declara)** | ✔ corrigido |
| 10 | plano downloads | none | `none` | honesto (ver nota) |

**Nota honesta:** a pergunta 10 (planejamento puro) ainda declara limitação —
o córtex determinístico cobre cálculo, não planejamento genérico; preferimos
declarar a inventar. A busca web continua **existente e implementada, mas
bloqueada por 403** neste ambiente (o proxy barra o egresso). Fora do sandbox
ou com chave Tavily/Brave, uma pergunta atual viraria `web_search` com fonte.

## Contrato
- **407 testes** passando (base 385 + 22 novos), `pytest -q` verde.
- MD5 dos 4 JS legados **idênticos**: chat/bots/memory/factory.
- Zero emojis (só SVG), zero mockup, offline-first, aditivo.
