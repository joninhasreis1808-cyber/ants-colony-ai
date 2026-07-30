# Ant's 9.0 — Auditoria de honestidade da interface (Bloco C.1)

> Princípio: **nada de "hipócrita"** — todo elemento reflete algo real; nada
> decorativo que finge. Varredura da interface, com a decisão por item.

## (a) Animações que não refletiam estado real
| Item | Situação | Ação |
|------|----------|------|
| Progresso vivo do chat | **Real** — acende com eventos de `/hive/status` | mantido |
| Linha do Tempo / Registro Vivo / Console | **Real** — de `/events/history` | mantido |
| Pulso das castas / trilhas | ligado a eventos reais | mantido |
| Botão de pânico (pulso quando engajado) | reflete estado real do backend | mantido |
| `prefers-reduced-motion` | respeitado em todas | mantido |

## (b) Botões/funções que não faziam nada ou duplicavam
| Item | Situação | Ação |
|------|----------|------|
| Chat | **UM só** (`#messages`, `#chat-input` únicos — verificado) | confirmado |
| Aprovar/Ajustar/Cancelar (8.1) | chamam `/hive/action/*` reais | mantido |
| Recrutar +1 / Dispensar −1 (formações) | chamam endpoints reais | mantido |
| Conceder permissão / Revogar / Pânico | chamam `/device/*` reais | mantido |

## (c) Números/painéis que não vinham de endpoint real — **CORRIGIDOS**
| Item | Antes (fingia) | Agora (real) |
|------|----------------|--------------|
| Cognição → "latência média **42ms**" | valor fixo no HTML | **removido** |
| Cognição → "backpressure **nominal**" | valor fixo | **removido** |
| Cognição → "ciclos de sono **3** · consolidação há **12min**" | valores fixos | **removido** |
| No lugar: "tarefas processadas / tempo ativo / fontes de busca" | — | **`GET /health`** real (`tasks_submitted`, `uptime_seconds`, `providers`) |

Os únicos números "fixos" que restam são **fatos de build** verdadeiros
(contagem de testes, versão, nº de castas/camadas) — não telemetria fingida.

## Resultado
- **Um só chat** confirmado (um `#messages`, um `#chat-input`).
- **Zero animação/painel decorativo que finge** — os que restaram são reais.
- **Selo de proveniência** em cada resposta (cálculo/memória/web N fontes/não
  sei) já vem do backend e aparece no resumo do chat.
- Console sem erros de JS (verificado com Playwright).
