# Poder de ação: a missão escreve arquivos (9.15)

A colônia deixou de só calcular e pesquisar: agora **age no sistema de arquivos**
dentro de uma missão — com a coleira do dono em dupla trava.

## Como funciona
Quando o objetivo pede escrita ("escreva … no arquivo …"), a Cartógrafa escolhe a
rota **device_action** (identificar → agir → confirmar). No passo **agir**, o
executor extrai `path` + `content` do objetivo e chama a ferramenta gated
`write_file` do ToolRegistry.

## Dupla trava (segurança)
1. **Escopo `write_files`** — sem ele, a ferramenta é recusada com honestidade
   (a colônia SABE escrever, mas não PODE). Concedido só pelo dono em
   `/device/scopes/grant` (owner-gated).
2. **`confirm`** — mesmo com escopo, sem `confirm` a missão faz uma **prévia
   (dry-run)**: diz o que gravaria, sem tocar no disco. Só grava de verdade com
   `confirm:true`.
3. **`path_guard`** — barra caminhos proibidos (raiz do SO, /etc, .ssh…) mesmo
   autorizado, e só permite pastas que o dono liberou em `/device/paths/allow`.

Resultado: um visitante anônimo pode até pedir a escrita, mas sem o escopo (que só
o dono concede) e sem um caminho autorizado, nada é gravado.

## Como usar
- **API:** `POST /mission/run` (ou `/auto`) com
  `{"goal": "escreva \"olá\" no arquivo /pasta/autorizada/nota.txt", "confirm": true}`.
- **Console:** marque **"gravar de verdade"** ao lançar a missão. O desfecho e a
  aba `tools_used` mostram `write_file` (gravado / prévia / recusado) — auditável.

## Prova
`tests/test_mission_write_915.py` (4 testes): parsing do objetivo; recusa honesta
sem escopo; dry-run com escopo e sem confirm; gravação real com escopo + confirm +
caminho autorizado.
