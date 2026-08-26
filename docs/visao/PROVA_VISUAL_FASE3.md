# Prova visual da interface — FASE 3 (9.18 · Passo 3)

> Prova executável (Regra 2 do PROTOCOLO). Capturada com Playwright (Chromium
> headless) contra o app real (`uvicorn` local), com o onboarding dispensado
> (`localStorage['ants-onboarded']='1'`). Screenshots entregues ao dono:
> `ui_desktop_1280.png`, `ui_mobile_390.png`, `ui_selo_epistemico.png`.

## Métricas medidas

| Cenário | Métrica | Resultado |
|---------|---------|-----------|
| Desktop 1280×800 | overflow horizontal da página | **0** |
| Desktop 1280×800 | itens de navegação no DOM | 14 (sidebar + bottom-nav coexistem) |
| Celular 390×844 | **scroll horizontal da página** | **0** (achado 1 do dossiê resolvido) |
| Celular 390×844 | bottom-nav visível | **sim** |
| Celular 390×844 | elementos além da viewport | 8 — **todos dentro de um container `overflow-x:auto`** (a tira de navegação rolável), não perda de conteúdo |
| Missão de cálculo | selo de proveniência | **"cálculo exato · confiança 1"** |
| Missão de cálculo | rótulo epistêmico (FASE 1) | **"VERIFICADO"** (`ps-epi-verified`, verde) |

## Leitura honesta

- O **achado 1** (dossiê 9.3: 98 elementos cortados por `overflow:hidden`, **sem**
  rolagem) está **resolvido**: hoje a página não rola na horizontal (0) e os únicos
  8 elementos que ultrapassam a viewport vivem numa **tira de navegação rolável**
  (`overflow-x:auto`) — comportamento intencional, não corte de conteúdo.
- A **bottom-nav** aparece no celular; a responsividade (T-C) está de pé.
- O **rótulo epistêmico** (Passo/FASE 1) foi provado **ponta a ponta no navegador**:
  a missão "12×12" produziu o selo **VERIFICADO** com a cor semântica correta.

## O que NÃO foi verificado (Regra 5)

- **Safari/iOS real** (WebKit): a captura usou Chromium; o motor do iPhone difere.
- **A URL pública** (`ants-c2ik`) não foi capturada de fora — o proxy do sandbox
  bloqueia `onrender.com`; a prova é do mesmo código rodando localmente.
- Estados animados (spawn/erro/sono) não foram capturados quadro a quadro.
- A ferramenta (Playwright) **não** faz parte das dependências do projeto — foi
  instalada só para esta prova e **removida** ao final (não afeta o `pytest`).
