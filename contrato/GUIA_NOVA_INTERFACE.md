# Ant's — Guia para uma interface nova (sem tocar no cérebro)

> As regras que **qualquer** interface nova deve seguir para funcionar com este
> backend intacto. Curto e direto. O detalhe de cada endpoint está em
> `API_CONTRACT.md`; o que a IA faz, em `INVENTARIO_FUNCIONALIDADES.md`.

## 1 · Como o frontend é servido (não mude isto)
- O backend serve a pasta `web/` na **raiz** via `StaticFiles(html=True)`
  (`backend/api/main.py`): `app.mount("/", StaticFiles(directory=web, html=True))`.
  Logo `GET /` → `web/index.html`; qualquer asset em `web/` é servido por caminho.
- **Rodar local:** `uvicorn backend.api.main:app --host 127.0.0.1 --port 8000`
  (a nova UI abre em `http://127.0.0.1:8000`). Empacotado (PyInstaller) a pasta
  `web/` é embutida — mantenha os assets **relativos à raiz** (`/css/…`, `/js/…`).
- A nova interface é **outra pasta `web/` (ou os mesmos arquivos)**: HTML/CSS/JS
  estáticos, sem build obrigatório, servidos do mesmo mount. Não precisa de
  servidor Node — é só substituir/estender os estáticos.
- **Mesma origem:** a UI chama a API na própria origem (`location.origin`), sem
  CORS especial. (O backend já libera CORS `*`, mas o certo é same-origin.)

## 2 · PWA (manter)
- `web/manifest.json` (`start_url: "/"`, `display: standalone`,
  `name: "Ant's"`). Mantenha um manifest válido para a instalação.
- `web/sw.js` — service worker. **Regra de ouro (lição do 9.2):** assets em
  **stale-while-revalidate**, nunca cache-first (senão um deploy serve JS/CSS
  velho e "as animações param"). API sempre **network-first**. Bump do nome do
  cache a cada release.

## 3 · O contrato legado que a UI DEVE preservar (4 JS imutáveis por MD5)
Estes arquivos **não podem ser alterados** (travados por MD5) e procuram IDs
fixos no DOM. A nova interface precisa **conter esses IDs** (mesmo que
reestilizados) para os scripts seguirem funcionando — ou não incluí-los se
substituir a função, mas então não pode carregá-los. Recomendado: **manter os
IDs** e deixar os legados vivos.

| Script (MD5) | IDs no DOM que ele exige | Endpoints que usa |
|--------------|--------------------------|-------------------|
| `chat.js` `e1cc6df5…` | `chat-input`, `chat-send`, `messages` | `POST /hive/task`, `WS /hive/live/{id}`, `GET /hive/status/{id}` |
| `bots.js` `ed95b37e…` | `bot-grid`, `bot-log`, `task-input`, `task-send`, `.state` | `POST /hive/task`, `WS /hive/live/{id}` |
| `memory.js` `de5d8499…` | `mem-list`, `mem-query`, `mem-search`, `mem-sleep`, `mem-stats` | `GET /memory/health`, `POST /memory/recall`, `POST /memory/sleep` |
| `factory.js` `18b0d583…` | `fac-create`, `fac-desc`, `fac-result`, `fac-template` | `POST /factory/create`, `POST /factory/quick` |

Os legados dependem de um objeto global `Ant` (com `Ant.api` = base URL),
definido por `web/js/app.js` — carregue-o **antes** dos legados. A ponte
`ants_bridge.js`/`api_bridge.js` expõe `window.Ants`/`window.AntAPI` e centraliza
os eventos do cliente. No `index.html` atual todos os 4 legados + `app.js` +
pontes + `ui_kernel.js` já são carregados, e todos os IDs acima existem — use-o
como referência de ordem de carregamento. (Confira os MD5 no CI antes de publicar.)

## 4 · O fluxo de uma tarefa (o mínimo para o chat funcionar)
1. `POST /hive/task { goal }` → guarde `task_id`, mostre o `echo` **na hora**.
2. Acompanhe por **UMA** fonte de verdade (não duas brigando):
   - **Recomendado:** polling `GET /hive/status/{id}` a cada ~600ms; **ou** SSE
     `…/stream`; **ou** `WS /hive/live/{id}`. Escolha uma.
3. **Progresso honesto:** derive o % da **fase do último evento**
   (`plan→do→check→act`), monotônico, e **sempre 0→100 ao concluir**. Não use
   contador por tempo (lição do 9.2).
4. Fim: `status ∈ {done, failed}` ou `result != null`. Renderize `result.answer`
   + **selo de proveniência** (`result.provenance.source`) + `sources[]` clicáveis.
