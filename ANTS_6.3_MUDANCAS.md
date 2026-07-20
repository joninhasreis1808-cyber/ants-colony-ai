# Ant's 6.3 — Linha do Tempo unificada + IA↔Interface 100% real

> Documento honesto, com prova. Tudo aditivo; nada que funcionava foi perdido.

## Contrato preservado
- **Testes:** `374 → 378 passed, 5 skipped` (só subiu).
- **MD5 dos 4 JS legados — inalterados:** chat `e1cc6df5…` · bots `ed95b37e…` ·
  memory `de5d8499…` · factory `18b0d5a8…`.
- **Zero mockup** (`grep Math.random|SAMPLE` limpo) · **zero emojis na tela**
  (ícones SVG) · **zero dependências novas**.

## Bloco A — IA 100% offline (verificado)
Pergunta *"o que são feromônios…"* com busca externa bloqueada → resposta do
cérebro próprio com **confiança 0.727**, castas e lacunas (não "sem evidências").

## Bloco B — Console + Missões fundidos na Linha do Tempo
Uma só aba, três seções coesas (`web/js/timeline_hub.js`, 161 linhas):
1. **Fluxo & Missões** — caminho da missão (Pedido→…→Resposta) acende com
   `ants:task-tick` reais; missões permanentes de `GET /organism/missions`
   com **criar** (`POST`) e cancelar.
2. **Registro Vivo** — ações por casta (ícone+cor), com **motivo** e
   "quem recrutou quem".
3. **Console (Diagnóstico)** — stream real com **filtros** (tudo/erros/ações/
   memória/segurança), **export .log** e limpar.
- **Fonte única de eventos**: um `GET /events/history` alimenta registro+console;
  sem polling duplicado. `live_panels.js` cedeu essas três responsabilidades ao
  hub (comportamento movido inteiro), seguindo com recursos/cognição/rainha.
- Abas **Console** e **Missões** removidas do topo e do bottom-nav; IDs legados
  (`console-log`, `console-clear`, `missions-list`, `decision-timeline`,
  `nav-mission-count`) preservados dentro da nova aba.
- Auditoria completa em `AUDITORIA_6.3.md`.

## Bloco C — IA↔Interface de verdade
- **Ponte real** `window.Ants` (6.2) + poller único que alimenta todas as seções.
- **UI Kernel** (`web/js/ui_kernel.js`, 86 linhas): a IA modifica a interface por
  comandos **declarativos** de um conjunto **fechado** (highlight, update_progress,
  open/close_section, append_timeline, set_state, toast). Comando inválido é
  ignorado com log — **nunca** HTML arbitrário. `Ants.ui(cmd)` na ponte.
- **"Como cheguei nisso?"** — abre o motivo real (confiança, fontes, fatos da
  memória, castas, lacunas + decisão de `/colony/observability`).

## Bloco D — melhorias pertinentes
- **`GET /hive/recruitment/{task_id}`** — cadeia real "quem chamou quem".
- **Trust persistente**: `trust_store` (KV/SQLite); a colmeia registra acerto/erro
  por bot ao concluir tarefa; `GET /organism/trust` expõe. DNA/tradições/feedback
  já persistiam (6.2). **Prova: trust e DNA sobrevivem a restart HTTP real.**
- **Estado honesto** do indicador via `/colony/state` (herdado, mantido).

## Prova (Playwright, headless)
- 3 perguntas aleatórias → cada uma dispara `POST /hive/task` + `GET /hive/status`,
  fluxo a 100%, registro enche (42/45/47 linhas reais).
- Fusão: abas Console/Missões ausentes; 3 seções vivas; filtros+export; missão
  criada por `POST` real; kernel aplica ações válidas e recusa inválidas.
- Persistência: trust (0.55×5 bots) e DNA ("documentação primeiro") idênticos
  após reinício do servidor.

## Honestamente não feito (fora de escopo, como pedido)
- NeuralBus global, Digital Twin, reprodução de bots, hormônios extras — **não**
  implementados de propósito (o prompt pediu para deixar fora desta entrega).
- Ativação por-camada da Cognição segue **mapeada** de `/mind/think` (não há
  endpoint de ativação por-camada; não criei SSE novo).
