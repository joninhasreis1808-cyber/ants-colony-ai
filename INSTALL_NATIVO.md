# Ant's 8.0 — App nativo: instalação, permissões e revogação

O app nativo (Tauri) empacota a colônia num aplicativo instalável. A casca Rust
inicia o backend Python como **sidecar** numa **porta livre dinâmica**, aguarda
o `/health` e abre a janela; ao fechar o app, o sidecar é encerrado junto.

> **Honestidade:** a versão web (Render) continua funcionando e **apenas
> planeja** ações de dispositivo. **Só no app nativo** a colônia executa
> (ver/agir/verificar), sempre atrás das permissões da Parte B.

## Construir

Pré-requisitos: Python 3.11, Rust/cargo, Node, e as libs de sistema do Tauri
(Linux: `webkit2gtk-4.1`, `libsoup-3.0`, `librsvg2`, `patchelf`).

```bash
bash scripts/build_all.sh        # detecta o SO e constrói
# ou, direto:
bash scripts/build_app.sh        # Linux/macOS  → AppImage/dmg
powershell scripts/build_native.ps1   # (se preferir o fluxo PS no Windows)
```

Saída em `app/src-tauri/target/release/bundle/`.

## Distribuição (realidade honesta)

- **Linux:** AppImage. Gere o checksum e (opcional) assine:
  `sha256sum Ants*.AppImage > Ants.AppImage.sha256`. Distribuição imediata.
- **Windows:** o **SmartScreen** pode avisar ("Windows protegeu o seu PC").
  Clique em **Mais informações → Executar mesmo assim**. Code signing EV é caro
  — documentado como trabalho futuro.
- **macOS:** o **Gatekeeper** bloqueia apps não notarizados — **clique direito →
  Abrir** na primeira vez. Para controlar mouse/teclado, conceda
  **Preferências do Sistema → Privacidade e Segurança → Acessibilidade**.
- **Antivírus:** um app que controla mouse/teclado é frequentemente sinalizado.
  Mitigação: transparência (este repositório é aberto), checksum público e, quando
  possível, assinatura.
- **Linux Wayland:** o controle de input exige o daemon `ydotool` ativo; sem ele
  a capacidade é **declarada indisponível** (não falha em silêncio).

## Permissões (nenhuma concedida por padrão)

Em **Ajustes → Controle do dispositivo**, cada escopo tem um toggle e uma
explicação simples. Os sete escopos independentes:

| Escopo | O que libera |
|--------|--------------|
| `read_files` | ler arquivos (nas pastas autorizadas) |
| `write_files` | criar/mover/apagar arquivos (nas pastas autorizadas) |
| `run_apps` | abrir/fechar aplicativos |
| `control_input` | controlar mouse e teclado |
| `screen_capture` | capturar a tela |
| `system_commands` | rodar comandos de sistema (whitelist) |
| `network` | acesso à rede |

Além dos escopos, a colônia só toca **pastas que você autorizar** (whitelist).
Há uma **blacklist imutável** (raiz do SO, `System32`, `/etc`, `~/.ssh`,
chaveiros) que é recusada **mesmo que você tente autorizar**.

Toda ação passa por: **pânico? → escopo? → pasta/comando permitido? → guarda
imunológica → confirmação (se destrutiva)**. Conteúdo lido da tela/web é sempre
**dado, nunca instrução** (defesa contra prompt injection).

## Como revogar tudo

- **Ajustes → Revogar tudo** remove todos os escopos na hora.
- **Botão de pânico** (canto inferior direito, sempre visível): congela a
  colônia e **revoga os escopos** imediatamente. Clique de novo para retomar.
- Os escopos podem ter validade ("confiar por 1 hora") e expiram sozinhos.
- Toda ação fica na **auditoria** (Ajustes), consultável e exportável (JSONL).

## Memória permanente

No app nativo, tudo (banco, escopos, DNA, tradições, confiança, auditoria) é
gravado no diretório de dados do app (`~/.local/share/ants` no Linux, ou
`ANTS_DATA_DIR`). Fecha e reabre — a memória persiste (fim do `memories_stored:0`).
