# Ant's 9.10 — FASE G: Qualidade / Chaos (os freios seguram sob estresse)

Uma colônia autônoma com mãos que modificam só é confiável se **aguenta o caos**.
A **FASE G** injeta falhas deliberadas nas partes mais perigosas (o laço autônomo
da FASE E e as ferramentas gated da FASE D) e **prova** que cada abuso termina num
motivo honesto — **nunca** um loop infinito, uma queda ou uma fuga da trava.

Esta fase é **só testes**: nenhuma mudança de comportamento. Ela documenta e
blinda as garantias que as fases anteriores já ofereciam.

## G1 — Chaos do laço autônomo

`tests/test_chaos_autonomy_910.py`:

| Caos injetado | Garantia provada |
|---|---|
| Executor **estoura exceção** | contida → missão `failed` + **rollback** ao último ciclo bom |
| **Prazo 0** (deadline) | encerra após 1 ciclo com `prazo esgotado` |
| Veto persistente + evidência sempre crescente | **nunca excede o teto** de ciclos (`limite de ciclos`) |
| Qualquer caminho | `elapsed_seconds ≥ 0` e governador sempre reportado |

## G2 — Chaos das ferramentas gated

`tests/test_tools/test_chaos_tools_910.py`:

| Abuso | Garantia provada |
|---|---|
| **Conteúdo gigante** (>200 KB) | erro honesto, **sem crash**, nada escrito |
| **Travessia de caminho** (`..`) em write **e** delete | `path_guard` barra → recusa |
| **Args malformados** (sem path) | recusa; `compute` com lixo → erro, não crash |
| **Ferramenta desconhecida** | recusa honesta |
| **Escopo revogado no meio** | próxima escrita barrada; a anterior permanece |
| `compute` puro | disponível **sob qualquer escopo** (não depende de permissão) |

## Resultado

**Suíte total: 664 verdes, 5 skipped** (+11 testes de caos). MD5 dos 4 JS legados
**intacto**. O superorganismo autônomo se mostra **resiliente**: sob exceção,
prazo, abuso de entrada ou revogação de permissão, os freios seguram — a colônia
para com um motivo claro, sem nunca travar nem escapar da coleira.
