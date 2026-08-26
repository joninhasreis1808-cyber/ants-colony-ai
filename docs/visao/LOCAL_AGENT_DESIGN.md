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

1. `CAN_READ_FILES` — **ABERTA (9.18)**: leitura via `backend/local_agent/
   executor.py`, com defesa em profundidade (grant assinado + escopo `read_files`
   + `path_guard` + capacidade explicitamente aberta) e auditoria. Read-only.
2. `CAN_WRITE_FILES` (dry-run por padrão; confirm + escopo `write_files`) — próxima.
3. `CAN_SCREENSHOT` / `CAN_CONTROL_APP` (abrir apps/URLs).
4. `CAN_RUN_COMMAND` (allowlist de comandos; o mais perigoso — por último).
5. Input/tela no nativo.

Antes de **cada** ação: permissão por escopo, confirmação para destrutivo, dry-run,
rollback, **botão de pânico** (`POST /device/panic`), auditoria, sanitização anti
prompt-injection (todo texto de tela/web/app é **dado**, nunca instrução),
Scope Guard + Goal-drift. Runtime web continua "apenas planeja".

## O que NÃO existe ainda (honestidade)

- Só a **leitura** (`CAN_READ_FILES`) está aberta; escrita/tela/input/app/comando
  **não** — respondem "capacidade ainda não aberta".
- Enquanto não há app nativo (Tauri), o `executor.py` roda no **servidor** como
  ponte de referência (lê o FS do container, sob todas as travas). Quando o Local
  Agent nativo existir, o mesmo fluxo grant→verify→ler roda **no dispositivo**.
- O transporte real (WebSocket autenticado Render↔Tauri) e o handshake de
  *device identity* ainda não foram implementados — só o formato do grant assinado.
