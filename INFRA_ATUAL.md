# INFRA_ATUAL — configuração de infraestrutura do Ant's 6.1

> Fatos verificados a partir do repositório. Onde eu **não** tenho como
> confirmar (painel do Render, sua conta GitHub), está marcado como
> **[NÃO VERIFICÁVEL POR MIM]** — confirme no dashboard.

---

## 1. GitHub

### URL do repositório
- **Real (a que o Render usa):** `https://github.com/joninhasreis1808-cyber/ants-colony-ai`
- Owner/repo: `joninhasreis1808-cyber/ants-colony-ai`
- Observação: dentro deste ambiente Claude Code, `git remote -v` mostra um
  **proxy local** (`http://local_proxy@127.0.0.1:41729/git/...`) porque a
  sessão empurra por um relay gerenciado. Há um `insteadOf` que reescreve
  `https://github.com/` → esse proxy. **Fora daqui, use a URL real acima.**

### Branch
- Branch de trabalho desta sessão: `claude/new-session-qf8twg`
- **Branch padrão (o que o Render publica): `main`** — confirmado por
  `git ls-remote --symref origin HEAD` → `ref: refs/heads/main` (commit `2a46621`).
- O Render, no modo Blueprint/autoDeploy, observa o **branch padrão (`main`)**.
  Merge para `main` = novo deploy.

### Push HTTPS ou SSH / autenticação
- **HTTPS** (o remoto é `http(s)://...`, não `git@`).
- Nesta sessão a autenticação é feita por um **relay gerenciado do ambiente**
  (proxy local com `http.proxyauthmethod basic`). **Não é a sua credencial** e
  não é exportável. **[NÃO VERIFICÁVEL POR MIM]** como está a sua auth real.
- Para replicar em outra máquina: use **HTTPS + Personal Access Token** (o
  GitHub pede o PAT como senha) **ou SSH** com uma chave adicionada à sua conta.
  O Render conecta ao GitHub via **GitHub App/OAuth** (autorização feita 1x no
  painel do Render), não via a sua auth local de git.

---

## 2. Render

### Tipo de serviço
- O `render.yaml` **declara `type: web` + `runtime: docker`** → ou seja, um
  **Web Service em Docker** (correto).
- **[NÃO VERIFICÁVEL POR MIM]** se o serviço que já existe na sua conta está
  realmente criado assim. Se a interface mostra mockup/"adormecida", é sinal de
  que pode ter sido criado como **Static Site** (sem backend). Verifique no
  painel: o serviço deve ser **Web Service**, não Static Site.

### `render.yaml` (arquivo inteiro, na raiz do repo)
```yaml
# Ant's 6.0 — Render Blueprint (deploy grátis, 1 clique).
# Fica na RAIZ do repo para o Render detectar automaticamente.
# Botão: https://render.com/deploy?repo=<url-do-seu-repo>
services:
  - type: web
    name: ants
    runtime: docker
    plan: free
    dockerfilePath: ./deploy/Dockerfile
    dockerContext: .
    healthCheckPath: /health
    autoDeployTrigger: commit
    envVars: []
```

### Build Command / Start Command
- Em **runtime Docker**, o Render **não usa** Build/Start Command do painel — ele
  usa o `Dockerfile`. O build é o `docker build` do `deploy/Dockerfile`; o start
  é o `CMD` do Dockerfile.
- **Start (efetivo, do Dockerfile):**
  `uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8765}`
- Fallback runtime nativo (se algum dia não usar Docker) — `Procfile`:
  `web: uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`
- **[NÃO VERIFICÁVEL POR MIM]** o que está digitado nos campos do painel — eu só
  vejo os arquivos do repo.

### Dockerfile em uso (`deploy/Dockerfile`, íntegra)
```dockerfile
# Ant's 6.0 — imagem de nuvem (enxuta, free-tier friendly).
FROM python:3.11-slim

WORKDIR /app

# tesseract: OCR opcional usado pela percepção; curl: healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr curl \
    && rm -rf /var/lib/apt/lists/*

# Dependências enxutas primeiro (aproveita cache de camadas).
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt

# Código e interface web (a API serve web/ na raiz).
COPY backend/ ./backend/
COPY web/ ./web/

# A nuvem injeta $PORT; local usa 8765.
ENV PORT=8765
EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT:-8765}/health" || exit 1

# shell form para expandir $PORT em runtime.
CMD uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8765}
```
> Importante: o `CMD` usa **shell form** para expandir `$PORT`. Se fosse
> exec-form (`["uvicorn", ..., "$PORT"]`) a variável **não** expandiria e o
> Render marcaria o serviço como unhealthy. `.dockerignore` na raiz impede que
> `app/` (Tauri, ~3.6 GB), `node_modules` e `target/` entrem na imagem.

