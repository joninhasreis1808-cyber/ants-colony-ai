# PyInstaller spec — binário standalone do backend do Ant's (sidecar do app).
# Uso: pyinstaller app/ants_backend.spec  (de qualquer diretório)
# Gera dist/ants_backend  — sobe a API em 127.0.0.1:8765 e serve a interface.
import os
import sys

from PyInstaller.utils.hooks import collect_submodules

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
# `collect_submodules("backend")` roda AQUI, antes do Analysis(pathex=[ROOT]),
# e precisa que `backend` já seja importável neste ponto. O executável
# `pyinstaller` é um script — seu sys.path[0] é o diretório DELE
# (/usr/local/bin, tipicamente), nunca o cwd de quem o chamou, ao contrário
# de `python3 -c`. Sem esta linha, a coleta abaixo silenciosamente devolve
# quase nada (achado ao empacotar: 15M em vez de ~111M, sidecar quebrado com
# "ModuleNotFoundError: No module named 'backend.api'" — nenhum erro no
# build, só um binário pequeno e mudo).
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

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
    # Entrypoint 8.0: o sidecar marca runtime nativo, aponta a persistência
    # para o diretório de dados do app e usa a porta dinâmica (ANTS_PORT).
    [os.path.join(ROOT, "backend", "api", "sidecar.py")],
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
