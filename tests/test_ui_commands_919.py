"""UI Command API tipada (9.19 · FASE 5b): a Mente comanda a UI, não edita HTML.

Prova que só o conjunto FECHADO de ações passa, que os parâmetros são validados
por ação, e que o vocabulário do backend casa com o do ui_kernel.js (fonte única).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from backend.interface import ui_commands as ui


def test_build_valida_e_monta_comando():
    cmd = ui.update_progress(42)
    assert cmd == {"action": "update_progress", "progress": 42}


def test_acao_desconhecida_recusada():
    with pytest.raises(ui.UICommandError):
        ui.build("exec_html", html="<script>")


def test_progress_fora_da_faixa_recusado():
    for bad in (-1, 101, "x", None):
        ok, _ = ui.validate({"action": "update_progress", "progress": bad})
        assert ok is False


def test_estado_invalido_recusado():
    with pytest.raises(ui.UICommandError):
        ui.set_state("voando")
    assert ui.set_state("exploring")["target"] == "exploring"


def test_secao_invalida_recusada():
    with pytest.raises(ui.UICommandError):
        ui.open_section("cozinha")
    assert ui.open_section("missions")["target"] == "missions"


def test_toast_e_timeline_exigem_texto():
    with pytest.raises(ui.UICommandError):
        ui.toast("   ")
    with pytest.raises(ui.UICommandError):
        ui.append_timeline("")


def test_vocabulario_bate_com_o_kernel_js():
    # Fonte única: as ações do backend devem existir no ui_kernel.js.
    kernel = Path("web/js/ui_kernel.js").read_text(encoding="utf-8")
    # Extrai as chaves do mapa ACTIONS = { nome: function ... }
    bloco = kernel.split("var ACTIONS", 1)[1]
    nomes = set(re.findall(r"\n\s{4}(\w+):\s*function", bloco))
    assert ui.ACTIONS <= nomes, f"backend tem ações fora do kernel: {ui.ACTIONS - nomes}"
