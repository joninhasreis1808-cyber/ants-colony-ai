# Ant's 9.3 — Correções de segurança C-1 e C-2

> Diagnóstico e conserto a partir do kit de prova do dono (ataques HTTP reais,
> dois servidores lado a lado). Só depois de reproduzir o furo, o conserto.

## O furo (reproduzido no código real de `main`)
Três endpoints que mudam estado ou tocam o dispositivo aceitavam chamadas
**anônimas** — qualquer um na rede fazia:

| Ataque | Endpoint | Antes |
|--------|----------|-------|
| Invasor se concede nível 5 (TOTAL) | `POST /permissions/grant` | **HTTP 200** — concedido |
| Grava `.py` na árvore de código do servidor | `POST /action/file` | **HTTP 200** — arquivo criado |
| Concede escopo de device (write_files) | `POST /device/scopes/grant` | **HTTP 200** — concedido |

Não havia **nenhuma** camada de autenticação. A guarda de caminhos
(`path_guard`, do 8.0) existia mas **não estava ligada** ao `/action/file` — a
árvore de código ficava gravável.

## C-1 · Guarda de token nas rotas sensíveis (`backend/api/security.py`)
Postura **loopback aberto** (escolha do dono):
- **Local/nativo** (padrão, sem `ANTS_PUBLIC`): o loopback é de confiança — o
  app do dono e os testes **não mudam**.
- **Exposto** (`ANTS_PUBLIC=1`): as rotas sensíveis exigem o token do dono —
  cabeçalho `Authorization: Bearer <ANTS_API_TOKEN>` ou `X-Ants-Token`. Sem
  token → **HTTP 401**. Comparação em tempo constante (`hmac.compare_digest`);
  o token nunca vai a log.
- **Exposto sem token configurado** → *fail-closed* (401): não há como
  autenticar ninguém, então ninguém passa.

Cobertura (sensíveis + irmãos): `/permissions/grant|revoke`,
`/action/file|app|navigate`, `/device/scopes/grant|revoke|revoke_all`,
`/device/paths/allow|disallow`, `/device/panic|panic/reset`. As rotas de
leitura e Q&A (`/health`, `/hive/task`, `/colony/state`, `/organism/vitals`,
`/events/summary`, `/ping`) seguem **abertas** — o produto não quebra.

## C-1b · 2ª guarda (defesa em profundidade) no `/action/file`
O `path_guard` foi **ligado** ao `/action/file`: nem o dono autenticado escreve
fora das pastas autorizadas nem na blacklist imutável. Sem pasta liberada, a
árvore de código do servidor fica intocável. Para gravar, autoriza-se a pasta
em `POST /device/paths/allow` primeiro.

## C-2 · Postura honesta no `/health`
`/health` passa a declarar `auth: {mode, token_configurado, publico}` — **sem
revelar o token**. No Render, confere-se o deploy: `mode` tem que ser `token` e
`publico` `true`.

## Prova (execução real, não simulação)
Servidor real (`uvicorn`, `ANTS_PUBLIC=1`, token configurado), atacado com `curl`:
```
ATAQUE 1 — grant nível 5 (anônimo)      HTTP 401  {"detail":"não autenticado: ..."}
ATAQUE 2 — grava .py na árvore          HTTP 401  (arquivo NÃO existe)
ATAQUE 3 — concede escopo de device     HTTP 401
CONTRAPROVA — dono com token (Bearer)   HTTP 200  <- passa
             dono com X-Ants-Token      HTTP 200  <- passa
2ª GUARDA — dono grava na árvore de código:
             HTTP 403  "Caminho recusado em file.create: fora das pastas
             autorizadas (...). Autorize a pasta em /device/paths/allow."
             arquivo NÃO existe — bloqueado
Q&A/interface (health, ping, colony/state, organism/vitals, events/summary,
             hive/task)                 HTTP 200  <- tudo aberto
/health auth: {'mode':'token','token_configurado':True,'publico':True}
token vaza no /health? 0 (não vaza)
```
+10 testes automatizados (`tests/test_web/test_security_auth_93.py`) que
reproduzem os ataques e a contraprova via TestClient.

## Contrato
- Testes: 519 → **529** (+10). MD5 dos 4 JS legados intactos. Zero deps novas
  (stdlib: `os`, `hmac`). Offline-first e Render intactos (aberto por padrão).

## Como configurar no Render (deploy público)
1. `ANTS_PUBLIC=1`
2. `ANTS_API_TOKEN=<um segredo forte>` (nunca commitado)
3. Conferir `GET /health` → `auth.mode == "token"`, `auth.publico == true`.
