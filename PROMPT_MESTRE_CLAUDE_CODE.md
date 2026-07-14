# ✦ PROMPT-MESTRE — ANT'S 6.0 · Superorganismo Digital Transparente

> **Para o Claude Code.** Este é o documento único e definitivo para montar o
> **Ant's** — website + PWA + app nativo — a partir do código-fonte que já
> acompanha este pacote. Ele mescla todos os relatórios (5.0, 6.0 e o feedback
> de design) com a interface enviada como guia visual. **Nada deve se perder ou
> quebrar.** Siga em sequência. Não pule etapas.

---

## 0 · CONTRATO INEGOCIÁVEL (leia antes de tocar em qualquer arquivo)

1. **Os 326 testes existentes devem continuar passando.** Rode `python -m pytest tests/ -q` antes e depois de cada bloco. Se algo quebrar, corrija antes de prosseguir.
2. **NÃO altere a lógica dos 4 arquivos JS originais.** Eles são intocáveis. Confira o MD5 ao final:
   - `web/js/chat.js` → `e1cc6df5be37d6e0502b1063767601bd`
   - `web/js/bots.js` → `ed95b37ebbf0b926daa685dfe09419c1`
   - `web/js/memory.js` → `de5d8499d12efd869baa138497996e10`
   - `web/js/factory.js` → `18b0d5a834fda16f613633a250db053d`
3. **NÃO adicione dependências externas obrigatórias.** Tudo funciona offline. APIs e libs são aceleradores opcionais, nunca requisitos.
4. **NÃO altere a lógica central do backend.** Só adições aditivas.
5. **Cada arquivo novo ≤150 linhas. Funções ≤30 linhas. ZERO emojis na interface** — apenas ícones SVG coesos (mesmo peso de linha e proporção).
6. **Toda mudança é aditiva.** Se um arquivo já existe e funciona, estenda-o sem reescrever o que já passa nos testes.

### IDs LEGADOS — o contrato entre a interface e o backend (NUNCA remover)

Os JS originais buscam exatamente estes IDs. A nova interface **deve** contê-los,
mesmo que como espelhos ocultos (`style="display:none"`) sincronizados por um
script-ponte:

```
app.js      → theme-toggle, conn, health-info, toast
chat.js     → chat-send, chat-input, messages
bots.js     → task-send, bot-grid, bot-log, task-input
memory.js   → mem-search, mem-sleep, mem-stats, mem-query, mem-list
factory.js  → fac-create, fac-desc, fac-template, fac-result
```

> A interface enviada (`design_reference/ants-command-redesign.html`) já preserva
> os IDs descritivos equivalentes (`chat-messages`, `bots-grid`, `memory-list`,
> `factory-description`, `factory-template`, `factory-create`, `settings-theme`,
> `settings-permissions`, `sidebar`, `.nav-item`, `connection-indicator`). O
> trabalho é **ligar** esses IDs descritivos aos IDs legados via `scripts.js`
> (pontes de compatibilidade), sem tocar nos 4 JS originais.

---

## 1 · FILOSOFIA (aplica-se a cada linha da interface)

> **"Um superorganismo digital transparente."**

A interface **não mostra bots — mostra a INTENÇÃO da colônia.** O usuário não
pensa *"o ExplorerBot achou um arquivo"*; ele percebe *"a colônia decidiu
explorar o dispositivo, encontrou uma pista, mudou a estratégia, validou a
descoberta e concluiu a missão."* Os bots são células de um organismo maior.

Cinco princípios: **(1)** organismo adaptativo · **(2)** autonomia proporcional
à confiança · **(3)** interface explicável · **(4)** eficiência antes de força ·
**(5)** evolução segura (testada em sandbox antes de promover).

**Regra de ouro de coerência:** cada painel, animação e botão da interface tem
correspondência direta com um módulo real do backend (listados na §3). Nada é
decorativo sem função.

---

## 2 · O QUE JÁ ESTÁ PRONTO (a fonte da verdade — NÃO reconstruir)

Este pacote **já contém** o backend completo, testado (326 testes) e independente.
NÃO reimplemente. Apenas conecte a interface a ele.

### Backend por camadas (tudo em `backend/`)