### Porta
- O serviço escuta em **`$PORT`** (injetado pelo Render), com fallback `8765`
  local. Confirmado no `CMD` e no `HEALTHCHECK` acima. ✓

### Variáveis de ambiente
- `render.yaml` → `envVars: []` (**nenhuma** declarada no Blueprint).
- Dockerfile define `ENV PORT=8765` (default; o Render sobrescreve com o `$PORT` real).
- **Nenhum segredo** é exigido para subir. **[NÃO VERIFICÁVEL POR MIM]** se você
  adicionou variáveis manualmente no painel (ex.: `RENDER_DEPLOY_HOOK` usado
  opcionalmente pelo workflow `.github/workflows/deploy.yml`).

### autoDeploy
- `render.yaml` → `autoDeployTrigger: commit` → **deploy automático a cada push
  no branch padrão (`main`)**. **[NÃO VERIFICÁVEL POR MIM]** se o toggle no painel
  está de fato ligado.

---

## 3. Passo a passo real que fez (ou faz) o deploy funcionar

O que foi construído nesta conversa para o serviço subir e responder:

1. **Configs de deploy na raiz** (o Render só auto-detecta na raiz):
   `render.yaml` (Docker), e o build usa `deploy/Dockerfile`.
2. **Imagem enxuta** — `requirements-cloud.txt` (sem `torch`/`chromadb`/
   `playwright`; só o necessário para subir a API). Sem isso, o plano free
   estoura RAM/tempo de build.
3. **`$PORT`** — `CMD` em shell form escutando `--port ${PORT:-8765}`.
4. **`.dockerignore`** — exclui `app/`, `target/`, `node_modules`, `.git` para
   a imagem não ficar gigante.
5. **Deploy no Render** (feito por você, na sua conta): botão "Deploy to Render"
   do README (lê o `render.yaml`) **ou** criar Web Service apontando para
   `deploy/Dockerfile`, autorizando Render↔GitHub uma vez.
6. **URL pública:** `https://ants-uoat.onrender.com`
   - **[NÃO VERIFICÁVEL POR MIM]** o status atual: deste ambiente a saída de
     rede para `onrender.com` é **bloqueada por política** (o gateway responde
     `403` ao CONNECT). Não consigo confirmar se está no ar — **confirme abrindo
     `https://ants-uoat.onrender.com/health` no seu navegador** (deve dar JSON
     `status: healthy`, 25 módulos).

### O que quebrou e precisou de correção no caminho (fatos)
- **Interface mostrando mockup:** os módulos JS usavam dados aleatórios
  (`Math.random`) / de exemplo (`SAMPLE`) e o HTML tinha números fixos
  (`4.712`, `142`, decisões `14:02`). **Corrigido:** removido todo mockup;
  cada painel lê o endpoint real; `api_bridge.js` + `live_panels.js`; falha de
  endpoint mostra "colônia adormecida" (nunca número falso).
- **Causa provável no seu Render:** serviço criado como **Static Site** (sem
  backend) e/ou o `main` ainda sem a correção (ela está no **PR #3**). Enquanto
  não mergear o PR e não for Web Service, o site não mostra dados reais.
- **`--port` fixo:** ajustado para `$PORT` (o Render exige) via `CMD` shell-form.

---

## 4. Checklist para replicar exatamente

- [ ] Repo: `https://github.com/joninhasreis1808-cyber/ants-colony-ai`, branch `main`.
- [ ] Arquivos na raiz: `render.yaml`, `Procfile`, `deploy/Dockerfile`, `requirements-cloud.txt`, `.dockerignore`.
- [ ] Render → **New Web Service** (não Static Site) → conectar o repo → runtime **Docker** → `dockerfilePath: deploy/Dockerfile` → branch `main`.
- [ ] Health check path: `/health`. Auto-Deploy: ligado.
- [ ] Sem variáveis de ambiente obrigatórias. Porta: deixe o Render injetar `$PORT`.
- [ ] Após subir, testar `https://<seu-app>.onrender.com/health` → JSON `status: healthy`, 25 módulos.
- [ ] README (seção "Deploy na nuvem") já contém o botão e o link certo/atualizado.
