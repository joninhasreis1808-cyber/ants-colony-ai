# Ant's — Relatório Mestre para IA externa (base para um roteiro de maestria)

> **Para quem lê (ChatGPT / DeepSeek / outra IA):** este documento descreve, com
> honestidade e precisão, o estado real do projeto **Ant's — Superorganismo
> Digital**. Seu objetivo é servir de base para você produzir um **roteiro
> profissional de melhorias de altíssimo nível**, mantendo a **Mente Colmeia como
> núcleo central**, e elevando ao teto de maestria quatro frentes:
> **(1) a própria Mente Colmeia, (2) a interface, (3) as animações,
> (4) as funções/capacidades e (5) a IA.**
> Ao final há um **BRIEF** dizendo exatamente o que entregar e quais
> **invariantes** (restrições inegociáveis) suas sugestões precisam respeitar.

---

## 0. O que é o Ant's (em uma frase)

Um **superorganismo digital bio-inspirado**: uma colônia de bots (castas) coordenada
por uma **Mente Colmeia** (hive-mind) que planeja, pesquisa, raciocina, verifica,
age e evolui — offline-first, sem LLM externo como cérebro, com um **corpo local
nativo** (app Tauri) que age no dispositivo do dono sob travas de segurança, e um
**cérebro remoto** (backend na nuvem) que propõe e coordena.

**Metáfora central (não abandonar):** *cérebro remoto × corpo local*. O cérebro
(servidor) **pensa e propõe**; o corpo (app nativo) **valida e age**. Nada
irreversível sem grant assinado + confirmação.

---

## 1. Invariantes do projeto (restrições INEGOCIÁVEIS)

Qualquer melhoria proposta **precisa respeitar** estes princípios — eles são a alma
do projeto, não detalhes:

- **I1 · Custo zero / free-tier.** Roda no Render free e em máquina comum. Nada de
  serviços pagos obrigatórios.
- **I2 · Offline-first.** O núcleo cognitivo funciona **sem internet** (regras +
  memória). APIs/web são ferramentas opcionais que degradam com elegância.
- **I3 · Sem LLM externo como cérebro.** A cognição é própria (regras,
  planejamento, memória). Um LLM pode ser *ferramenta* plugável, nunca o cérebro.
- **I4 · Sem build step no front.** Interface é **HTML/CSS/JS vanilla** servida
  direto; nada de bundler/framework obrigatório (PWA).
- **I5 · 4 arquivos JS legados são IMUTÁVEIS** (`web/js/chat.js`, `bots.js`,
  `memory.js`, `factory.js`) — verificados por MD5 a cada mudança. IDs legados do
  DOM preservados. Toda evolução de front é **aditiva**.
- **I6 · Segurança do corpo é sagrada.** O servidor **nunca** age no dispositivo:
  ele **assina grants**; o corpo nativo **valida e executa** sob travas
  (path_guard, command_guard, allowlist de apps, confirm, escopos, nonce, TTL,
  segredo por dispositivo). Nada destrutivo sem confirmação humana explícita.
- **I7 · Autoevolução só mexe em DADOS**, nunca em código de produção
  automaticamente. Toda evolução é propor → aprovar → aplicar (sob canário,
  reversível).
- **I8 · A interface nunca inventa dados.** Painel sem dado real mostra estado
  vazio honesto; "ao vivo" só se for ao vivo.
- **I9 · Rito de engenharia:** cada mudança = diagnóstico → **prova executável** →
  `pytest -q` verde → um PR por tarefa → squash-merge. "A verdade acima do
  relatório bonito": todo relatório declara **o que NÃO foi verificado**.

---

## 2. Arquitetura (camadas)

```
KERNEL (imutável)      events · security · permissions
BIOLOGIA               hivemind (castas, feromônio, metabolismo, homeostase) · stigmergy
COGNIÇÃO               cognitive · reasoning · nlp · evaluation · learning · cognition
INTERFACE              api (FastAPI) · web (PWA vanilla)
APPS                   app_factory · intelligence · agents
CORPO LOCAL (nativo)   app/ (Tauri v2 + Rust) · app/local-agent-core (crate provado)
```

