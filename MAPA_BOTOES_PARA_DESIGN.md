# Ant's — Mapa de Botões e Funcionalidades (base para o Claude Design)

> Traduz o contrato do backend em **telas, botões e o que cada um faz**. Cada
> função aqui é REAL (existe no backend, verificada). Use como base para desenhar
> a nova interface. Regra de ouro: **cada botão chama um endpoint real** — nada
> decorativo. O backend NÃO muda; a interface nova conversa com ele.

---

## PRINCÍPIOS DE DESIGN (não negociáveis do projeto)
- **Zero emojis** — só ícones SVG profissionais e coesos.
- **Zero dados falsos** — dado ausente aparece como "—", nunca um número inventado.
- **Offline-first** — se um endpoint falha, a área mostra "colônia adormecida", não trava.
- **Honestidade visual** — nada na tela que não reflita algo real do backend.
- **Respeitar `prefers-reduced-motion`**; console sem erros.
- Identidade própria (não imitar ChatGPT/Claude/Manus). Tipografia atual: Newsreader + IBM Plex Mono (livre para redesenhar).

---

## TELA 1 — CHAT (o coração; tela inicial)

**A função central: mandar um objetivo e ver a colônia trabalhar ao vivo.**

| Elemento | O que faz | Endpoint real |
|---|---|---|
| **Campo de texto** (id `chat-input`) | onde o usuário digita o objetivo/pergunta | — |
| **Botão Enviar** (id `chat-send`) | dispara a tarefa; mostra o "eco" imediato | `POST /hive/task` |
| **Área de mensagens** (id `messages`) | histórico da conversa (usuário + colônia) | — |
| **Barra de progresso** | mostra a colônia trabalhando: fase plan→do→check→act, sempre 0→100 | `GET /hive/status/{id}` (ou SSE/WS) |
| **Linha do tempo viva** (embutida no chat) | cada passo aparece: casta + o que descobriu + quem acionou + horário | eventos de `GET /hive/status/{id}` |
| **Selo de proveniência** (em cada resposta) | mostra a ORIGEM: "cálculo" / "memória" / "web (N fontes)" / "raciocínio" / "não sei" | `result.provenance.source` |
| **Fontes clicáveis** | quando veio da web, links das fontes | `result.sources[]` |
| **Botão "Como cheguei nisso?"** | abre o raciocínio real (confiança, fatos, lacunas) | `result.gaps`, `result.confidence` |
| **Botão "Aprender isto"** | consolida a resposta na memória (aprende p/ próxima vez) | `POST /hive/learn` |
| **Chips de sugestão** (opcional) | atalhos: "Pesquisar…", "Calcular…", "Criar app…" | preenchem o campo |

*Nota de design:* a linha do tempo viva é o diferencial — estilo assistente (passos revelados um a um, colapsando num resumo ao fim: "7 etapas · 3 castas · confiança 0.82").

---

## TELA 2 — COLÔNIA / FORMAÇÕES (a Rainha coordenando)

**Mostra as castas trabalhando em formações, e deixa o usuário ajustar.**

| Elemento | O que faz | Endpoint real |
|---|---|---|
| **Painel de formações** | lista as formações ativas: nome, objetivo, bots | `GET /hive/formations` |
| **Card de cada bot** | ícone da casta + nome de missão + o que faz agora | idem |
| **Botão "Recrutar +1"** | Rainha envia +1 bot do tipo → acelera | `POST /hive/formation/{id}/reinforce` |
| **Botão "Dispensar −1"** | remove 1 bot (NUNCA abaixo de 1 — desabilita em 1) | `POST /hive/formation/{id}/release` |
| **Aviso "Missão concluída"** | aparece ao terminar; some ao descartar | `result` da formação |
| **Botão X (descartar)** | remove a formação (só após concluída) | `DELETE /hive/formation/{id}` |
| **Enxame ao vivo** | visualização dos bots + feromônios + estado de cada um | `GET /hive/swarm` |
| **Cadeia "quem chamou quem"** | árvore de recrutamento de uma tarefa | `GET /hive/recruitment/{id}` |

