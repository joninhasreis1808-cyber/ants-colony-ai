# CURRENT_STATE.md — Auditoria (FASE 0 do ROTEIRO DE MAESTRIA v9.25)

> **Natureza:** auditoria **sem alteração de código** (PARTE III do roteiro).
> **Base medida:** `main` @ `8939e32` · iteração 9.26 · API 2.0.0.
> **Status:** Fase 0 concluída. **Aguardando autorização do dono para a Fase A.**

---

## 1. Comandos executados (a prova)

```
python -m pytest tests/ -q          → 879 passed, 5 skipped
(cd app/local-agent-core && cargo test) → 24 unit + 4 integração = 28 passed
md5sum web/js/{chat,bots,memory,factory}.js → intactos (abaixo)
```

**MD5 dos 4 JS legados (I5) — conferem com a linha de base:**

| Arquivo | MD5 |
|---|---|
| `web/js/chat.js` | `e1cc6df5be37d6e0502b1063767601bd` |
| `web/js/bots.js` | `ed95b37ebbf0b926daa685dfe09419c1` |
| `web/js/memory.js` | `de5d8499d12efd869baa138497996e10` |
| `web/js/factory.js` | `18b0d5a834fda16f613633a250db053d` |

> Nota: a suíte exige `pip uninstall -y playwright` antes do `pytest` neste
> ambiente — com o playwright instalado, testes de browser falham por caminho de
> binário ausente (ruído de ambiente, não regressão). Rodada também com
> `PYTHONHASHSEED=0` (o seed que já expôs um teste flaky no CI): **879 verdes**.

---

## 2. Inventário real (medido)

| Métrica | Valor |
|---|---|
| Rotas (decorators em `backend/api/routes/`) | **103** |
| Módulos backend (pastas) | **26** |
| Arquivos Python no backend | **278** |
| Arquivos de teste | **83** |
| Testes passando | **879** (+5 skipped) |
| Testes Rust (corpo local) | **28** |
| Arquivos JS no front | **37** |
| Arquivos CSS | **5** |
| Capacidades do corpo nativo | **6** (arquivo r/w, comando, tela, app, entrada) |

---

## 3. Gate de qualidade (PARTE V) — resultado honesto

| Verificação | Resultado |
|---|---|
| `pytest -q` ≥ base (879) | ✅ **879** (igual à base; auditoria não altera código) |
| MD5 dos 4 legados | ✅ intactos |
| `grep Math.random\|SAMPLE` em `web/js/` | ✅ **ZERO mockup real** — os 2 hits são **comentários** que documentam a regra (`resource_center.js:23`, `cognitive_center.js:35`: *"Nunca inventar (sem Math.random)"*) |
| `grep -P` de emoji | ⚠️ **`grep -P` indisponível neste ambiente** (rc=2, faixa de code point grande demais) — verificado por **fallback em Python** |
| Emoji em `web/js/` (fallback Python) | ⚠️ 17 linhas, **todas explicadas** (abaixo) — zero emoji decorativo em código novo |

**Detalhe do achado de emoji (não é regressão):**

| Arquivo | Linhas | Natureza |
|---|---|---|
| `chat.js` (6), `factory.js` (3), `bots.js` (1), `memory.js` (1) | 11 | **Legados imutáveis (I5)** — não podem ser tocados |
| `scripts.js` | 6 | **Padrões de detecção do próprio shim `noEmojiLayer`**, que substitui os pictogramas por ícones SVG em runtime (ex.: `/✅/.test(raw)`) |

Ou seja: os emojis vivem no espelho legado e no código que **os remove**. Nenhum
arquivo novo introduz emoji decorativo.

---

## 4. Provado × Pendente por ambiente

### ✅ Provado com prova executável (aqui / no CI)
- Núcleo cognitivo completo: EventBus, Blackboard, ColonyState, Task Graph com nós
  ricos, Cartógrafa (7 rotas), planejador hierárquico, trilha cognitiva tipada,
  cadeia de fallback em escada, modos FAST/DELIBERATE/CRITICAL.
- Memória + knowledge graph + proveniência + rótulo epistêmico.
- Maturidade de autoevolução **ligada ao laço vivo**: calibração (ECE) alimentada
  por missões reais, canário realimentado por missões (promove/reverte sozinho),
  causal graph (biblioteca).