- **Núcleo & mente colmeia** — `hivemind/` (ciclo P-D-C-A, recrutamento, feromônios `pheromone.py`, quórum, regeneração, micélio, lifecycle).
- **Superorganismo cognitivo (offline, próprio)** — `cognitive/` (9 camadas + `orchestrator.py`), `reasoning/` (motor próprio + inferência lógica), `nlp/` (tokenização, sentimento, TF-IDF, embeddings PMI). **Sem NLTK/spaCy/transformers/Ollama.**
- **Castas & evolução** — `hivemind/castes.py`, `polymorphism.py`, `economy.py` (com mercado cognitivo), `plasticity.py`, `morphogenesis.py`, `colony_state.py` (3 estados), `culture.py`, `homeostasis.py`, `stigmergy_field.py` (feromônios vetoriais).
- **Meta-cognição & seleção** — `cognitive/meta_supervisor.py`, `evaluation/algorithm_selection.py`, `cognitive/queen_council.py`, `cognitive/advanced_reasoning.py`, `cognitive/global_workspace.py`.
- **Organismo vivo (Parte A dos relatórios 5.0/6.0)** — `hivemind/metabolism.py`, `circadian.py`, `hormones.py`, `colony_dna.py`, `recruitment_tracker.py`; `security/immune_system.py`; `permissions/trust_based_autonomy.py`; `intelligence/permanent_missions.py`, `observer.py`, `discovery.py`, `predictor.py`, `temporal.py`, `scheduler.py`, `limitations.py`, `recommender.py`; `learning/feedback_learner.py`; `memory/knowledge_graph.py`, `procedural.py`, `semantic_memory.py`, `hybrid_store.py`, `world_cache.py`, `cache_manager.py`; `agents/investigator.py`, `architect_agent.py`, `autonomous_bot.py`, `smart_navigator.py`; `monitoring/observability.py`.
- **Autossuficiência** — `providers/local_provider.py` (fallback por regras), `playwright_provider.py` (navegação sem API), Computer Use com whitelist/sandbox/auditoria.
- **API** — `api/main.py` serve `web/` na raiz, CORS liberado, `/health` com todos os módulos. Routers já montados sob prefixos: `/hive /perceive /action /permissions /memory /factory /bio /mind /colony /organism`.

### Endpoints que a interface deve consumir (todos já existem)

| Painel da interface | Endpoint real |
|---|---|
| Conexão / saúde | `GET /health` |
| Chat / missão | `POST /hive/task`, `GET /hive/status/{id}`, `GET /hive/swarm` |
| Cognição (pensamento) | `POST /mind/think`, `POST /mind/reason`, `POST /mind/infer`, `POST /mind/assess` |
| Estado da colônia | `GET /colony/state`, `POST /colony/homeostasis`, `GET /colony/meta`, `GET /colony/observability` |
| Sinais vitais / organismo | `GET /organism/vitals`, `POST /organism/immune/analyze`, `GET /organism/dna` |
| Feedback da Rainha | `POST /organism/feedback` (kind: approve/reject/teach/default/forbid) |
| Missões permanentes | `GET /organism/missions`, `POST /organism/missions` |
| Feromônios / enxame | `GET /bio/pheromones`, `POST /bio/pheromones/deposit`, `GET /bio/mycelium/status` |
| Memória | rotas `/memory/*` (já usadas por `memory.js`) |
| Factory | rotas `/factory/*` (já usadas por `factory.js`) |

---

## 3 · A INTERFACE (guia visual → produção)

Use `design_reference/ants-command-redesign.html` como **fonte da verdade
visual**. Ela é um export de ferramenta de design (formato `.dc.html` renderizado
por `support.js`/React). **Sua tarefa é portar aquele design para HTML/CSS/JS
vanilla** que o backend serve estaticamente em `web/`, mantendo o contrato de IDs.

### 3.1 Abas (unificadas conforme o feedback de design)

A interface tem **10 abas**, com Chat + Colônia + Cognição fundidos na principal:

1. **🐜→ícone Colônia** — Chat integrado + **Missão Atual** (barra viva) + **Cognição** (pensamento revelado passo a passo) + rede viva de bots. *É aqui que "conversar" vira "dar tarefa à colônia".*
2. **Ambiente** — dispositivo + internet + aplicativos + arquivos + projetos + permissões + estado do sistema (substitui o antigo "buscar memória").
3. **Cognição** — 9 camadas com barras de ativação + **linha temporal** + hipóteses + decisões + evidências + conflitos (a timeline vive aqui, é consequência do raciocínio).
4. **Rainha** — objetivos mestres, conselho (animado quando convocado), decisões recentes **com o MOTIVO**, e **feedback em toda decisão** (5 botões — §3.3).
5. **Missões** — projetos ativos e permanentes; caminho da missão no topo (Pedido → Planejamento → Pesquisa → Hipóteses → Execução → Validação → Resposta), cada etapa **acende** ao concluir.
6. **Recursos** — sinais vitais: CPU, RAM, disco, rede, bateria, temperatura, bots ativos, fila, latência, uptime.
7. **DNA** — estratégias aprendidas, especializações, tradições, evolução semanal.
8. **Factory** — criação de apps.
9. **Console** — DevTools profissional (logs, API, bots, sistema, erros; filtros; export).
10. **Ajustes** — permissões, perfis (Usuário/Desenvolvedor/Cientista), tema, nível de confiança.

