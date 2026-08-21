# Ant's 9.8 — FASE D: Ferramentas reais (as "mãos" da colônia, com trava)

A FASE A (9.6) deu à colônia mãos de **leitura** (`list_dir`, `read_file`), sempre
atrás do `path_guard`. A **FASE D** dá as mãos que **modificam e calculam** — o que
falta para agir como um Manus — mas **nunca como cheque em branco**: escrever e
apagar são irreversíveis, então cada ferramenta carrega sua própria trava.

## A regra de ouro: capacidade ≠ permissão, e dry-run antes de agir

Toda ferramenta passa pelo **ToolRegistry**, que valida **capacidade** ("sei
fazer") **e permissão** ("posso fazer AGORA", o escopo do device) **antes** de
executar. Sem o escopo concedido, a ferramenta é **recusada com honestidade** —
mesmo sabendo executá-la. Sobre isso, as ferramentas destrutivas têm uma segunda
trava: **dry-run por padrão**.

| Ferramenta | Capacidade | Escopo exigido | Risco | Trava |
|---|---|---|---|---|
| `write_file` | `filesystem.write` | `write_files` | médio | dry-run → `confirm:true` grava |
| `make_dir` | `filesystem.write` | `write_files` | médio | dry-run → `confirm:true` cria |
| `delete_path` | `filesystem.delete` | `write_files` | **alto** | dry-run; **nunca apaga pasta não vazia** |
| `compute` | `compute.exact` | *(nenhum — é puro)* | baixo | — |

- **Dry-run**: sem `confirm:true`, a ferramenta apenas **diz o que faria**
  (`would_write`, `would_delete`…) e não toca no disco. É o "olhe antes de apagar".
- **path_guard**: toda escrita/leitura só ocorre **dentro das pastas autorizadas**
  pelo dono; a árvore do sistema (raiz do SO, credenciais, `.ssh`, `.env`…) é
  **blacklist dura**, recusada mesmo com autorização.
- **delete_path** nunca apaga uma árvore inteira: pasta com conteúdo é recusada,
  **mesmo com `confirm:true`**.
- **compute** é puro (SymPy, sem `eval`) e não toca no dispositivo — por isso **não
  exige escopo**, só a capacidade.

## Como usar

Já pelas rotas da FASE A:

- `GET /tools` — catálogo honesto: cada ferramenta + capacidade + escopo + risco +
  **se está disponível agora**.
- `POST /tools/run` `{ "name": "...", "args": {...} }` — valida e executa (ou
  recusa). Protegido por `require_owner`.

`GET /health` → `intelligence.tools` lista as mãos e o risco de cada uma.

## Por que isso importa para a autonomia (FASE E)

Com um catálogo uniforme de ferramentas gated, o **executor de missões** (FASE B) e
o **laço autônomo** (FASE E) poderão **agir** — escrever um relatório, organizar
uma pasta, calcular — chamando ferramentas do mesmo jeito, sempre com a permissão
do dono e a segurança do dry-run. A colônia ganha mãos sem perder a coleira.

## Testes

`tests/test_tools/test_tools_fase_d_98.py` (9): sem escopo → recusa; dry-run não
toca no disco; `confirm` grava/apaga de verdade; pasta não vazia recusada; caminho
fora das pastas bloqueado; `compute` sem escopo. **Suíte total: 643 verdes.**
MD5 dos 4 JS legados **intacto**.