**Números reais (medidos):** ~278 arquivos Python no backend, 26 pastas de módulo,
**103 rotas**, **37 arquivos JS** + 5 CSS no front, **83 arquivos de teste**,
**879 testes** passando (5 skipped). O core Rust do corpo tem 28 testes (`cargo
test`). Versão da API: 2.0.0; iteração interna: 9.25.

---

## 3. Inventário de capacidades ATUAIS (o que já existe e está provado)

### 3.1 Mente Colmeia (o núcleo — a base central)
- **Esqueleto cooperativo:** EventBus, Shared Blackboard, ColonyState (máquina de
  estados), Task Graph (DAG com nós ricos: `priority/confidence/evidence`).
- **Planejamento:** Cartógrafa (7 rotas com score), planejador hierárquico,
  esqueletos de decomposição por rota.
- **Cognição tipada:** Cognitive Trace (passos tipados: plan/research/hypothesis/
  verify/decide/act/learn/error), cadeia de **fallback explícita**
  (PRIMARY→SECONDARY→COGNITIVE→HUMAN, escala ao humano sem base), **modos de
  deliberação** FAST/DELIBERATE/CRITICAL ligados ao gate de risco.
- **Castas & recursos:** rainha/exploradoras/operárias/soldados/etc.; reputação,
  polimorfismo/caste-switching, cultura, metabolismo/energia/economia, homeostase,
  circadiano/sono, estigmergia (feromônio), sistema imunológico + quarentena.
- **Memória:** working/semantic/procedural/LTM, consolidator/forgetter/compactor,
  knowledge graph, seed knowledge (inato), proveniência + rótulo epistêmico
  (verified/inferred/uncertain).
- **Maturidade de autoevolução (ligada ao laço vivo):** **calibração de confiança**
  (ECE, alimentada por missões reais via `/calibration`), **canário interno**
  (5→10→25→50→100%, com rollback reversível, realimentado por missões), **causal
  graph** (causa→efeito, força, explain/root_causes).
- **Autonomia:** governador, níveis de confiança, evolução controlada (dados).

### 3.2 Automação nativa (o "n8n da colônia", soberano e offline)
- **Secret Vault:** segredos por-capability, rotação, TTL, **derivação HMAC**
  (segredo por dispositivo), auditoria que nunca loga o valor.
- **Motor de Fluxos:** workflows multi-passo sobre o Tool Registry; segredos por
  referência (`$secret.NOME`), dados entre passos (`$steps.ID.chave`), travas do
  registry preservadas.
- **Gatilhos:** reativo (EventBus) + agenda (recorrente/one-shot via `due()`).

### 3.3 Corpo local nativo (app Tauri) — as 6 capacidades
Todas com **decisão de segurança provada em Rust** (`cargo test`) e execução
type-checada em isolamento:
- **Arquivo:** ler / escrever (dry-run + confirm; path_guard/whitelist).
- **Comando:** rodar (allowlist do command_guard + confirm; argv, nunca shell).
- **Tela:** capturar (destino só em pasta autorizada; comando do SO).
- **App:** abrir (allowlist `ANTS_ALLOWED_APPS` + confirm; spawn).
- **Entrada fina:** mover/clicar/digitar/tecla (vocabulário fechado + confirm;
  ferramenta do SO tipo `xdotool`).
- **Ponte segura:** handshake de segredo efêmero por execução; **identidade de
  dispositivo** (segredo derivado por dispositivo — grant de A recusado por B);
  endpoint que assina grants (`/local-agent/grant`, autenticado pelo dono).

### 3.4 Interface (PWA vanilla)
- Abas: Colônia, Cognição, Ambiente, Recursos, Rainha, Factory, Ajustes.
- Câmera ao Vivo (screenshots por evento), mind panel, mission console, timeline,
  selo de proveniência.