*As 6 castas (ícones distintos, cores próprias):* Exploradores, Construtores, Coletores, Costureiros, Operárias, Soldados.

---

## TELA 3 — COGNIÇÃO (o pensamento da IA)

| Elemento | O que faz | Endpoint real |
|---|---|---|
| **9 camadas cognitivas** (barras) | ativação de cada camada (planner, researcher, critic…) | `POST /mind/think` |
| **Hipóteses / lacunas / confiança** | o que a colônia considerou e o que faltou | `POST /mind/think`, `/reason`, `/assess` |
| **Meta-cognição** | gargalos e pesos que a colônia ajustou em si mesma | `GET /colony/meta` |
| **Observabilidade** | decisões recentes com o motivo real | `GET /colony/observability` |
| **Eventos do sistema nervoso** | atividade interna ao vivo | `GET /events/summary`, `/events/history` |

---

## TELA 4 — MEMÓRIA (o que a colônia sabe e aprende)

| Elemento | O que faz | Endpoint real |
|---|---|---|
| **Campo de busca** (id `mem-search`/`mem-query`) | procura na memória da colônia | `POST /memory/recall` |
| **Lista de memórias** (id `mem-list`) | mostra o que foi lembrado | idem |
| **Estatísticas** (id `mem-stats`) | total, memórias fortes, força média | `GET /memory/health` |
| **Botão "Ciclo de sono"** (id `mem-sleep`) | consolida o importante, decai o irrelevante | `POST /memory/sleep` |
| **Botão "Ensinar um fato"** | grava conhecimento novo manualmente | `POST /memory/remember` |

---

## TELA 5 — FACTORY (criar software)

| Elemento | O que faz | Endpoint real |
|---|---|---|
| **Seletor de modelo** (id `fac-template`) | 6 modelos: api_rest, web_app, cli_tool, data_pipeline, saas_dashboard, mobile_app | `GET /factory/templates` |
| **Campo de descrição** (id `fac-desc`) | descreve o app desejado | — |
| **Botão "Criar"** (id `fac-create`) | gera o projeto | `POST /factory/create` ou `/quick` |
| **Resultado** (id `fac-result`) | arquivos gerados, status | `GET /factory/projects/{id}` |
| **Lista de projetos** | projetos já criados | `GET /factory/projects` |
| **Botão "Deploy"** | publica um projeto | `POST /factory/deploy/{id}` |

---

## TELA 6 — DISPOSITIVO / AÇÕES (o app nativo agindo)

**Só executa no app nativo; no modo web, apenas planeja (mostrar o selo honesto).**

| Elemento | O que faz | Endpoint real |
|---|---|---|
| **Selo de runtime** | "modo nativo — posso agir" vs "modo web — só planejo" | `GET /device/runtime` |
| **Toggles de permissão** (7 escopos) | ler/escrever arquivos, abrir apps, controlar input, capturar tela, comandos, rede | `GET/POST /device/scopes` |
| **Pastas autorizadas** | adicionar/remover pastas que a colônia pode acessar (whitelist) | `GET/POST /device/paths` |
| **Plano de ação** | mostra os passos ANTES de executar | `POST /device/evaluate` |
| **Botões Aprovar / Cancelar** | autoriza ou cancela o plano | `POST /hive/action/approve` · `/cancel` |
| **BOTÃO DE PÂNICO** (sempre visível) | congela tudo + revoga permissões na hora | `POST /device/panic` |
| **Trilha de auditoria** | tudo que a colônia fez no dispositivo (exportável) | `GET /device/audit` · `/audit/export` |

*Design crítico:* ações destrutivas exigem confirmação clara; o botão de pânico é fixo e destacado (borda de alerta).

---

