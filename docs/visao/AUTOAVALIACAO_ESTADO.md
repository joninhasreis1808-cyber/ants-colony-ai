# AUTOAVALIAÇÃO DO ESTADO — Ant's (Fase 0 do Roteiro)

> **Natureza:** diagnóstico honesto e verificado, **sem nenhuma implementação**
> (Fase 0 do `ROTEIRO_ants_AUTOAVALIACAO_E_EVOLUCAO.md`). Base medida: `main`
> commit `01e3603`. **Aguardando autorização do dono antes da Fase 1.**

## Aviso de honestidade (antes de tudo)

- O `PROTOCOLO_COWORK.md` **não estava entre os anexos** desta rodada. As 6 regras
  abaixo foram **reconstruídas** a partir dos documentos fornecidos (são
  consistentes entre si); marque como *inferência a confirmar* até o protocolo real
  ser fornecido.
- O dossiê `RELATORIO_PARA_CHATGPT.md` é da base **9.3 / commit `f94edf8` / 534
  testes**. O projeto avançou **muito** desde então (hoje 9.15 / `01e3603` / **712
  testes**). Por isso a maioria dos 9 achados **já foi resolvida** — confirmado por
  medição, não presunção.

## A · As 6 regras do PROTOCOLO_COWORK (reconstruídas — a confirmar)

1. **Não reescrever.** Evolução incremental e reversível; incompatibilidade → camada
   de compatibilidade, nunca demolição.
2. **Testes só sobem.** `pytest -q` antes/depois; quebrou → PARAR, diagnosticar,
   corrigir; nunca mascarar ou editar teste só para passar.
3. **Intocáveis.** MD5 dos 4 JS legados e IDs legados no DOM preservados.
4. **UI nunca inventa estado.** Todo dado/animação/progresso vem do backend real; a
   IA atualiza a UI só por eventos/comandos tipados (UI Kernel), nunca HTML cru.
5. **Coleira.** Sem LLM externo como cérebro; sem auto-modificação de código em
   produção; device só via Local Agent nativo autenticado (cérebro remoto × corpo
   local).
6. **Limites.** Custo zero, offline-first, sem build step, sem framework novo;
   segurança primeiro em qualquer ação de dispositivo; trabalho em branch → PR.

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

## F · O que NÃO foi verificado nesta Fase 0 (Regra 5)

- **Confirmação visual em pixel** dos achados 1–3 (layout a 390px/1280px) — exigiria
  Playwright; aqui a verificação foi **estrutural** (CSS/DOM), não renderizada.
- **A URL pública em produção** não foi acessada deste ambiente (o proxy do sandbox
  bloqueia `onrender.com`); o `/health` de produção foi confirmado pelo dono em
  conversa, não por mim aqui.
- **Busca web real** e **Safari/iOS (WebKit)** não exercidos.
- **RAM/CPU/latência** não medidos (Fase 0 é diagnóstico; medição de desempenho
  entra nas fases que tocam desempenho).
- **`PROTOCOLO_COWORK.md`** não foi lido (não anexado) — as 6 regras acima são
  reconstrução.
- **Kit de ataque de segurança** não reexecutado nesta rodada.
