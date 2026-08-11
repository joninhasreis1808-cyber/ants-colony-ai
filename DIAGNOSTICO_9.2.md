# Ant's 9.2 — Diagnóstico (Bloco A) antes de corrigir

> Causa real de cada sintoma, verificada no código. Só depois disto, o conserto.

## A.1 · Animações pararam (regressão recorrente) — CAUSA ENCONTRADA
O service worker serve os assets em **cache-first** (`web/sw.js`):
```js
// Assets: cache-first.
e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
```
Depois de cada merge com JS/CSS novo, o navegador continua rodando o **código
velho em cache** até o nome do cache mudar E o novo SW ativar E o cliente
recarregar. Bump manual de versão (`ants-v18`) não basta: se eu esquecer, ou o
SW antigo ainda estiver ativo, as animações rodam com CSS/JS defasado. **É a
raiz da regressão "as animações pararam de novo".**
**Correção (B):** `stale-while-revalidate` para assets same-origin — serve o
cache na hora (rápido) **e sempre busca a versão nova em segundo plano**,
atualizando para o próximo load. Merges nunca mais servem código velho. A API
continua network-first. (As demais suspeitas — `display:none`, RAF, reduced-
motion — foram checadas: a respiração liga em `data-colony-state` via
`/colony/state` e os `@keyframes` existem; o problema era o cache.)

## A.2 · Barra de progresso intermitente — CAUSA ENCONTRADA
- **Fonte única, sem corrida:** o progresso é dirigido só pelo *polling* de
  `api_bridge.startFlow` (`/hive/status`), que emite `ants:task-tick` →
  `timeline_hub.renderPath`. O `web/js/sse.js` (adicionado no 8.0) **nunca é
  chamado** — é código morto; não há briga SSE×polling.
- **O % é baseado em TEMPO, não em eventos:** `startFlow` incrementa um contador
  a cada 600ms (`if (i < steps-2) i++`) e salta para 100 no fim. Logo o
  progresso não reflete o andamento real e "falha às vezes" (tarefas instantâneas
  concluem antes do 1º tick; tarefas longas estagnam no contador).
**Correção (C):** derivar o % dos **eventos reais** de `/hive/status` (fase do
último evento → etapa), garantir **0→100 sempre** ao concluir, **reset limpo**
entre missões, e **remover o `sse.js` morto** (uma fonte de verdade só).

## A.3 · Busca inconsistente e "confusa" — CAUSA ENCONTRADA
A resposta da web **não passa pelo compositor** (`response_composer` do 9.1 não
é usado no pipeline de busca) — o texto vem cru do `decider` (despejo de
snippet). Daí a "confusão".
**Correção (D):** sintetizar a resposta da web pelo `response_composer.web()`
— resposta clara + **selo de proveniência** + **fontes clicáveis**; se as fontes
divergem, uma linha honesta. Consistência via cache (2ª vez `cached:true`, já do
9.0). Ordem da cascata confirmada: memória → seed → base curada → Wikipedia →
DuckDuckGo → (SearXNG/Tavily/Brave se env) → raciocínio.

## A.4 · Ruído na interface — ITENS ENCONTRADOS (aba Ambiente)
Auditoria honesta de CADA campo do "Mapa do Ambiente" — quais vêm de dado real
e quais eram placeholder eterno "—":

| Elemento | Situação real | Ação |
|----------|---------------|------|
| Internet → "Requisições nesta sessão" (`env-reqs`) | **real** (`/events/summary`) | **manter** |
| Internet → "Domínios visitados" (`env-domains`) | sempre "—" (sem fonte) | **remover** |
| Internet → "Fontes verificadas" (`env-verified`) | sempre "—" (sem fonte) | **remover** |
| Dispositivo → arquivos/processos (`env-files`,`env-procs`) | sempre "—" (sem fonte) | **remover nó** |
| Dispositivo → "Sensores" | texto estático decorativo | **remover nó** |
| Conhecimento → nós/relações/confiança (`env-nodes`…) | sempre "—" (sem fonte) | **remover nó** |
| Memória → curto prazo/consolidadas/força | **quebrado**: `live_panels` lia chaves inexistentes (`short_term`, `avg_strength` na raiz) em vez de `counts.total/strong` e `extra.avg_strength` → sempre "—" | **CONSERTAR** (mostrar dado real) |
| `sse.js` carregado mas nunca usado | código morto no bundle | **remover** |
| Cognição (dev) — métricas | já corrigido no 9.0 (dados reais de `/health`) | mantido |
| Selo de proveniência | real, útil | manter/realçar |

Descoberta além do sintoma original: a aba Ambiente tinha **um único campo
real** (requisições); todo o resto era placeholder "—" ou bug de chave. A
Memória tem dado real em `/memory/health` (total, fortes, força média) — foi
**consertada** (não removida). Os nós sem fonte foram **removidos** em vez de
fingir. O resto do app (progresso, registro vivo, console, formações,
permissões, Cognição) reflete estado real e fica. "Antes/depois" no PR.