### 3.2 Identidade visual própria (NÃO imitar ChatGPT/Claude/Manus)

- Paleta: âmbar `#d4a017`, mel `#e8b84b`, folha `#3d7a3d`, terra `#5c4033`, ouro-da-rainha `#d4a017`, soldado `#8b0000`, exploradora `#2563eb`. Texto pergaminho `#e8e0d5`. Fundo profundo `#0a0e14`.
- Fontes do guia: **Newsreader** (títulos) + **IBM Plex Mono** (dados/código).
- Padrão hexagonal de colmeia sutil (opacidade ~0.03).
- **Interface viva:** `colony-breath` (respiração lenta quando ociosa), `node-pulse` (bots ativos pulsam), `pheromone-flow` (trilhas coloridas animadas), `memory-glow` (memória acessada sobe e brilha), `queen-pulse` (pulso da Rainha acelera com carga), `connection-spark` (conexões piscam ao transferir dados). Respeite `prefers-reduced-motion`.
- **8 estados** mudam o tema discretamente: adormecida, observando, explorando, construindo, aprendendo, defendendo, executando, emergência (500ms ease-in-out).

### 3.3 Feedback estrutural (liga direto ao backend `POST /organism/feedback`)

Em **toda decisão importante**, cinco botões — cada um altera um peso diferente:

| Botão | `kind` | Efeito real no backend |
|---|---|---|
| 👍 Funcionou | `approve` | reforça o peso da estratégia (`FeedbackLearner.approve`) |
| 👎 Não gostei | `reject` | reduz o peso |
| 💬 Ensinar | `teach` | grava preferência na memória procedural |
| 📌 Tornar padrão | `default` | promove a tradição (peso alto) |
| 🚫 Nunca faça | `forbid` | bloqueia a estratégia |

*(Use texto/ícone SVG, não emoji, na UI final — a tabela acima só nomeia a intenção.)*

### 3.4 Cognição viva & recrutamento (a grande melhoria de transparência)

- O pensamento aparece **lentamente**, passo a passo (revelação/typewriter), não tudo de uma vez: *"Researcher criou estratégia → solicitou ExplorerBot#3 → encontrou 47 arquivos → encaminhou ao Critic → Confidence 87%"*.
- Consuma `GET /hive/status/{id}` (que retorna os **eventos** reais da colônia) e `POST /mind/think` (que retorna `answer`, `confidence`, `domain`, `hypotheses`, `gaps`, `critique_ok`).
- Mostre **quem chamou quem** com base em `recruitment_tracker` (exponha via evento ou pequeno endpoint se necessário — aditivo).

---

## 4 · EXECUÇÃO — ordem exata

### Bloco 0 — Verificação
```bash
python -m pytest tests/ -q          # deve mostrar "326 passed"
md5sum web/js/chat.js web/js/bots.js web/js/memory.js web/js/factory.js
```

### Bloco 1 — Portar a interface (só arquivos NOVOS/estáticos em web/)
- `web/index.html` — as 10 abas, com todos os IDs legados presentes (ocultos onde preciso). **Sem emojis; só `<symbol>` SVG num sprite.**
- `web/css/design_system.css` (≤200 linhas) — tokens, padrão hexagonal, animações vivas, 8 estados.
- `web/css/style.css` — layout responsivo (bottom-nav <600px, rail 600–1023px, sidebar ≥1024px; toque ≥48px).
- `web/js/scripts.js` (≤200 linhas) — **só UI + pontes de compatibilidade**: navegação `.nav-item`→aba, título dinâmico, ponte campo-visível→ID-legado, controlador do painel de progresso (estilo Manus), abrir/fechar modais, indicador flutuante. **Não duplique o que `app.js` já faz** (tema, conn, toast, health).
- `web/js/` novos módulos vivos (cada ≤150 linhas): `context_engine.js` (estado→tema), `colony_main.js` (chat+missão+cognição), `cognition_live.js` (pensamento revelado), `recruitment_view.js` (quem chamou quem), `environment_view.js`, `signs_vitals.js`, `queen_dashboard.js` (feedback), `dna_view.js`, `mission_center.js`, `memory_live.js`, `learning_feed.js`, `console.js`, `profiles.js`, `workspace.js`.
- Carregue os 4 JS originais **sem modificá-los**, e `scripts.js` **antes** deles para preparar as pontes.

### Bloco 2 — Ligar aos endpoints reais (§2)
Cada painel busca o endpoint correspondente. Sempre trate erro com estado
"colônia adormecida" (não quebre a UI se o backend estiver offline).

