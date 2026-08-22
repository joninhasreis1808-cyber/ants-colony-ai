# Ant's 9.12 — Próximos passos 1·2·3 (pós-PLANO_MESTRE)

Depois de fechar as fases B–H, revi a conversa inteira, auditei que **todas as
peças estão na `main`** (script de auditoria: 15/15 módulos + painel), e rodei uma
**simulação ponta a ponta** com o código real. A simulação revelou um refino
necessário (R) e então implementei os três próximos passos — com atenção extra no
1 e no 3.

## R · Refino descoberto na simulação
Numa missão de **cálculo**, a decisão coletiva saía "investigar" porque o voto
exigia evidência/fontes externas — critério que só cabe a rotas de **pesquisa**.
Corrigido: `DecisionSignals.evidence_based`; rotas determinísticas julgam por
confiança + ausência de contradição/desvio. O guarda de desvio também deixou de
vetar falsamente uma resposta **numérica** (mede contra o objetivo).

## Passo 1 (atenção extra) · A missão AGE com ferramentas gated — Manus ponta a ponta
`backend/hivemind/tool_executor.py`: o executor de missões deixa de só narrar e
**chama ferramentas do ToolRegistry** (capacidade + escopo + dry-run). Ligações
passo→ferramenta são extensíveis (`_BINDINGS`; hoje `resolver→compute`). A
resposta real da ferramenta entra na missão; recusa honesta quando falta escopo.
O desfecho traz `tools_used` e a Câmera mostra "Operárias usaram a ferramenta X".
**Prova em navegador real**: "quanto é 12*12" → laço converge, usa `compute`,
Resposta **144**.

## Passo 2 · Persistência opt-in — a colônia lembra entre reinícios
`backend/hivemind/state_store.py` (JSON atômico, ligado por `ANTS_STATE_DIR`). A
**memória de experiência** (B3) e o **livro-razão de evolução** (FASE H) gravam a
cada mutação e recarregam do disco. Sem a variável, tudo segue em memória
(comportamento atual — nada quebra). `reload_experience()` /
`reload_evolution_ledger()` releem após um reinício.

## Passo 3 (atenção extra) · Console visual de Missão Autônoma + Evolução
`web/js/mission_console.js` (aditivo, **sem tocar nos 4 JS legados**): dois
consoles na aba Colônia — um lança `/mission/auto` (mostra rota, ciclos,
ferramentas usadas, resposta) e outro opera `/evolution` (minerar → aprovar/
rejeitar → aplicar, com o status de cada proposta). Usa `AntAPI` (fonte única),
estilos próprios, zero emoji, e mostra erro honesto quando a rota owner-gated
exige token num deploy público. **Verificado no navegador real, zero erros de JS.**

## Números
- **685 testes verdes** (+12 nesta rodada: R+1+2+3), 5 skipped.
- MD5 dos 4 JS legados (chat/bots/memory/factory) **idêntico**.
- Auditoria 15/15 + simulação ponta a ponta **PASS**.

Nada do que foi pedido ficou de fora: a colônia agora **planeja, decide em
consenso, AGE com mãos travadas, itera com freios, lembra entre reinícios e evolui
com sua assinatura** — e o dono controla tudo isso por uma interface honesta.
