# AUTOAVALIAÇÃO DO ESTADO — Ant's (Fase 0 do Roteiro)

> **Natureza:** diagnóstico honesto e verificado, **sem nenhuma implementação**
> (Fase 0 do `ROTEIRO_ants_AUTOAVALIACAO_E_EVOLUCAO.md`). Base medida: `main`
> commit `01e3603`. **Aguardando autorização do dono antes da Fase 1.**

## Aviso de honestidade (antes de tudo)

- **Correção da própria Fase 0:** numa rodada anterior o `PROTOCOLO_COWORK.md` não
  havia sido anexado e eu **reconstruí** as 6 regras — e **errei**. O protocolo real
  (v1.0, base 9.3) foi fornecido depois; as 6 regras corretas são de **processo**
  (abaixo), não os princípios que eu havia inferido. Registro o erro em vez de
  escondê-lo (Regra 5).
- O dossiê `RELATORIO_PARA_CHATGPT.md` é da base **9.3 / commit `f94edf8` / 534
  testes**. O projeto avançou **muito** desde então (hoje 9.15 / `01e3603` / **712
  testes**). Por isso a maioria dos 9 achados **já foi resolvida** — confirmado por
  medição, não presunção.

## A · As 6 regras do PROTOCOLO_COWORK (as reais, v1.0)

1. **Diagnóstico antes de correção.** Nenhuma alteração entra sem uma medição que a
   justifique; hipótese derrubada por experimento é progresso, não fracasso.
2. **Prova executável, não descrição.** Toda mudança relevante vem com algo que o
   dono possa abrir e conferir (screenshot, artefato, saída de comando, número
   antes/depois) — nunca só "corrigido".
3. **A rede de segurança é sagrada.** `pytest -q` verde antes e depois; quem adiciona
   teste declara o total; quem quebra conserta ou reverte.
4. **Um commit por tarefa** (formato: versão · Tarefa · Diagnóstico · Correção ·
   Prova · Testes) — nada de commit-monstro.
5. **Declarar o que NÃO foi verificado** (a mais importante): todo relatório termina
   com essa seção; omitir limite é o mesmo que mentir.
6. **Interface nunca inventa texto.** Painel sem dado real não é preenchido com
   exemplo; "ao vivo" só se for ao vivo; estado vazio se explica.

> Observação: os *princípios* que eu havia reconstruído (não reescrever, offline-
> first, MD5/IDs intactos, sem LLM-cérebro, cérebro remoto×corpo local) são reais e
> valem — mas vivem no `ROTEIRO`/`PLANO_MESTRE` (invariantes I1–I8), **não** são "as 6
> regras do protocolo". As duas coisas se somam; eu as confundi.

## B · Linha de base (medida)

| Métrica | Dossiê (9.3) | **Real agora (01e3603)** |
|---|---|---|
| Testes `pytest -q` | 534 | **712 passando, 5 skipped** |
| MD5 dos 4 JS legados | — | **intactos** (`chat e1cc6df5…`, `bots ed95b37e…`, `memory de5d8499…`, `factory 18b0d583…`) |
| Rotas | 84 | ~**97** decorators em `backend/api/routes/` |
| Módulos no `/health` | 25 | **26** |
| Arquivos front (JS) | 30 | **34** (JS puro, sem build) |
| Provedores de busca | Wikipedia, DuckDuckGo, Brave, Tavily | idem + `playwright_provider` |
| IDs legados no DOM | — | **18/18 presentes** |

## C · Estado dos 9 achados (reproduzidos contra o código real)

| # | Achado (dossiê 9.3) | Estado agora | Evidência medida |
|---|---|---|---|
| 1 | `.topbar` crava 624px em 390px | **Resolvido (estrutural)** | sem `min-width` fixo na `.topbar`; `design_system.css` reestrutura o topo. *Confirmação em pixel (Playwright) pendente — ver seção F.* |
| 2 | Só 1 breakpoint útil de celular | **Resolvido/ampliado** | breakpoints em `design_system.css` (`max-width:639px`, `min-width:640px`, `min-width:960px`) + `style.css`/`cloud.css` |
| 3 | 3 das 7 abas somem no celular | **Resolvido (estrutural)** | `bottomnav` (mobile) + 7 `data-tab` no `index.html`. *Visual pendente — ver F.* |
| 4 | Painel de texto fixo rotulado "tempo real" | **Resolvido** | `web/js/bot_camera.js` (Câmera ao Vivo) presente e ativo |
| 5 | Cache/memória/web indistinguíveis | **Resolvido** | `web/js/provenance_seal.js`: rótulos "busca na web" / "resposta da memória · repetida" / "conhecimento interno" + botão "buscar de novo" |
| 6 | Polling 600ms com SSE/WS ociosos | **Resolvido** | `api_bridge.js`: WebSocket `/hive/live/{id}` é **primário**; polling 600ms só **fallback** (9.4·T5) |
| 7 | `urllib` síncrono em rota async | **Resolvido** | `local_provider.py` usa `httpx` com `AsyncClient` (9.4·T7); `urllib` removido |
| 8 | 4 funções >60 linhas em `hive.py` | **Ainda existe (baixa)** | `solve`(69), `_compile_result`(87), `_compile_trace`(66), `_build_provenance`(102) |
| 9 | Contador de testes fixo "529" | **Resolvido** | front usa `id="stat-tests">—` e `id="chip-tests">— testes`, preenchidos do `/health` (contagem dinâmica). *Nota: chip "versão 9.4.0" está estagnado (real 9.15).* |

