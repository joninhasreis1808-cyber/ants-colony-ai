"""Coerência da configuração do app Tauri (9.20 · Tauri-prep).

Não compila o Tauri aqui (faltam libs GTK/WebKit), mas GARANTE que a configuração
não divirja em silêncio — o tipo de erro que só aparece na hora do build na
máquina do dono. Cruza tauri.conf.json × capabilities × ícones × scripts × front.
Puro stdlib; roda no CI a cada mudança.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
TAURI = APP / "src-tauri"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def conf() -> dict:
    return _load(TAURI / "tauri.conf.json")


@pytest.fixture(scope="module")
def caps() -> dict:
    return _load(TAURI / "capabilities" / "default.json")


def test_conf_tem_campos_essenciais(conf):
    for key in ("productName", "version", "identifier"):
        assert conf.get(key), f"tauri.conf.json sem '{key}'"
    assert conf["bundle"]["externalBin"], "sem externalBin (sidecar)"


def test_sidecar_bate_entre_conf_e_capabilities(conf, caps):
    # O nome do sidecar no bundle precisa ser o MESMO autorizado no shell:execute.
    ext = conf["bundle"]["externalBin"]
    assert "binaries/ants_backend" in ext
    shell = [p for p in caps["permissions"]
             if isinstance(p, dict) and p.get("identifier") == "shell:allow-execute"]
    assert shell, "capabilities sem shell:allow-execute para o sidecar"
    names = {a.get("name") for a in shell[0]["allow"]}
    assert "binaries/ants_backend" in names
    assert all(a.get("sidecar") for a in shell[0]["allow"]), "sidecar:true faltando"


def test_todos_os_icones_existem(conf):
    for rel in conf["bundle"]["icon"]:
        assert (TAURI / rel).exists(), f"ícone ausente: {rel}"


def test_frontend_aponta_para_a_web_real(conf):
    front = (TAURI / conf["build"]["frontendDist"]).resolve()
    assert front == (ROOT / "web").resolve(), "frontendDist não aponta para /web"
    assert (front / "index.html").exists(), "web/index.html não existe"
    # a ponte nativa precisa estar carregada na interface
    assert "native_bridge.js" in (front / "index.html").read_text(encoding="utf-8")


def test_capabilities_referencia_janela_main(caps):
    assert "main" in caps.get("windows", []), "capability não cobre a janela 'main'"


def test_build_script_gera_o_nome_que_o_tauri_espera():
    # O script do sidecar deve copiar para binaries/ants_backend-<triple>,
    # cujo basename ('ants_backend') casa com o externalBin.
    script = (ROOT / "scripts" / "build_backend_binary.sh").read_text(encoding="utf-8")
    assert "app/src-tauri/binaries/ants_backend-${TRIPLE}" in script
    assert re.search(r"rustc -Vv", script), "script não descobre o target triple"


def test_package_json_tem_scripts_de_build():
    pkg = _load(APP / "package.json")
    for s in ("dev", "build", "tauri"):
        assert s in pkg["scripts"], f"package.json sem script '{s}'"