### Bloco 3 — PWA
- `web/manifest.json`: `name:"Ant's — Superorganismo Digital"`, `short_name:"Ant's"`, `display:standalone`, `background_color:#0a0e14`, `theme_color:#d4a017`, ícones 192 e 512 (padrão hexagonal + formiga estilizada, SVG→PNG).
- `web/sw.js`: cache-first para assets, network-first para `/health` e demais rotas de API, **fallback offline com a tela "colônia adormecida"**. Faça bump de versão do cache.

### Bloco 4 — App nativo (Tauri) + binário
- `app/src-tauri/tauri.conf.json`: empacota `web/` como frontend; em `beforeDevCommand`/sidecar, sobe o backend Python; ícone nativo; notificações do SO.
- Binário do backend: `pyinstaller --onefile --name ants_backend backend/api/main.py`.
- Scripts: `scripts/build_website.sh`, `scripts/build_app.sh`, `scripts/build_all.sh`.
- O app nativo deve iniciar o backend automaticamente e abrir `http://localhost:8765`.

### Bloco 5 — Integração final
```bash
python -m pytest tests/ -q                        # continua 326+ passed
uvicorn backend.api.main:app --host 0.0.0.0 --port 8765 &
curl -s http://localhost:8765/health | python -m json.tool
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8765/     # 200
md5sum web/js/chat.js web/js/bots.js web/js/memory.js web/js/factory.js   # inalterados
```

---

## 5 · COMPROMISSO SAGRADO — melhorias estruturais VITAIS a incluir

Ao montar, **acrescente** estas melhorias (todas aditivas, testáveis, ≤150 linhas,
sem dependências) — elas tornam a colmeia mais orgânica, livre, poderosa e eficaz,
e fazem os botões conversarem com o progresso vivo da IA:

1. **Ponte de eventos ao vivo (SSE/polling):** um pequeno módulo `web/js/live_bridge.js` que faz *polling* de `GET /hive/status/{id}` a cada ~500ms e emite eventos para `cognition_live.js` e `mission_center.js`. Assim a barra de missão e o "pensamento" refletem o estado REAL da colônia, não uma simulação. (Se preferir, adicione um endpoint SSE aditivo `GET /hive/stream/{id}` no backend, sem alterar o pipeline.)
2. **Reflexo de estado automático:** `context_engine.js` deriva o estado (explorando/construindo/…) da intenção da tarefa e de `GET /colony/state`, e aplica o tema — a interface "respira" conforme a colônia respira de verdade.
3. **Feedback que fecha o ciclo:** cada clique nos 5 botões chama `POST /organism/feedback` e, ao concluir, mostra visualmente o peso ajustado (a decisão "aprende" na frente do usuário).
4. **Sinais vitais reais:** `signs_vitals.js` consome `GET /colony/homeostasis` e `GET /organism/vitals` (hormônios, fase circadiana, imunidade) — os medidores mostram o organismo real, com alertas quando algo sai do equilíbrio.
5. **Observer proativo não-invasivo:** um card flutuante que exibe achados do `Observer` ("4 duplicados", "backup atrasado") no máximo 3×/dia, sempre com ação sugerida e botão de permitir/ignorar.
6. **Guarda imunológica na UI:** antes de qualquer ação de Computer Use disparada pela interface, chame `POST /organism/immune/analyze`; se `dangerous`, exija confirmação explícita e destaque em vermelho (borda `--ant-ember`).
7. **Acessibilidade e resiliência:** `prefers-reduced-motion`, foco visível, toque ≥48px, e degradação graciosa (a UI nunca trava se um endpoint falhar — mostra "colônia adormecida").

---

## 6 · CHECKLIST DE ENTREGA (só finalize com tudo ✅)

```
[ ] 326+ testes passando (nenhum quebrado)
[ ] MD5 dos 4 JS originais inalterados
[ ] Zero emojis na interface (só ícones SVG coesos)
[ ] Todos os IDs legados presentes e ligados às pontes
[ ] As 10 abas funcionam e consomem endpoints REAIS
[ ] Cognição revela o pensamento passo a passo (dados reais de /hive/status e /mind/think)
[ ] Feedback (5 botões) chama /organism/feedback e mostra o peso ajustado
[ ] Sinais vitais leem /colony/homeostasis e /organism/vitals
[ ] Interface "respira" e muda de tema conforme o estado da colônia
[ ] PWA instalável, com fallback offline "colônia adormecida"
[ ] App Tauri sobe o backend e abre a interface
[ ] Startup < 3s, RAM baixa, funciona 100% offline
[ ] README atualizado; gerar ants-6.0-final.tar.gz
```

---

> **Lembre-se:** o Ant's não RESPONDE — ele ADMINISTRA. E a interface não é um
> painel: é uma **janela para dentro de um organismo vivo e transparente**. Cada
> pixel deve corresponder a algo real que a colônia está pensando ou fazendo.
