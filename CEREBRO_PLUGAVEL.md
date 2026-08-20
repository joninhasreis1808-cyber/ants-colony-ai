# Ant's — Córtex plugável (cérebro opcional) e Pesquisa Profunda (9.5)

> Como dar à colônia um **cérebro de raciocínio** — sem embutir modelo, sem
> quebrar o offline-first. É um **acelerador opcional**: sem ele, a Mente
> Colmeia raciocina por **regras** (comportamento atual). A base do projeto
> continua sendo a Mente Colmeia; o córtex é uma **faculdade compartilhada**
> que as castas consultam.

## O que muda
- **Sem cérebro** (padrão): `/health.reasoning.backend == "rules"`. Tudo como hoje.
- **Com Ollama** (local, grátis) **ou uma API** (chave sua): a Rainha usa o
  córtex para **planejar sub-perguntas** e **sintetizar** a resposta da
  **Pesquisa Profunda** — investigação em várias etapas.

Auto-detecção (nesta ordem): **API** (se há chave) › **Ollama** (se está
rodando) › **regras**.

---

## Opção 1 — Ollama (na sua máquina, grátis, offline)

**Não roda no Render free tier** (512 MB, sem GPU; o modelo pesa GBs). É o
cenário do **app nativo / seu PC**.

```bash
# 1. Instale o Ollama:  https://ollama.com
# 2. Baixe um modelo leve (roda em máquina modesta):
ollama pull qwen2.5:3b        # ~2 GB   (ou: llama3.2:3b)
# 3. Rode o Ant's local normalmente:
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```
O Ant's detecta o Ollama sozinho em `http://127.0.0.1:11434`. Para conferir:
```bash
curl -s http://127.0.0.1:8000/health | python -m json.tool | grep -A3 reasoning
# esperado:  "backend": "ollama"
```
Variáveis (opcionais): `ANTS_OLLAMA_URL` (default `http://127.0.0.1:11434`),
`ANTS_OLLAMA_MODEL` (default `qwen2.5:3b`).

---

## Opção 2 — API compatível com OpenAI (funciona no Render também)

Qualquer provedor com o formato OpenAI (`/chat/completions`): OpenAI, Groq,
OpenRouter, Together, etc. **Custa por uso** e **exige rede** — por isso é
opcional. No Render, defina as variáveis de ambiente do serviço:

```bash
ANTS_LLM_API_URL = https://api.groq.com/openai/v1     # exemplo (Groq)
ANTS_LLM_API_KEY = sk-...                              # SUA chave (nunca commite)
ANTS_LLM_MODEL   = llama-3.1-8b-instant
```
Conferir depois do deploy: `GET /health` → `reasoning.backend == "api"`. O
token **nunca** aparece no `/health` (só `backend`, `llm`, `model`).

---

## Controle do modo
`ANTS_LLM = auto | api | ollama | rules`
- `auto` (padrão): API › Ollama › regras.
- `rules`: força o motor de regras (ignora chave/Ollama) — útil para testes.

---

## Como usar a Pesquisa Profunda
Na aba **Colônia**, digite um tema e clique em **"Pesquisa profunda"** (ou envie
`{goal, deep:true}` para `POST /hive/task`). A colônia investiga em etapas —
a **Câmera ao Vivo** mostra: **Rainha** (planeja) → **Exploradoras** (pesquisam
cada sub-pergunta) → **Operárias** (compilam/deduplicam) → **Soldados**
(verificam) → **Rainha** (sintetiza). O selo de proveniência declara a origem;
sem evidência, diz honestamente "não sei" (Regra 6) — nunca inventa.

## Garantias
- **Offline-first:** sem córtex/rede, tudo funciona por regras + declara limitação.
- **Nada embutido / nada obrigatório** (decisão do dono).
- **Render seguro:** sem chave → `rules` (não muda o deploy atual).
- **Mente Colmeia rege:** o córtex é faculdade das castas, não um chefe paralelo.
