# PyInstaller spec — binário standalone do backend do Ant's (sidecar do app).
# Uso: pyinstaller app/ants_backend.spec  (rode a partir da raiz do repo)
# Gera dist/ants_backend  — sobe a API em 127.0.0.1:8765 e serve a interface.
import os

from PyInstaller.utils.hooks import collect_submodules

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

# A interface web (PWA) precisa viajar dentro do binário.
datas = [(os.path.join(ROOT, "web"), "web")]

# uvicorn/fastapi carregam vários módulos por nome (import tardio).
hiddenimports = (
    collect_submodules("uvicorn")
    + collect_submodules("backend")
    + ["anyio", "click", "h11", "websockets", "watchfiles"]
)

block_cipher = None

a = Analysis(
    [os.path.join(ROOT, "backend", "api", "main.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ants_backend",
    debug=False,
    strip=False,
    upx=True,
    console=True,
    onefile=True,
)