**Placar:** 8/9 resolvidos; 1 remanescente (achado 8, cosmético/baixo risco) + 1
detalhe menor (rótulo de versão no front).

## D · Atual × Proposto (o esqueleto já existe)

O `PLANO_MESTRE_ARQUITETURA_ANTS.md` descreve 8 fases (A–H) como futuro; na
prática, **elas já foram implementadas** ao longo dos ciclos anteriores (FASE A
fundação; B inteligência; C superorganismo; D ferramentas; E autonomia; F
interface; G qualidade; H evolução controlada). O esqueleto que o Roteiro manda
construir primeiro — **Task Graph, EventBus, Blackboard, Tool Registry, Verifier,
Checkpoint/Recovery — já existe**. O cruzamento detalhado, arquivo por arquivo
(✅/🟡/⬜), está em **`docs/visao/MAPA_ATUAL_x_VISAO.md`** (já no repositório).

**Resumo do que já existe vs. fronteira:**
- ✅ **Já existe e testado:** núcleo cooperativo (bus/blackboard/state), planejador
  hierárquico + Cartógrafa, hipóteses/verificador/contradição, castas + reputação +
  polimorfismo, metabolismo/homeostase/circadian/imunológico, Tool Registry +
  capabilities + path_guard, autonomia com governador, evolução controlada (só
  dados), Câmera ao Vivo + mind panel + mission console, proveniência, persistência
  opt-in, missão que AGE com ferramentas (compute, escrita de arquivo gated).
- 🟡 **Parcial (padronizar/conectar):** contratos de eventos unificados; nós do
  TaskGraph com `priority/confidence/evidence`; memória hierárquica L0–L6 nomeada;
  provenance schema; UI Command API tipada; cadeia de fallback explícita.
- ⬜ **Fronteira real (abrir por último, com cautela):** **Local Agent nativo**
  (ponte autenticada Render↔dispositivo — capability tokens, comandos assinados);
  **Browser Perception** (PAGE MODEL + relearn); modos FAST/DELIBERATE/CRITICAL
  formais; calibração de confiança; canary interno.

### Divergências documentação × código (a corrigir na narrativa)
- Números do dossiê defasados (534→712 testes; 84→97 rotas; 30→34 JS; 9.3→9.15).
- `PLANO_MESTRE` trata A–H como futuro, mas estão **implementados**.
- `RELATORIO_PARA_CHATGPT` lista 9 achados majoritariamente **já resolvidos**.
- Front exibe "versão 9.4.0" (estagnado) — cosmético.

## E · Ordem segura recomendada (proposta — NÃO implementar sem autorização)

Alinhada ao Roteiro, mas ajustada ao fato de o esqueleto já existir:

1. **Fase 1 — Consolidar/padronizar o que já existe** (baixo risco, alto retorno):
   unificar o esquema de eventos e `ColonyState` como fonte única; padronizar os
   nós do TaskGraph; documentar contratos. *Risco: baixo (aditivo). Cuidado:
   preservar formatos consumidos pela Câmera ao Vivo.*
2. **Higiene (achados 8 e 9-menor):** extrair as 4 funções longas de `hive.py`
   **sem mudar comportamento** (testes de caracterização antes); atualizar o rótulo
   de versão no front. *Risco: baixo-médio (regressão de comportamento em `hive.py`
   — mitigar com testes que fixam a saída atual).*
3. **Fase 2 — Tempo real:** já em grande parte feito (WS primário); resta reforçar
   reconexão com backoff e um só canal para câmera/progresso/painéis. *Risco:
   baixo.*
4. **Fase 3 — Repaginação da interface + confirmação visual dos achados 1–3**
   (Playwright 390px/1280px). *Risco: médio (CSS/IDs legados — regra 3).* 
5. **Fase 5 — Corpo local (Local Agent):** a fronteira mais estratégica **e** a mais
   sensível. Só depois de núcleo + interface sólidos. *Risco: alto (segurança da
   ponte) — abrir uma capacidade por vez, com dry-run/rollback/pânico/auditoria.*

