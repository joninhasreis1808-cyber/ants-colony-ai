"""`backend/api/routes/hive.py::MEMORY` ligada a ANTS_DB, não hardcoded.

Achado durante o PR #99 (isolamento entre testes) e declarado sem corrigir
na hora: `MEMORY = SharedMemory("ants.db")` ignorava a variável ANTS_DB por
completo — gravava sempre no arquivo literal do cwd do repositório,
independente de qualquer configuração de ambiente (deploy, sidecar nativo,
suíte de testes). Mesma classe de risco do #92: a peça (SharedMemory) sempre
aceitou um `db_path` configurável; só o ponto de construção real nunca
repassava a variável de ambiente.

`MEMORY` é singleton de MÓDULO, ligado na primeira importação — um teste
dentro do mesmo processo não prova a fiação (o módulo já foi importado por
outro teste antes, com o `ANTS_DB` que já estava valendo então). Por isso o
teste de verdade roda num SUBPROCESSO novo, mesmo padrão já usado por
`test_app_nativo_runtime.py` para o mesmo tipo de problema.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_hive_py_nao_hardcoda_mais_ants_db():
    fonte = (RAIZ / "backend/api/routes/hive.py").read_text(encoding="utf-8")
    assert 'SharedMemory("ants.db")' not in fonte, (
        "MEMORY voltou a ignorar ANTS_DB — grava sempre no arquivo literal "
        "do cwd, independente do ambiente"
    )
    assert 'os.environ.get("ANTS_DB"' in fonte


def test_memory_usa_o_arquivo_de_ants_db_num_processo_novo(tmp_path):
    alvo = tmp_path / "colonia_de_teste.db"
    env = dict(os.environ)
    env["ANTS_DB"] = str(alvo)
    script = (
        "import backend.api.routes.hive as h\n"
        "assert h.MEMORY is not None\n"
        "print('ok')\n"
    )
    r = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(RAIZ), env=env,
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, f"stdout={r.stdout} stderr={r.stderr}"
    assert "ok" in r.stdout
    assert alvo.exists(), (
        "o arquivo apontado por ANTS_DB não foi criado — MEMORY ainda não "
        "está ouvindo a variável de ambiente de verdade"
    )
