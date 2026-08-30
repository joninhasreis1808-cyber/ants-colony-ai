# binaries/ — o sidecar do backend

Esta pasta recebe o **binário standalone do backend** (o sidecar que o app Tauri
sobe no desktop). Ele **não é versionado** (veja `app/.gitignore`) — é gerado.

## Como o Tauri encontra o sidecar

O `tauri.conf.json` declara `externalBin: ["binaries/ants_backend"]`. Na hora do
build, o Tauri procura o arquivo com o **target triple** anexado ao nome:

```
binaries/ants_backend-x86_64-unknown-linux-gnu        # Linux
binaries/ants_backend-x86_64-pc-windows-msvc.exe      # Windows
binaries/ants_backend-aarch64-apple-darwin            # macOS (Apple Silicon)
```

## Como gerar

Da raiz do repositório:

```bash
bash scripts/build_backend_binary.sh
```

Ele roda o PyInstaller (`app/ants_backend.spec`), descobre seu triple com
`rustc -Vv` e copia `dist/ants_backend` para cá com o nome certo. O
`scripts/build_app.sh` já chama isso antes de `npm run build`.

> Antes de tudo, rode `bash scripts/tauri_doctor.sh` para conferir se a toolchain
> e as libs de sistema estão presentes.
