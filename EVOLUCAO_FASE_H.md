# Ant's 9.11 — FASE H: Evolução controlada (a última do PLANO_MESTRE)

Um superorganismo que aprende precisa poder **evoluir** — mas evolução sem controle
é perigosa. A **FASE H** fecha o PLANO_MESTRE dando à colônia um caminho de melhoria
**seguro, auditável e reversível**, com uma regra inviolável: **a colônia NUNCA
reescreve o próprio código nem muda produção sozinha.**

## Como a colônia evolui

A colônia **propõe** melhorias a partir de sinais **reais** da própria experiência
(FASE B3):

- uma rota que **falhou** repetidamente para objetivos parecidos → propõe
  **despriorizá-la**;
- uma rota que **venceu** repetidamente → propõe **promovê-la**.

Cada proposta entra num **livro-razão** (`EvolutionLedger`) e passa por um fluxo
gated:

```
  a colônia PROPÕE ──▶ o DONO aprova/rejeita ──▶ (se aprovada) APLICA
        │                      │                          │
     mineração            require_owner            só mexe em DADOS
   (experiência)          (assinatura)          (viés da memória, reversível)
```

## As quatro garantias

| Garantia | Como |
|---|---|
| **Auditável** | livro-razão append-only; cada proposta tem `evidence` e `history` |
| **Versionada** | cada transição (proposed → approved/rejected → applied) fica gravada com timestamp |
| **Gated** | `require_owner` em todas as rotas; aplicar exige aprovação explícita |
| **Reversível & sem código** | aplicar só reforça/penaliza a **memória de experiência** (dados); **nenhum código de produção é tocado** |

## Porta REST (owner-gated)

- `GET /evolution` — livro-razão completo (auditoria)
- `POST /evolution/mine` — minera a experiência e registra propostas (não aplica)
- `POST /evolution/{id}/approve` · `/reject` — decisão do dono
- `POST /evolution/{id}/apply` — aplica uma proposta **aprovada** (só dados)

`GET /health` → `intelligence.controlled_evolution: true` +
`evolution_endpoint: "/evolution"`.

## Testes

`tests/test_evolution_911.py` (9): mineração propõe despriorizar/promover;
abaixo do limiar não propõe; aprovar→aplicar muda **só** a memória (+1 registro,
"nenhum código tocado"); rejeitar impede aplicar; histórico registra cada
transição; endpoint completo (mine→approve→apply→409); `/health` expõe a postura.

**Suíte total: 673 verdes, 5 skipped.** MD5 dos 4 JS legados **intacto**. A colônia
agora evolui a própria decisão — sem jamais fugir da coleira do dono.
