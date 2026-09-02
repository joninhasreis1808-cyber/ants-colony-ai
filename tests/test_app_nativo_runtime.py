"""O app nativo se declara como corpo (achado compilando e RODANDO o Tauri).

O que aconteceu
---------------
Nesta rodada as bibliotecas de sistema do GTK/WebKit puderam ser instaladas, e
pela primeira vez o app Tauri foi **compilado e executado** de verdade. Rodando,
apareceu um defeito que nenhum teste pegava:

    /local-agent/status  ->  {"runtime": "server", "native": false}

**Dentro do app nativo.** A colônia rodando no corpo acreditava não ter corpo, e
as capacidades de dispositivo seriam recusadas justamente onde deveriam
funcionar.

A causa
-------
Existem duas leituras de runtime, e elas olham variáveis diferentes:

  `backend/action/runtime.py`        lê  ANTS_RUNTIME
  `backend/local_agent/runtime.py`   lê  ANTS_LOCAL_AGENT   <- a que a rota usa

O entrypoint do sidecar definia só a primeira.

Por que marcar no sidecar é seguro
----------------------------------
`backend/api/sidecar.py` só existe dentro do binário do sidecar
(`app/ants_backend.spec`). O deploy web sobe `backend.api.main:app` direto pelo
uvicorn e **nunca importa este módulo** — o servidor não tem como se declarar
nativo por acidente. Este arquivo trava as duas pontas dessa afirmação.
"""
from __future__ import annotations

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_o_sidecar_declara_as_DUAS_variaveis_de_runtime():
    fonte = (RAIZ / "backend/api/sidecar.py").read_text(encoding="utf-8")
    assert 'os.environ["ANTS_RUNTIME"] = "native"' in fonte
    assert 'os.environ["ANTS_LOCAL_AGENT"] = "native"' in fonte, \
        "sem esta, /local-agent/status responde native:false DENTRO do app"


def test_as_duas_leituras_de_runtime_existem_e_olham_variaveis_diferentes():
    """Se um dia forem unificadas, este teste avisa que o sidecar pode simplificar."""
    acao = (RAIZ / "backend/action/runtime.py").read_text(encoding="utf-8")
    corpo = (RAIZ / "backend/local_agent/runtime.py").read_text(encoding="utf-8")
    assert "ANTS_RUNTIME" in acao and "ANTS_LOCAL_AGENT" not in acao
    assert "ANTS_LOCAL_AGENT" in corpo and "ANTS_RUNTIME" not in corpo


def test_a_marca_nativa_liga_o_corpo_de_verdade(monkeypatch):
    import backend.local_agent.runtime as R

    monkeypatch.delenv("ANTS_LOCAL_AGENT", raising=False)
    assert R.is_native() is False and R.runtime_name() == "server"
    monkeypatch.setenv("ANTS_LOCAL_AGENT", "native")
    assert R.is_native() is True and R.runtime_name() == "native"


def test_o_deploy_WEB_nao_importa_o_sidecar():
    """A garantia de que o servidor não vira 'nativo' por acidente.

    Procura o IMPORT, não a palavra: "sidecar" aparece em comentário e docstring
    de forma legítima, e um teste que confunde as duas coisas reprova texto
    honesto.
    """
    import ast

    arvore = ast.parse((RAIZ / "backend/api/main.py").read_text(encoding="utf-8"))
    importados = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            importados.update(a.name for a in no.names)
        elif isinstance(no, ast.ImportFrom):
            importados.add(no.module or "")
            importados.update(f"{no.module}.{a.name}" for a in no.names)
    assert not any("sidecar" in m for m in importados), \
        f"main.py importa o sidecar; o Render se declararia corpo: {importados}"


def test_por_padrao_o_processo_NAO_e_nativo():
    """Sem a marca explícita, é servidor/ponte — honesto e seguro."""
    import backend.local_agent.runtime as R

    anterior = os.environ.pop("ANTS_LOCAL_AGENT", None)
    try:
        assert R.is_native() is False
    finally:
        if anterior is not None:
            os.environ["ANTS_LOCAL_AGENT"] = anterior


def test_o_spec_do_pyinstaller_aponta_para_o_entrypoint_do_sidecar():
    """Se o spec mudar de entrada, a marca nativa deixaria de ser aplicada."""
    spec = (RAIZ / "app/ants_backend.spec").read_text(encoding="utf-8")
    assert '"backend", "api", "sidecar.py"' in spec


def test_o_app_declara_o_sidecar_como_binario_externo():
    import json

    conf = json.loads((RAIZ / "app/src-tauri/tauri.conf.json").read_text(encoding="utf-8"))
    externos = conf.get("bundle", {}).get("externalBin") or []
    assert any("ants_backend" in e for e in externos), \
        "sem externalBin, o app não leva a colônia dentro dele"
