# Desenho do Corpo Local (Local Agent) — FASE 5

> **Abertura cautelosa.** Esta é a fronteira mais poderosa **e** mais sensível do
> Ant's. Este documento é o **desenho + a trava de segurança**; **nada de I/O de
> device foi implementado ainda.** Cada capacidade real será aberta depois, uma por
> vez, com autorização do dono, dry-run, rollback, pânico e auditoria.

## O princípio: cérebro remoto × corpo local

O Render (nuvem) **não controla** o computador/celular do usuário — está remoto.
Quem toca arquivos, apps, tela, teclado é um **Local Agent nativo** (Tauri),
instalado no dispositivo.

```text
  Mente Colmeia (Render)          Local Agent (dispositivo)
  ─────────────────────           ─────────────────────────
  planeja e PROPÕE          →     VALIDA a permissão
  assina um grant           →     verifica assinatura+prazo+nonce
  (nunca executa device)          EXECUTA localmente, sob a coleira do dono
                                  (dry-run → confirma → rollback/pânico/auditoria)
```

**Invariante duro:** o servidor remoto **nunca** recebe acesso irrestrito à
máquina. Ele só emite *pedidos assinados*; o poder de agir mora no dispositivo.

## A trava de segurança (já implementada, testada)

`backend/local_agent/capability_tokens.py` — o portão que antecede qualquer ação:

- **Capacidades** (o "posso fazer" ≠ "sei fazer"): `CAN_READ_FILES`,
  `CAN_WRITE_FILES`, `CAN_SCREENSHOT`, `CAN_BROWSER`, `CAN_RUN_COMMAND`,
  `CAN_CONTROL_APP`.
- **`sign_command(capability, resource)`** — o servidor propõe; assina com HMAC-
  SHA256 sobre `{capability, resource, nonce, issued_at, expires_at}`.
- **`verify_command(token, seen=nonce_store)`** — o Local Agent valida:
  assinatura (tempo constante), **prazo** (grants são curtos, ~30s), **nonce**
  (anti-replay). Sem os quatro, recusa honesta.
- **Segredo da ponte:** `ANTS_BRIDGE_SECRET` (env); nunca vai a log. Sem device
  I/O no módulo (teste garante).

Cobertura: `tests/test_local_agent_918.py` (round-trip, capacidade desconhecida,
adulteração, segredo errado, expiração, replay, ausência de I/O).

## Como a ação real será aberta (ordem, uma por vez)

Cada capacidade entra como uma ferramenta do **ToolRegistry** (já existente), com
permissão, risco, schema, timeout e rollback — e **só** depois da anterior estar
sólida:

Distinção profissional: **arquivo** é seguro executar como ponte no servidor;
**dispositivo** (tela/app/comando) é só **validado + delegado** ao agente nativo —
o servidor nunca age no dispositivo.

1. `CAN_READ_FILES` — **ABERTA · executada** (gated: grant + `read_files` +
   `path_guard`). Read-only.
2. `CAN_WRITE_FILES` — **ABERTA · executada** (dry-run salvo `confirm` + `write_files`
   + `path_guard`).
3. `CAN_SCREENSHOT` — **ABERTA · validada+delegada** (escopo `screen_capture`;
   envelope autorizado, `executed:false`).
4. `CAN_CONTROL_APP` — **ABERTA · validada+delegada** (escopo `run_apps`).
5. `CAN_RUN_COMMAND` — **ABERTA · validada+delegada** (o mais perigoso: escopo
   `system_commands` + **allowlist** (`command_guard`) + `confirm` obrigatório;
   nunca executado no servidor).
6. `CAN_BROWSER` — **ainda fechada** (demonstra a regra "uma por vez"): responde
   "capacidade ainda não aberta".

Runtime: `ANTS_LOCAL_AGENT=native` marca o app nativo; sem isso, é o servidor/ponte
(padrão). As capacidades de dispositivo só executam de fato no runtime nativo.

Antes de **cada** ação: permissão por escopo, confirmação para destrutivo, dry-run,
rollback, **botão de pânico** (`POST /device/panic`), auditoria, sanitização anti
prompt-injection (todo texto de tela/web/app é **dado**, nunca instrução),
Scope Guard + Goal-drift. Runtime web continua "apenas planeja".

## O que NÃO existe ainda (honestidade)

- **Nenhuma ação de dispositivo** (tela/app/comando) é executada por este código —
  são só **validadas** e delegadas ao agente nativo (`executed:false`). Só arquivo
  executa, como ponte, sob todas as travas.
- Enquanto não há app nativo (Tauri), o `executor.py` roda no **servidor** como
  ponte de referência (lê/escreve o FS do container, sob todas as travas; autoriza
  dispositivo sem agir). Quando o Local Agent nativo existir, o mesmo fluxo
  grant→verify→executar roda **no dispositivo**.
- O transporte real (WebSocket autenticado Render↔Tauri) e o *device identity*
  handshake ainda não existem — só o formato do grant assinado e o envelope.
- O transporte real (WebSocket autenticado Render↔Tauri) e o handshake de
  *device identity* ainda não foram implementados — só o formato do grant assinado.
