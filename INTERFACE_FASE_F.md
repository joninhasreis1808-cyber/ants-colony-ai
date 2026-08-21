# Ant's 9.9 — FASE F: Interface reativa (a "Mente da Colônia" visível)

Toda a inteligência das FASES B–E vivia no backend, mas era **invisível** na
interface. A **FASE F** dá à PWA um painel que mostra, **ao vivo e honestamente**,
a mente que a colônia ganhou — **sem tocar em nenhum dos 4 JS legados imutáveis**
(`chat.js`, `bots.js`, `memory.js`, `factory.js`).

## O painel "Mente da Colônia"

`web/js/mind_panel.js` (aditivo) renderiza, no container `#mind-panel` da aba
Colônia, o bloco `intelligence` do `/health`:

- **Rotas** que a Cartógrafa conhece (B1): `computation`, `memory`,
  `knowledge_base`, `reasoning`, `web_search`, `deep_research`, `device_action`.
- **Capacidades** ativas: planejador hierárquico, contradição, desvio de objetivo,
  decisão coletiva, atenção emergente, divisão de trabalho, laço autônomo.
- **Ferramentas** gated (FASE D) com **risco** e **disponibilidade real** — as que
  exigem permissão não concedida aparecem **riscadas**; `compute` (puro, sem
  escopo) aparece disponível.
- **Placar de aprendizado**: acertos/erros da memória de experiência (B3) + os
  endpoints `/mission` e `/mission/auto`.

## Como respeita as regras da casa

- **Fonte única** (9.4 · T6): o painel **não faz fetch próprio** — ele ouve o
  evento `ants:health` que o `app.js` já distribui. Uma verdade só, sem duplicar
  chamadas.
- **Estilos próprios**: injeta seu próprio `<style>` uma vez; não depende de CSS
  externo nem colide com o existente.
- **Zero emoji** (a regra do `noEmojiLayer`); só texto e as cores do tema.
- **Legado intocado**: o teste verifica o **MD5 dos 4 JS imutáveis** — inalterado.

## Prova

- `tests/test_web/test_mind_panel_99.py` (4): o JS lê a fonte única e mostra
  risco/disponibilidade; o `index.html` inclui o script e o container; o `/health`
  entrega os campos consumidos; os 4 JS legados seguem com o MD5 idêntico.
- **Smoke em navegador real** (Chromium headless): o painel renderiza com dados
  vivos, **sem nenhum erro de JS**, mostrando as ferramentas de arquivo riscadas
  (sem permissão) e o `compute` disponível.

**Suíte total: 653 verdes, 5 skipped.** A interface finalmente **mostra** o
superorganismo — honesta, reativa e sem quebrar nada.