- **UI Command API tipada** (backend `interface/ui_commands.py` casado com o
  `ui_kernel.js` — a IA comanda a UI por eventos tipados, nunca HTML cru).
- **Painel "Cognição ao Vivo"** (aditivo, colapsável): trilha tipada + escada de
  fallback + modo + barra de calibração viva.
- **Painel "Corpo Local"** (só no app nativo): dispara as 6 capacidades.
- Design system central (`design_system.css :root` + aliases `--ant-*`).

---

## 4. Estado de maturidade (honesto — o que está PROVADO × PENDENTE)

**Provado com prova executável (aqui, no CI):** toda a lógica de backend, o núcleo
cognitivo, a automação nativa, o **core de segurança do corpo** (Rust, 28 testes),
o fio UI→grant→executor (server-side), a identidade de dispositivo, o laço vivo
(calibrador + canário realimentados), a fiação da UI, a camada HTTP de validação
(`validate_native.sh` rodou 5/5 contra backend real).

**Pendente — depende de hardware/deployment (NÃO é falha de execução, é limite do
ambiente):**
- O **build gráfico do Tauri** não roda no sandbox (faltam GTK/WebKit); provado em
  partes (core + type-check isolado). **Falta compilar e rodar na máquina do dono.**
- As **ações físicas reais** (tela/app/entrada de verdade) e o **visual em pixels**
  só se confirmam com o app rodando.
- O **transporte remoto pela rede** (TLS/WebSocket Render↔Tauri) é camada de
  deployment; o **contrato de autenticação** (segredo por dispositivo + nonce +
  TTL) está pronto e provado, mas o soquete seguro é passo de implantação.

---

## 5. As 5 frentes de melhoria pedidas (contexto + provocações para o roteiro)

Para cada frente, aprofunde com propostas concretas, priorizadas, e **respeitando
os invariantes (§1)**. Onde uma ideia colidir com um invariante, diga como
contorná-la (ex.: camada de compatibilidade), nunca sugira quebrá-lo.

### 5.1 Mente Colmeia (NÚCLEO — o mais importante)
Estado: rica e madura, mas há fronteiras de inteligência ainda abertas.
Provoque melhorias em: **memória hierárquica L0–L6 nomeada**; **calibração de
confiança** contra sinais mais fortes (não só auto-consistência); **causal graph**
alimentado pelo laço vivo (hoje é biblioteca); **A/B real de estratégias por rota**
(hoje o canário é por tipo-de-objetivo); **deliberação com simulação** (o Simulator
existe mas não roda N vezes por modo); **teoria da mente / coordenação entre
castas** mais rica; **meta-cognição** (a colônia raciocinando sobre o próprio
desempenho); **curiosidade/exploração dirigida**; **consolidação de sono** que
realmente reorganiza a memória. Tudo offline e determinístico onde possível.

### 5.2 Interface
Estado: funcional, honesta, vanilla, aditiva; painéis "Cognição ao Vivo" e "Corpo
Local" existem, mas o visual não foi refinado num browser.
Provoque melhorias em: **repaginação coesa** (mantendo IDs legados e MD5); **modo
foco/observatório** para ver a colônia pensar; **visualização do Task Graph e da
escada de fallback** como diagramas vivos; **linha do tempo cognitiva** navegável;
**acessibilidade** (teclado, contraste, ARIA); **responsividade** desktop/mobile
comprovada; **temas** (o design system já tem tokens). Sem build step, sem tocar
nos 4 JS legados.

### 5.3 Animações
Estado: quase inexistentes (SVG estáticos, alguns flashes).
Provoque melhorias em: **micro-animações significativas** (não decorativas): pulso
da colônia por estado, feromônio se difundindo, castas acordando/hibernando,
partículas que representam bots reais em ação, transições de estado da máquina
`ColonyState`, animação da escada de fallback e do canário subindo/revertendo.
Tudo em **CSS/SVG/Canvas puro** (sem libs pesadas obrigatórias), performático,
respeitando `prefers-reduced-motion`.

