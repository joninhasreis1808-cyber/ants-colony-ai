# Auditoria B.1 — antes de fundir (nada se perde)

Mapa do que existe hoje em cada aba, e onde reaparece na nova **Linha do Tempo**.

## Linha do Tempo (atual)
| Função/elemento | Fonte real | Reaparece em |
|---|---|---|
| `#decision-timeline` (eventos por integrante) | `GET /events/history` | Seção 2 — Registro Vivo |
| ícone + cor por casta, timestamp, texto | mapa IC/CS | Seção 2 (mantido + motivo + recrutamento) |
| refresh ao abrir / em `ants:task-done` / 5s | evento/interval | timeline_hub (poller único) |

## Console (atual)
| Função/elemento | Fonte real | Reaparece em |
|---|---|---|
| `#console-log` stream cru | `GET /events/history?limit=60` | Seção 3 — Console (Diagnóstico) |
| append ao vivo de chamadas de rede | evento `ants:netcall` | Seção 3 (mantido) |
| botão `#console-clear` (Limpar) | — | Seção 3 (mantido) |
| chips "nível: debug/trace" (por modo) | classes only-dev/only-sci | Seção 3 (mantido) |
| **filtros por tipo (erro/ação/memória/segurança)** | — (não existia funcional) | Seção 3 — **adicionado** |
| **export** | — (não existia) | Seção 3 — **adicionado** (baixa .log) |

## Missões (atual)
| Função/elemento | Fonte real | Reaparece em |
|---|---|---|
| `#missions-list` (missões permanentes) | `GET /organism/missions` | Seção 1 — Fluxo/Missões |
| badge `#nav-mission-count` | contagem | Seção 1 (contador) |
| **criar missão** | `POST /organism/missions` (existia no back) | Seção 1 — **adicionado** (form) |
| caminho da missão (Pedido→…→Resposta) | `#research-flow` (aba Chat) + `/hive/status` | Seção 1 — **espelho vivo** do progresso atual |

## Navegação
- Remover itens `data-tab="console"` e `data-tab="missions"` do topo e do bottom-nav.
- Remover seções `#tab-console` e `#tab-missions` (conteúdo migra para `#tab-timeline`).
- IDs legados preservados: `console-log`, `console-clear`, `missions-list`,
  `decision-timeline`, `nav-mission-count` — todos migram para dentro da aba
  Linha do Tempo (nenhum é removido).

## Fonte única de eventos
`web/js/timeline_hub.js` faz **um** fetch de `/events/history` (+`/organism/missions`)
e distribui às 3 seções — sem polling duplicado. `live_panels.js` deixa de
tratar timeline/console/missions (comportamento movido inteiro para o hub);
segue cuidando de recursos/cognição/rainha.