## TELA 7 — ORGANISMO / SINAIS VITAIS (a colônia viva)

| Elemento | O que faz | Endpoint real |
|---|---|---|
| **Estado da colônia** (respiração) | dormant/observing/exploring/building/verifying/learning/defending/executing | `GET /colony/state` |
| **Sinais vitais** | hormônios, ritmo circadiano, energia | `GET /organism/vitals` |
| **Capacidades reais** | o que a IA sabe fazer AGORA | `GET /organism/capabilities` |
| **DNA / genoma** | traços aprendidos da colônia | `GET /organism/dna` |
| **Tradições / cultura** | boas práticas consolidadas | `GET /organism/traditions` |
| **Confiança (trust)** | reputação por bot/estratégia | `GET /organism/trust` |
| **Missões permanentes** | tarefas contínuas (criar/remover) | `GET/POST /organism/missions` |
| **Observador do host** | duplicatas, backup atrasado, disco cheio | `GET /organism/observer` |
| **Autonomia** (seletor) | Cautelosa / Supervisionada / Autônoma | `GET/POST /colony/autonomy` |

---

## TELA 8 — AJUSTES

| Elemento | O que faz | Endpoint real |
|---|---|---|
| **Tema** (id `theme-toggle`) | claro/escuro | — |
| **Perfis** | Usuário / Desenvolvedor / Cientista (nível de detalhe) | — |
| **Permissões de dispositivo** | (espelha a Tela 6) | `/device/scopes` |
| **Saúde do sistema** (id `health-info`) | status, módulos ativos, postura de auth | `GET /health` |
| **Feedback** (5 tipos por decisão) | 👍 funcionou / 👎 não / ensinar / tornar padrão / nunca faça | `POST /organism/feedback` |

*(Feedback: usar ícones SVG, não emojis, na UI final.)*

---

## O UI KERNEL (como a IA mexe na interface, com segurança)

A interface pode receber comandos da IA por um conjunto FECHADO de ações (nunca HTML arbitrário). Útil para animações reagirem ao que a colônia faz:

| Ação | Efeito visual |
|---|---|
| `highlight` | realça uma casta/seção por instantes |
| `update_progress` | move a barra de progresso (0-100) |
| `open_section` / `close_section` | abre/fecha uma aba ou subseção |
| `append_timeline` | adiciona uma linha ao registro vivo |
| `set_state` | muda o estado (a "respiração" da interface) |
| `toast` | notificação efêmera |

---

## REGRAS TÉCNICAS QUE O DESIGN DEVE RESPEITAR

1. **IDs legados obrigatórios** (4 scripts imutáveis dependem deles): `chat-input`, `chat-send`, `messages`, `bot-grid`, `bot-log`, `task-input`, `task-send`, `mem-list`, `mem-query`, `mem-search`, `mem-sleep`, `mem-stats`, `fac-create`, `fac-desc`, `fac-result`, `fac-template`, `theme-toggle`, `health-info`. Podem ser reestilizados, mas devem EXISTIR no DOM.
2. **Uma fonte de verdade para o progresso** (polling OU SSE OU WebSocket — nunca dois brigando). % derivado da fase, sempre chega a 100%.
3. **Service worker:** stale-while-revalidate para assets, network-first para API, bump de cache a cada versão (senão as animações "morrem").
4. **Servida de `web/` na raiz**, assets em caminho absoluto (`/js`, `/css`), sem build obrigatório.

---

## RESUMO PARA O DESIGNER

O Ant's tem **8 telas** e cerca de **50 funções reais**, cada uma ligada a um endpoint verificado. O diferencial visual é a **linha do tempo viva no chat** (a colônia pensando passo a passo) e a **interface que respira** conforme o estado real. Tudo com ícones SVG, sem emoji, honesto (dado ausente = "—"), e degradando com dignidade quando offline. O backend é intocável; a interface nova é livre para ser linda, desde que fale com ele por esses endpoints e preserve os IDs legados.
