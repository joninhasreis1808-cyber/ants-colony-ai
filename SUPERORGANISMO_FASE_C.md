# Ant's 9.8 — FASE C: Superorganismo (a colônia decide, foca e se realoca)

A FASE B (9.7) deu à colônia uma **mente** que planeja e executa. A **FASE C** faz
essa mente ser **coletiva e emergente** — como um formigueiro de verdade, onde
nenhuma formiga manda, mas o conjunto se coordena. Três mecanismos, todos
determinísticos, offline, e **aditivos** (não mudam o estado done/failed do
executor da FASE B — são camadas de coordenação que informam a interface e a
autonomia futura da FASE E).

## Os três mecanismos

| # | Peça | Arquivo | O que faz |
|---|------|---------|-----------|
| C1 | **Decisão coletiva** | `backend/hivemind/collective.py` | as 4 castas **votam** comprometer × investigar por sinais reais (evidências, fontes, contradições, desvio, confiança) via quórum (70%). Contradição aberta ou desvio é **veto de qualidade dos soldados**. Sem consenso, prevalece a prudência. |
| C2 | **Estigmergia de atenção** | `backend/hivemind/attention.py` | cada descoberta reforça o **feromônio** das suas palavras-chave; o que se repete sobe, o resto evapora. O **foco** da missão emerge do campo, não de uma ordem fixa. |
| C3 | **Divisão de trabalho** | `backend/hivemind/labor.py` | quando a colônia decide investigar, recruta **exatamente a casta que resolve o gargalo** (contradição→soldados, desvio→rainha, poucas fontes→exploradoras, pouca evidência→operárias). |

## Como tudo se encaixa na missão (FASE B · B5)

```
executa o TaskGraph  ─┐
                      ▼
             [C2] cada passo reforça o campo de ATENÇÃO (foco emerge)
                      ▼
             [B4] verifica desvio de objetivo
                      ▼
             [C1] as castas VOTAM comprometer × investigar (quórum + veto)
                      ▼
             [C3] se "investigar": realoca a casta do gargalo
                      ▼
             [B3] aprende (estratégia/erro) · desfecho auditável
```

O desfecho de `/mission/run` (e `GET /mission/{id}`) agora traz, além de rota,
grafo, blackboard e checkpoints: **`collective`** (o veredito e os votos),
**`attention`** (o foco emergente, top-6) e **`allocation`** (a realocação
sugerida). Todos os passos emitem eventos por casta para a **Câmera ao Vivo** —
o consenso e a realocação aparecem no trajeto, sem nenhuma mudança de front-end.

## Reuso honesto

Nada foi reinventado: C1 usa o `QuorumDecision` que já existia; C2 usa o
`PheromoneField` da estigmergia; C3 fala a mesma língua do `Recruiter`. A FASE C
**compôs** os primitivos biológicos da colônia num fluxo de missão real.

## Postura visível

`GET /health` → bloco `intelligence` agora inclui `collective_decision`,
`attention_field` e `adaptive_labor`.

## Testes

- C1 `test_collective_98.py` (7) · C2 `test_attention_98.py` (4) · C3 `test_labor_98.py` (6)
- `test_health_intelligence_97.py` estendido para o superorganismo

**Suíte total: 633 verdes, 5 skipped.** MD5 dos 4 JS legados **intacto**. Nenhum
comportamento anterior mudou — a FASE C só somou coordenação coletiva à colônia.
