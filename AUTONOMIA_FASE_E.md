# Ant's 9.9 — FASE E: Autonomia segura (o laço Observar→Planejar→Agir→Verificar)

A FASE B roda **uma passada**. Um agente autônomo de verdade **itera**: quando a
decisão coletiva (FASE C) foi "investigar", a colônia observa o que faltou,
replaneja, age de novo e reverifica — até **convergir** ou até um **governador de
segurança** mandar parar. **Nunca um laço infinito.**

## O laço

```
        ┌───────────────────────────────────────────┐
        ▼                                           │
   OBSERVAR ─→ PLANEJAR ─→ AGIR ─→ VERIFICAR ─→ decisão coletiva
   (sinais)   (FASE B)   (ferramentas   (FASE C)      │
                          gated FASE D)               │
        │                                             │
        └── converge? teto? sem-progresso? falha? ────┘
                          │
                          ▼
                 desfecho auditável (ciclos + resposta)
```

## Segurança é a regra, não um detalhe

O `AutonomyGovernor` garante que o laço **sempre termina**:

| Freio | O que faz |
|---|---|
| **Teto de ciclos** | máx. 3 por padrão (1–5) — nunca roda para sempre |
| **Prazo (deadline)** | tempo de parede máximo |
| **Sem-progresso** | se a evidência não cresce entre ciclos, **para** (não insiste no que não anda) |
| **Falha + rollback** | um ciclo que falha para o laço e mantém o **último ciclo bom** |
| **Só age gated** | AGIR acontece **só pelas ferramentas da FASE D** (capacidade+escopo+dry-run) — a autonomia **jamais excede a permissão do dono** |

Cada ciclo é uma **Mission com checkpoints** (FASE A) — retomável.

## Como parar de verdade

- **Convergiu** → o consenso das castas disse "comprometer".
- **Sem progresso** → a evidência estagnou; investigar mais seria desperdício.
- **Contradição/desvio persistente** → veto dos soldados mantém "investigar" até o
  teto de ciclos (a colônia não entrega uma resposta contestada).
- **Falha** → rollback ao último ciclo bom.

## Porta REST

`POST /mission/auto` `{ "goal": "...", "deep": true, "online": true, "max_cycles": 3 }`
→ devolve o desfecho do laço: a lista de **ciclos** (decisão, progresso, evidência,
estado por ciclo), se **convergiu**, o **motivo da parada**, o **governador** e a
**resposta** final. `GET /health` → `intelligence.autonomous_loop: true`.

## Testes

`tests/test_autonomy_99.py` (7): converge quando a evidência cresce até o consenso;
para no teto de ciclos quando um veto persiste; para por sem-progresso quando a
evidência estagna; falha → rollback; convergência de primeira → um ciclo; endpoint
`/mission/auto`. **Suíte total: 649 verdes, 5 skipped.** MD5 dos 4 JS legados
**intacto**.
