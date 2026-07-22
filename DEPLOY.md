# DEPLOY — Ant's 6.2 no Render (à prova de erro)

> O erro mais comum é criar o serviço como **Static Site**. Isso serve só os
> arquivos de `web/`, **sem o backend FastAPI** — então todo `fetch` falha e a
> interface mostra "colônia adormecida". Para dados reais, o serviço **precisa
> ser Web Service + Docker**. Siga os passos abaixo exatamente.

---

## 1. Suba o código para um repositório Git

O Render faz deploy a partir de um repo (GitHub/GitLab). Garanta que estes
arquivos estão na **raiz** do repo (já vêm no pacote):

- `render.yaml` — blueprint (runtime docker, healthcheck `/health`)
- `deploy/Dockerfile` — imagem enxuta que roda `uvicorn ... --port $PORT`
- `Procfile` — fallback para runtime nativo

## 2. Crie o serviço no Render — **Web Service (Docker)**

### Opção A — Blueprint (1 clique, recomendado)

1. Render → **New +** → **Blueprint**.
2. Conecte o repositório. O Render lê o `render.yaml` e já configura:
   - `runtime: docker`
   - `dockerfilePath: ./deploy/Dockerfile`
   - `healthCheckPath: /health`
3. Clique **Apply**. Pronto.

### Opção B — Manual

1. Render → **New +** → **Web Service** (⚠️ **NÃO** "Static Site").
2. Conecte o repo.
3. Em **Language/Runtime**, escolha **Docker**.
4. **Dockerfile Path**: `./deploy/Dockerfile`
5. **Health Check Path**: `/health`
6. **Plan**: Free.
7. **Create Web Service**.

> Você **não** precisa definir o comando de start nem a porta manualmente: o
> Dockerfile já roda `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`
> e o Render injeta `$PORT` automaticamente. Nunca fixe uma porta no lugar de
> `$PORT` — o Render exige que a aplicação escute na porta que ele fornece.

## 3. Verifique que o backend está de pé

Depois do build (~2–4 min), abra no navegador:

```
https://SEU-APP.onrender.com/health
```

- **Correto** → um JSON com `"status": "healthy"` e 25 módulos.
- **Errado** → veio a página HTML ou 404 ⇒ o serviço foi criado como Static
  Site. Apague e recrie como **Web Service (Docker)**.

Confira também o keep-alive leve:

```
https://SEU-APP.onrender.com/ping   →   {"pong":"ok"}
```

## 4. Aviso do plano Free — hibernação

O plano gratuito do Render **hiberna** o serviço após ~15 min sem tráfego. A
próxima requisição **acorda** o serviço, o que leva **~30–50 s**. Nesse intervalo
a interface mostra honestamente "colônia adormecida" com um botão **"tentar
acordar"** — não é bug, é o cold start.

**Manter acordado (opcional):** aponte um monitor de uptime (ex.: UptimeRobot,
cron-job.org) para `GET /ping` a cada 10 min. O endpoint `/ping` é ultraleve
(não toca memória/hive), feito exatamente para isso.

## 5. Rodar localmente (para comparar)

```bash
pip install -r requirements-cloud.txt
uvicorn backend.api.main:app --host 0.0.0.0 --port 8765
# abra http://localhost:8765  (interface)  e  /health  (JSON)
```

## 6. Checklist final

- [ ] Serviço é **Web Service**, runtime **Docker** (não Static Site)
- [ ] `/health` responde JSON com `status: healthy`
- [ ] `/ping` responde `{"pong":"ok"}`
- [ ] Interface carrega e conversa com o backend (não fica "adormecida")
- [ ] Monitor de uptime batendo em `/ping` (se quiser evitar o cold start)