### 5.4 Funções / Capacidades
Estado: 6 capacidades do corpo + automação nativa + factory de apps.
Provoque melhorias em: **novas capacidades do corpo** (ex.: clipboard, janelas,
watch de arquivos) sempre sob o mesmo modelo de travas; **Browser Perception**
(PAGE MODEL já existe — evoluir para navegação autônoma com relearn); **biblioteca
de fluxos** prontos (automação nativa); **agendador visual** de gatilhos;
**marketplace interno** de ferramentas/skills; **modo "aprender uma tarefa"**
(gravar → generalizar → repetir). Sempre gated, auditável, reversível.

### 5.5 IA (a inteligência)
Estado: cognição própria por regras + memória; LLM só como ferramenta plugável.
Provoque melhorias em: **raciocínio mais forte offline** (chains determinísticas,
verificação cruzada, decomposição melhor); **uso opcional de LLM local** (ex.:
Ollama) como *córtex* plugável sem virar dependência; **RAG sobre a memória
própria**; **aprendizado por feedback** (👍/👎) que realmente muda o
comportamento; **auto-avaliação de missão** com template rígido; **detecção de
alucinação** mais forte (o rótulo epistêmico existe); **calibração** que fecha o
laço predito×real com sinais reais.

---

## 6. BRIEF — o que você (IA externa) deve produzir

Produza um **ROTEIRO PROFISSIONAL DE MELHORIAS**, no mesmo espírito de engenharia
do projeto (§1, I9), com:

1. **Diagnóstico crítico** honesto do estado atual (pontos fortes e fracos reais),
   por frente (§5).
2. **Roteiro priorizado por fases**, cada fase com:
   - objetivo e valor claro;
   - **incrementos pequenos e testáveis** (um por tarefa), com prova sugerida;
   - risco e mitigação; dependência entre fases;
   - qual **invariante** cada incremento poderia ameaçar e como respeitá-lo.
3. **Ênfase na Mente Colmeia como núcleo** — a maior parte do valor deve vir de
   torná-la mais inteligente, transparente e autônoma (sem quebrar I3/I7).
4. **Melhorias concretas e "impressionantes"** em interface, animações,
   funções/capacidades e IA — mas sempre aditivas, offline-first, custo zero, sem
   build step, sem tocar nos 4 JS legados (I4/I5).
5. **Critérios de "teto de maestria"**: como saberemos que chegamos lá (métricas,
   provas, experiência do usuário).
6. **O que NÃO fazer** (anti-padrões que quebrariam a alma do projeto).

Formato sugerido: fases numeradas, tabelas de incrementos, e uma seção final "O que
NÃO foi verificado / pressupostos" — porque a honestidade é um valor central aqui.

> **Regra de ouro para suas sugestões:** *melhore o organismo, não o substitua.*
> Nada de reescrever o que funciona só porque parece mais elegante; camada de
> compatibilidade quando houver incompatibilidade; tudo testável e reversível.

---

## 7. Referências de contexto (arquivos-chave, se precisar aprofundar)

- Visão e mapa: `docs/visao/MAPA_ATUAL_x_VISAO.md`, `RELATORIO_MESTRE_7.0.md`,
  `AUTOAVALIACAO_ESTADO.md`, `APP_NATIVO_TAURI.md`, `ESQUEMA_DE_EVENTOS.md`.
- Núcleo: `backend/hivemind/`, `backend/cognitive/`, `backend/cognition/`.
- Corpo local: `app/local-agent-core/` (Rust), `app/src-tauri/`,
  `backend/local_agent/`.
- Interface: `web/` (PWA), `web/js/ui_kernel.js`, `web/js/cognition_panel.js`,
  `web/css/design_system.css`.
- Rito/protocolo: as 6 regras do PROTOCOLO_COWORK (diagnóstico, prova executável,
  rede de testes verde, um commit por tarefa, declarar o não-verificado, interface
  não inventa).
