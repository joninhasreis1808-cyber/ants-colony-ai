# 🐜 Projeto Ant's — Colônia de Bots com Mente Colmeia

![tests](https://img.shields.io/badge/tests-162%20passing-3ad29f)
![python](https://img.shields.io/badge/python-3.11%2B-0f3460)
![pwa](https://img.shields.io/badge/PWA-instal%C3%A1vel-e94560)

Uma colônia de **bots autônomos** que colaboram como uma mente colmeia:
percebem o mundo, agem sobre ele, lembram do que aprendem e criam
aplicativos completos — tudo acessível por uma **interface web (PWA)** que
funciona no computador e no celular.

## 🧠 Mente colmeia orgânica

A colmeia **lê o objetivo e se auto-organiza**: um roteador cognitivo
(`backend/hivemind/cognitive_router.py`) infere a intenção da tarefa
(pesquisar, perceber, criar) e recruta só os bots certos, no fluxo certo.
Pesquisa mobiliza navigator→learner; percepção traz o perceptor; "crie um
app" aciona o creator. Nada de pipeline cego — cada tarefa mobiliza a
colônia na medida exata, e qualquer bot novo é incorporado só declarando
suas `skills`.

## ⚡ Começar em 1 comando

```bash
bash scripts/start.sh        # instala, testa e sobe tudo
# abra http://localhost:8765
```

Ou na nuvem (grátis): `bash scripts/deploy_cloud.sh` (Railway / Render / Fly.io).

## 🧩 As 5 capacidades

| Fase | Capacidade | Onde |
|------|-----------|------|
| 1 | **Mente colmeia** — 5 bots em ciclo P‑D‑C‑A, memória compartilhada | `backend/hivemind` |
| 2 | **Percepção & Ação** — texto, imagem, OCR, docs, web, dispositivos, permissões | `backend/perception`, `backend/action`, `backend/permissions` |
| 3 | **Memória de longo prazo** bio‑inspirada (atenção→sono) | `backend/memory` |
| 4 | **App Factory** — cria apps a partir de descrições | `backend/app_factory` |
| 5 | **Interface web + deploy + consolidação** | `web/`, `deploy/`, `backend/api/main.py` |

## 🖥️ Interface web

PWA instalável com 5 abas: 💬 Chat · 🤖 Bots · 🧠 Memória · 🏭 Factory ·
⚙️ Ajustes. Tema claro/escuro, streaming ao vivo por WebSocket, cache
offline via Service Worker. Servida pela própria API na raiz (`/`).

## 🌐 API unificada

Ponto de entrada único: `uvicorn backend.api.main:app`.
`GET /health` · `/hive/*` · `/perceive/*` · `/action/*` · `/permissions/*` ·
`/memory/*` · `/factory/*`. CORS liberado, interface web na raiz.

## ✅ Qualidade

153 testes automatizados cobrindo todas as fases. Todos os arquivos
Python respeitam limites de tamanho; funções com type hints; backends
plugáveis (embedder, vector store, deploy, dispositivos) permitem rodar
offline nos testes e trocar por serviços reais em produção sem mudar a API.

## 🤝 Como contribuir

1. Rode `bash scripts/test_all.sh` e garanta 100% verde.
2. Mantenha os limites de linha e adicione testes para código novo.
3. Novos bots: declare `skills` e o Recruiter os incorpora sozinho.

## 📄 Licença

MIT — use, modifique e distribua livremente.

---

Evolução do projeto EFQEA. Bots autônomos que formam uma **mente colmeia**:
cada bot executa o ciclo **P‑D‑C‑A** (Plan‑Do‑Check‑Act) e colabora com os
demais através de uma **memória compartilhada** (blackboard), enquanto a
colmeia transmite em tempo real tudo o que está fazendo.

## Arquitetura

```
POST /task ─► Hivemind ─► Recruiter (recruta bots por skill)
                 │
                 ▼   (cada bot roda P‑D‑C‑A, lê/escreve na memória)
   Navigator ─► Extractor ─► Interpreter ─► Decider ─► Learner
                 │                                        │
        SharedMemory (RAM + SQLite)              EventBus ─► WS /live
```

### Componentes

| Camada | Papel |
|--------|-------|
| `backend/core.py` | Tipos de domínio (Task, BotEvent, SearchResult) |
| `backend/hivemind/` | Orquestrador (`hive`), recrutamento (`recruiter`), montagem (`factory`) |
| `backend/providers/` | Router com fallback: Tavily → Brave → DuckDuckGo |
| `backend/bots/` | Navigator, Extractor, Interpreter, Decider, Learner |
| `backend/memory/` | Memória compartilhada (SQLite) + EventBus (pub/sub) |
| `backend/api/` | FastAPI: `/task`, `/status`, `/live`, `/health` |

## Melhorias essenciais já incluídas na Fase 1

- **EventBus pub/sub** desacoplado — múltiplos clientes observam a mesma
  tarefa; o streaming ao vivo fica testável e independente da API.
- **Recrutamento por skill** — bots se auto‑organizam; adicionar um bot novo
  é só declarar suas `skills`.
- **Resiliência da colmeia** — se um bot falha, a colmeia continua e reporta.
- **Confiança quantificada** — o Decider entrega um score de evidências.
- **Aprendizado persistente** — o Learner acumula estatísticas entre tarefas.

## Como rodar

```bash
pip install -r requirements.txt

# subir a API
uvicorn backend.api.app:app --reload

# enviar uma tarefa
curl -X POST localhost:8000/task -H 'Content-Type: application/json' \
     -d '{"goal": "o que é uma mente colmeia?"}'

# acompanhar
curl localhost:8000/status/<task_id>
```

### Providers pagos (opcionais)

```bash
export TAVILY_API_KEY=...   # ativa Tavily
export BRAVE_API_KEY=...    # ativa Brave
```

Sem chaves, o DuckDuckGo (gratuito) assume — sempre há um fallback.

## Testes

```bash
pytest            # 37 testes cobrindo core, memória, providers, bots, hive e API
```

## Convenções

- Máx. 200 linhas por arquivo · type hints em todas as funções ·
  código comentado em pt‑BR · nuvem‑first, backend Python puro.

## Próximos passos (Fase 3)

LLM/serviço real de tradução no TextInterpreter, modelo de visão no
ImageAnalyzer, backends reais de dispositivo (ADB/uiautomator), cache
Redis opcional e roteamento semântico de skills no Recruiter.

---

# 🐜 Fase 2 — Percepção e Ação

A colmeia ganhou sentidos e mãos, com **permissões granulares** em tudo.

## Percepção (`backend/perception/`)

| Módulo | Faz |
|--------|-----|
| `text_interpreter` | Intenção, entidades, resumo, sentimento, idioma |
| `image_analyzer` | Dimensões, tipo de gráfico, descrição, regiões de texto |
| `document_reader` | pdf, docx, xlsx, pptx, html, md, txt, csv, json, xml |
| `equation_solver` | Parse/solve/explain/plot com SymPy, LaTeX |
| `ocr_engine` | OCR via Tesseract, com pré-processamento |

## Ação (`backend/action/`)

| Módulo | Faz |
|--------|-----|
| `web_navigator` | Navegação Playwright: navegar, clicar, extrair, JS, screenshot |
| `form_filler` | Detecta e preenche formulários por mapeamento de campos |
| `file_operator` | Criar/mover/deletar/organizar/backup — tudo autorizado |
| `app_launcher` | Abrir/fechar/listar apps (backend plugável) |
| `device_controller` | Screenshot, GPS, toques, notificações |

## Permissões (`backend/permissions/`)

5 níveis (BASIC→TOTAL), política declarativa recurso→nível, confirmação
para ações sensíveis, revogação pontual e **auditoria append-only**
exportável (JSON/CSV). Bots herdam o nível do usuário.

## Ponte entre fases

O **PerceptorBot** (`backend/bots/perceptor.py`) integra a percepção ao
ciclo P‑D‑C‑A: lê o contexto compartilhado, interpreta o texto e resolve
equações embutidas — a Fase 2 alimentando a mente colmeia da Fase 1.

## Endpoints novos

`POST /perceive/{text,image,document,equation,ocr}` ·
`POST /action/{navigate,file,app}` ·
`GET /permissions/{user_id}` · `POST /permissions/{grant,revoke}` ·
`GET /permissions/audit/{user_id}`

## Melhorias essenciais adicionadas na Fase 2

- **Política de permissão declarativa** — uma única fonte de verdade
  (`permission_levels.py`) mapeia recurso→nível; fácil de auditar e evoluir.
- **Degradação graciosa** — OCR e navegador checam disponibilidade do
  binário e falham com mensagem clara, sem quebrar imports nem testes.
- **Backends plugáveis** — apps e dispositivo usam Protocols, então o
  backend simulado dos testes vira backend real na Fase 3 sem tocar a API.
- **Auditoria imutável exportável** — trilha completa de toda ação.
- **PerceptorBot** — costura Fase 1 e Fase 2 numa colmeia que percebe.

## Testes (Fase 2)

78 testes no total (37 Fase 1 + 41 Fase 2), cobrindo percepção, ação,
permissões, auditoria e a integração PerceptorBot.

---

# 🐜 Fase 3 — Memória de Longo Prazo (bio-inspirada)

A colmeia deixou de "guardar tudo num HD" e passou a ter uma **rede viva**
de memória que seleciona, fortalece, enfraquece e reorganiza informação —
como um cérebro.

## Módulos (`backend/memory/`)

| Módulo | Papel biológico |
|--------|-----------------|
| `attention` | Atenção seletiva: filtra por novidade, emoção, utilidade, repetição |
| `encoder` | Codificação hipocampal: embedding + features + associações |
| `distributed_store` | Córtex distribuído: coleções semantic/episodic/procedural/emotional/working |
| `consolidator` | Consolidação sináptica: fortalece o usado, enfraquece o ocioso |
| `retriever` | Recuperação por reconstrução associativa (não busca exata) |
| `forgetter` | Esquecimento adaptativo: decay por tipo, poda, interferência |
| `sleep_cycle` | Sono NREM (consolida) + REM (descobre padrões entre domínios) |
| `long_term_memory` | Fachada: `remember()` e `recall()` |

## Embedder plugável (melhoria essencial)

`embedder.py` abstrai a geração de embeddings atrás de um Protocol. O
padrão é o **HashingEmbedder** (768-dim, determinístico, offline, sem
downloads) — o que torna todo o sistema testável sem baixar modelos
pesados. Se `sentence-transformers` estiver instalado, o
`SentenceTransformerEmbedder` assume automaticamente. Mesma filosofia
plugável do backend vetorial (`vector_backend.py`: memória por padrão,
ChromaDB opcional).

## Integração com a mente colmeia

O HiveMind aceita um `LongTermMemory` opcional. Quando presente:
antes de cada tarefa a colmeia faz `recall()` e injeta o conhecimento
prévio no contexto; depois de cada tarefa faz `remember()` do resultado.
O que **um** bot aprende beneficia **todos** — e o `SleepCycle` roda para
a colmeia inteira, não por bot.

```python
from backend.memory.long_term_memory import LongTermMemory
from backend.hivemind.factory import build_hive

ltm = LongTermMemory()
hive, _ = build_hive(ltm=ltm)   # colmeia com memória de longo prazo
```

## Endpoints novos

`POST /memory/remember` · `POST /memory/recall` · `GET /memory/context` ·
`POST /memory/sleep` · `GET /memory/health`

## Melhorias essenciais adicionadas na Fase 3

- **Embedder e vector store plugáveis** — sistema roda offline e
  determinístico nos testes; modelos reais entram sem tocar no código.
- **Fachada `LongTermMemory`** — API única (`remember`/`recall`) que
  esconde a orquestração dos sete módulos.
- **Integração opcional e retrocompatível** — a colmeia funciona com ou
  sem memória longa; nenhum teste das fases anteriores quebrou.
- **REM cross-domínio** — o sono só associa memórias de tipos diferentes
  na faixa de similaridade média, onde moram as analogias úteis.

## Próximos passos (Fase 4)

Ativar sentence-transformers/ChromaDB em produção, persistência em disco
do córtex, priorização de recall por humor/horário, e um "sonho dirigido"
que gera hipóteses a partir dos padrões REM.

---

# 🐜 Fase 4 — App Factory 2.0

A colmeia agora **cria apps completos** a partir de descrições em
linguagem natural: analisa, projeta, gera código, testa de verdade,
documenta e faz deploy.

## Pipeline (`backend/app_factory/`)

| Módulo | Papel |
|--------|-------|
| `requirement_analyzer` | Extrai tipo, features, restrições e stack da descrição |
| `architect` | Escolhe padrão (MVC/Clean/Component/Command/Pipeline) e estrutura |
| `template_engine` | 6 templates funcionais (api/web/mobile/dashboard/cli/pipeline) |
| `code_generator` | Gera código válido a partir de template + arquitetura |
| `sandbox` | Executa/testa código isolado (subprocess + timeout) |
| `tester` | Valida sintaxe, roda pytest no sandbox, auto-fix (3 tentativas) |
| `deployer` | Deploy plugável (6 alvos), health check, rollback |
| `documenter` | README, guia de instalação, diagrama Mermaid |
| `factory_orchestrator` | Encadeia todo o pipeline; registra projetos |

## Como usar

```python
from backend.app_factory.factory_orchestrator import FactoryOrchestrator
from backend.app_factory.results import AppOptions
from backend.app_factory.enums import DeployTarget

orch = FactoryOrchestrator()
result = orch.create_app(
    "uma API REST de tarefas com autenticação e banco de dados",
    AppOptions(run_tests=True, auto_deploy=True, target=DeployTarget.RAILWAY),
)
print(result.summary())   # tipo, arquivos, testes, deploy URL
```

## CreatorBot — a fábrica dentro da colmeia

`backend/bots/creator_bot.py` integra a App Factory ao ciclo P‑D‑C‑A:
qualquer colmeia pode criar apps, sugerir melhorias e fazer code review.
Se a memória de longo prazo (Fase 3) estiver ativa, o bot recorda
projetos anteriores para orientar decisões.

## Endpoints novos

`POST /factory/create` · `POST /factory/quick` · `GET /factory/templates` ·
`GET /factory/projects` · `GET /factory/projects/{id}` ·
`POST /factory/deploy/{id}`

## Melhorias essenciais adicionadas na Fase 4

- **Testes de verdade, não simulados** — o `tester` roda `pytest` no
  código gerado dentro de um sandbox real. Quando o pipeline diz
  "testado: True", os testes rodaram mesmo.
- **Deploy plugável** — 6 alvos atrás de um Protocol; o backend simulado
  vira Vercel/Railway real sem tocar a interface.
- **Código sempre válido** — o gerador valida a sintaxe (AST) de todo
  arquivo Python; o `auto_fix` remove os inválidos antes de entregar.
- **Personalização por requisitos** — detectou "autenticação"? O template
  ganha um `auth.py`. A fábrica adapta o projeto ao que foi pedido.

## Testes

137 testes no total (109 Fases 1‑3 + 28 da Fase 4), cobrindo
atenção, codificação, armazenamento, consolidação, recuperação,
esquecimento, sono e a integração com o HiveMind.