- Automação nativa soberana: Secret Vault (derivação por dispositivo, auditoria
  sem vazar valor), Motor de Fluxos, Gatilhos (evento + agenda).
- Corpo local: **decisão de segurança das 6 capacidades provada em Rust** (28
  testes); `la_execute` type-checado em isolamento; handshake de segredo efêmero;
  **identidade de dispositivo** (grant de A recusado por B).
- Fio UI→grant→executor (server-side) e camada HTTP de validação
  (`validate_native.sh` → 5/5 contra backend real).
- UI Command API tipada (vocabulário backend cruzado com o `ui_kernel.js`).

### ⚠️ Pendente **por limite de ambiente** (não é falha de execução)
| Item | Por quê | Onde se resolve |
|---|---|---|
| **Build gráfico do Tauri** | faltam `webkit2gtk-4.1`/`gtk-3`/`patchelf` (o `tauri_doctor.sh` confirma) | máquina do dono |
| **Ações físicas reais** (tela/app/entrada) | exigem monitor, app instalado e `xdotool` | máquina do dono |
| **Visual em pixels / performance de animação** | sem browser neste ambiente | máquina do dono |
| **Transporte TLS Render↔Tauri** | camada de *deployment*; o contrato de autenticação (segredo por dispositivo + nonce + TTL) já está pronto e provado | implantação |
| **`grep -P`** para o gate de emoji | build do grep sem suporte à faixa | usar o fallback Python (documentado acima) |

---

## 5. As 6 regras do PROTOCOLO_COWORK — confirmadas

1. **Diagnóstico antes de correção** — nenhuma alteração sem medição que a justifique. ✅
2. **Prova executável, não descrição** — cada mudança traz saída de comando/teste. ✅
3. **A rede de segurança é sagrada** — `pytest -q` verde antes e depois; quem quebra conserta. ✅
4. **Um commit por tarefa** — nada de commit-monstro. ✅
5. **Declarar o que NÃO foi verificado** — presente em todo relatório (§4 e §7). ✅
6. **Interface nunca inventa texto** — estado vazio honesto; "ao vivo" só se for. ✅

## 6. Conformidade com os 9 invariantes (I1–I9)

Nenhum invariante violado nesta auditoria (ela não altera código). Linha de base
confirmada para os que são verificáveis por comando: **I5** (MD5 intactos),
**I8** (zero mockup real no front), **I9** (rito de prova executável), **I4**
(front segue vanilla, sem build step), **I1/I2/I3** (nenhuma dependência paga,
nenhum LLM como cérebro, núcleo offline).

---

## 7. O que NÃO foi verificado (Regra 5)

- **Build gráfico do Tauri e ações físicas** — ver §4 (limite de ambiente).
- **Prova visual (Playwright)** — o playwright precisa ser desinstalado para a
  suíte rodar aqui; screenshots 390/1280 exigidos pela Fase C não foram tirados.
- **RAM/CPU/latência** — não medidos nesta auditoria (entram nas fases que tocam
  desempenho, conforme o roteiro).
- **Deploy em produção** — o `/health` público não foi acessado deste ambiente
  (proxy do sandbox bloqueia `onrender.com`); o auto-deploy dispara por push em
  `main`, mas a confirmação é pelo painel do dono.
- **Benchmark de comportamento** (F3) — ainda não existe; é um incremento do roteiro.

---

## 8. Desvio declarado (transparência)

O roteiro pede a branch `ants-maestria`. A diretriz desta sessão fixa a branch
`claude/new-session-qf8twg` e proíbe outra sem permissão explícita. **Mantive a
branch designada**; o fluxo (branch → PR → `main`, nunca push direto) é idêntico.
Se preferir `ants-maestria`, basta autorizar.

---

## 9. Próximo passo

**Fase 0 concluída.** Conforme a PARTE III do roteiro, **aguardo sua autorização**
para iniciar a **FASE A — Mente Colmeia** (A1 · deliberação com simulação N-vezes;
A2 · causal graph no laço vivo; A3 · memória L0–L6 + Retrieval Planner; A4 · A/B
por rota; A5 · meta-cognição; A6 · consolidação de sono; A7 · conselho + teoria da
mente leve).

Ordem de valor recomendada pelo próprio roteiro: **A3 → A1 → A2 → A5 → A4 → A6/A7**
(A3 e A1 não têm dependências e destravam o resto).