## G · Status da Ordem de Serviço v9.4 (refino imediato) — medido

Os documentos `ROTEIRO_ants_9.4_*.md` descrevem o refino imediato. Estado real:

| Tarefa | O que pedia | Estado |
|---|---|---|
| T-A | Sidebar fixa (sticky) | ✅ `design_system.css:390` (`position:sticky;top:0;align-self:start`) |
| T-B | Remover botão "Memória", automatizar sob a Rainha + cartão em Sinais Vitais | ✅ **em grande parte** (nav sem aba "Memória"; cartão "Memória · viva" no Ambiente). *A prova do teste "pergunta repetida → cached sem clique" e do sono agendado a confirmar.* |
| T-C | Responsividade desktop/celular (bottom-nav) | ✅ `bottomnav` + breakpoints |
| T1 | `min-width` da topbar no celular (98→0) | ✅ (estrutural; visual pendente) |
| T3 | Selo de proveniência | ✅ `provenance_seal.js` |
| T4 | Abas por toque ≥44×44px | ✅ (bottom-nav; medida em px pendente) |
| T5 | Fim do polling 600ms → fonte única (SSE/WS) | ✅ WS primário, polling fallback |
| T6 | Unificar 2 chamadas de saúde | 🟡 a verificar (vários JS leem `/health`) |
| T7 | Remover chamada síncrona do provedor local | ✅ `httpx` async |
| T8 | Contador de testes real | ✅ dinâmico do `/health` |
| T9 | Zero emoji em `web/js/` (SVG) | 🟡 a verificar (o `grep -P` deste ambiente falhou; checar com ferramenta compatível) |
| T10 | Extrair 4 funções longas de `hive.py` **sem mudar comportamento** | ⬜ **pendente** (as 4 seguem >60 linhas) |
| Câmera ao Vivo | Live Bot View aprofundada, cache honesto | ✅ `bot_camera.js` |

**Resumo:** o refino v9.4 está **quase todo entregue**. Pendências reais: **T10**
(higiene de `hive.py`), confirmar **T6** e **T9**, atualizar o rótulo "versão 9.4.0"
no front, e provar visualmente (Playwright) T-B/T-C/T1/T4.

## H · Pendências abertas do PROTOCOLO (seção 4) — estado atual

| Pendência (protocolo, 9.3) | Estado agora |
|---|---|
| Tela branca no `ants-7ylk` | **Superada**: o serviço oficial foi consolidado em **`ants-c2ik`** (9.15); os duplicados foram apagados pelo dono. |
| Token de segurança não configurado | ✅ **Resolvido**: `ANTS_PUBLIC=1` + `ANTS_API_TOKEN` no serviço; `/health` reporta `auth.mode:"token"`, `publico:true` (confirmado pelo dono). Blindado no `render.yaml` (`sync:false`). |
| Cache de respostas invisível | ✅ **Resolvido**: `provenance_seal.js` (web/memória/conhecimento) + "buscar de novo". |
| Sem servidor MCP | ⬜ **Ainda aberto**: não há servidor MCP no repositório (fora do escopo até o dono pedir). |

> Nota: o "Estado do projeto" do PROTOCOLO_COWORK (serviço oficial `ants-yeys`/9.2,
> 534 testes) está **defasado**; hoje é `ants-c2ik`/9.15/712 testes. Recomendo
> atualizar essa seção do protocolo quando o dono autorizar.

## F · O que NÃO foi verificado nesta Fase 0 (Regra 5)

- **Confirmação visual em pixel** dos achados 1–3 (layout a 390px/1280px) — exigiria
  Playwright; aqui a verificação foi **estrutural** (CSS/DOM), não renderizada.
- **A URL pública em produção** não foi acessada deste ambiente (o proxy do sandbox
  bloqueia `onrender.com`); o `/health` de produção foi confirmado pelo dono em
  conversa, não por mim aqui.
- **Busca web real** e **Safari/iOS (WebKit)** não exercidos.
- **RAM/CPU/latência** não medidos (Fase 0 é diagnóstico; medição de desempenho
  entra nas fases que tocam desempenho).
- **T9 (zero emoji em `web/js/`)** não confirmado — o `grep -P` de emoji falhou neste
  ambiente (faixa de code point grande demais para este build do grep); checar com
  ferramenta compatível.
- **T6 (unificação das chamadas de `/health`)** não medido a fundo — vários JS leem
  `/health`; falta confirmar se há redundância por ciclo.
- **Kit de ataque de segurança** não reexecutado nesta rodada.
- (O `PROTOCOLO_COWORK.md` **agora** foi lido — a seção A já traz as 6 regras reais.)