5. Registro vivo: cada `event {bot, phase, message, data, ts}` vira uma linha.

## 5 · O UI Kernel (a IA mexe na UI dentro de uma fronteira segura)
**Honestidade:** o **backend não emite** comandos de UI. O "UI Kernel"
(`web/js/ui_kernel.js`, `window.AntsKernel`) é **client-side**: um conjunto
**fechado** de ações que a ponte/IA aplica a partir de eventos — nunca executa
HTML arbitrário. Se a nova UI quiser esse recurso, reimplemente (ou reaproveite)
o kernel. Ações existentes e seu formato:

| Ação | Payload | Efeito |
|------|---------|--------|
| `highlight` | `{action, target, reason}` | realça uma casta/seção por instantes |
| `update_progress` | `{action, progress:0-100}` | move a barra + dispara `ants:task-tick` |
| `open_section` / `close_section` | `{action, target}` | abre/fecha uma aba/subseção |
| `append_timeline` | `{action, caste, text, ts}` | adiciona linha ao registro |
| `set_state` | `{action, target: <estado>}` | muda o estado (respiração) da colônia |
| `toast` | `{action, text}` | notificação efêmera |

Disparo: `window.AntsKernel.apply(cmd)` ou `document.dispatchEvent(new
CustomEvent("ants:ui", {detail: cmd|[cmds]}))`. Comando inválido é **ignorado
com log**, nunca roda HTML. Estados válidos de `set_state`: `dormant, observing,
exploring, building, verifying, learning, defending, executing`.

## 6 · Eventos internos do cliente (como os painéis conversam sem polling duplo)
A ponte (`api_bridge.js`) já centraliza: ao ver `POST /hive/task`, ela lê o
status e **dispara** `ants:task-tick { taskId, pct, done, status }` e
`ants:task-done`. Uma UI nova pode ouvir esses eventos em vez de cada painel
fazer o seu próprio polling — **uma fonte, muitos ouvintes**.

## 7 · Estado dos painéis (leia o real, nunca invente)
- Respiração/estado: `GET /colony/state` → atribua a um atributo (ex.:
  `data-colony-state`) e anime por CSS.
- Recursos: `GET /organism/vitals`. Rede/atividade: `GET /events/summary`.
- Memória: `GET /memory/health` (`counts.total`, `counts.strong`,
  `extra.avg_strength`). Cognição: `POST /mind/think`. Capacidades:
  `GET /organism/capabilities`. Rainha/decisões: `GET /events/history`.
- **Dado ausente = "—"**, jamais um número inventado (princípio do projeto).

## 8 · Segurança que a UI precisa respeitar (9.3)
- Local: nada muda. Público (`ANTS_PUBLIC=1`): rotas sensíveis exigem token.
  **Não** embuta o token no JS do navegador de um deploy público — nesse cenário
  a UI pública é read-only/Q&A; as ações de device/permissão ficam para o app
  nativo (onde o loopback é confiável). Confira `GET /health` → `auth`.
- Ação em arquivo exige pasta autorizada antes (`POST /device/paths/allow`),
  senão o `path_guard` recusa com 403 (é defesa, mostre a mensagem ao usuário).

## 9 · Regras de estilo (do projeto, mantenha)
- **Zero emojis** na UI nova (ícones SVG). *(Os JS legados têm emojis internos;
  são imutáveis — não conte como violação, mas não os replique na casca nova.)*
- Offline-first: a UI degrada com dignidade quando um endpoint falha
  ("colônia adormecida"), nunca trava nem mente.
- `prefers-reduced-motion` respeitado; console sem erros.
- Tipografia/paleta próprias (Newsreader + IBM Plex Mono no atual) — livre para
  redesenhar, desde que os **IDs legados** e o **contrato de dados** fiquem.

## 10 · Checklist de compatibilidade (antes de publicar a nova UI)
```
[ ] Servida de web/ na raiz (mesmo mount), assets em caminho absoluto (/js, /css)
[ ] IDs legados presentes (§3) — ou legados não carregados se substituídos
[ ] MD5 dos 4 JS legados inalterados (se mantidos)
[ ] Uma fonte de verdade para progresso (polling OU sse OU ws), % por fase, 0→100
[ ] result.answer + provenance + sources renderizados
[ ] Painéis leem endpoints reais; ausente = "—"
[ ] sw.js stale-while-revalidate + bump de cache; manifest válido
[ ] Zero emojis na casca nova; reduced-motion; console limpo
[ ] /health.auth conferido para o modo de deploy (local vs público)
```
