"""`web/js/live_dashboard.js` não inventa mais números por casta (achado
declarado sem corrigir ao investigar o item 6, corrigido agora).

O módulo desenhava um array `COLONY` fixo no código — "3/5 ativas",
"5/6 ativas" etc. — números que nunca vieram de lugar nenhum, violando a
mesma regra já documentada em ESTADO_ATUAL.md para o resto do app:
qualquer falha de endpoint mostra "—", nunca um número falso.

Ao investigar, dois problemas a mais apareceram (confirmados ao vivo via
Playwright antes da correção, não só por leitura de código):
1. `index.html` tinha uma SEGUNDA cópia dos números fake, hardcoded
   diretamente no HTML da "Hierarquia" — o `#org-hierarchy` que o JS
   escrevia estava `display:none`, morto; o que o usuário via de fato
   era este HTML estático, nunca tocado pelo JS.
2. As classes `.colony-node`/`.colony-link` que o SVG gerado usa não
   tinham NENHUMA regra de CSS — os nós renderizavam pretos (fill padrão
   do navegador) e as linhas eram invisíveis (stroke:none padrão);
   confirmado com `getComputedStyle` num Chromium real antes do fix.
"""
from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_live_dashboard_nao_hardcoda_mais_contagem_por_casta():
    fonte = (RAIZ / "web/js/live_dashboard.js").read_text(encoding="utf-8")
    assert '"queen",    label: "Rainha"' not in fonte
    assert "active: 3, total: 5" not in fonte
    assert "active: 5, total: 6" not in fonte
    assert '"/hive/formations"' in fonte, (
        "o módulo precisa buscar a contagem real em /hive/formations — "
        "mesma fonte que o painel de formações da Cognição usa"
    )


def test_live_dashboard_declara_nao_sei_quando_a_rede_falha():
    fonte = (RAIZ / "web/js/live_dashboard.js").read_text(encoding="utf-8")
    assert "return null" in fonte
    assert "sem dados" in fonte, (
        "sem resposta da API, a interface precisa dizer que não sabe — "
        "nunca mostrar um zero como se fosse uma contagem confirmada"
    )


def test_index_html_nao_tem_mais_a_hierarquia_fixa_no_marcado():
    fonte = (RAIZ / "web/index.html").read_text(encoding="utf-8")
    assert '<b>3</b>/5' not in fonte
    assert '<b>5</b>/6' not in fonte
    assert 'Jardineiras' not in fonte, (
        "rótulo da casta antiga (legado) não corresponde a nenhuma casta-base "
        "real de backend/hivemind/castes_base.py"
    )
    assert 'id="colony-hierarchy"' in fonte, (
        "o HTML precisa de um contêiner real e visível para live_dashboard.js "
        "preencher — o antigo #org-hierarchy é display:none, morto"
    )


def test_css_define_regras_para_os_nos_e_conexoes_da_rede():
    fonte = (RAIZ / "web/css/design_system.css").read_text(encoding="utf-8")
    assert ".colony-node{" in fonte or ".colony-node {" in fonte, (
        "sem esta regra os nós do SVG renderizam pretos (fill padrão do "
        "navegador) — confirmado ao vivo antes do fix"
    )
    assert ".colony-link{" in fonte or ".colony-link {" in fonte, (
        "sem esta regra as linhas do SVG são invisíveis (stroke:none padrão)"
    )


def test_live_panels_aponta_para_o_conteiner_real_agora():
    fonte = (RAIZ / "web/js/live_panels.js").read_text(encoding="utf-8")
    assert 'AntDashboard.mount("org-hierarchy"' not in fonte
    assert 'AntDashboard.mount("colony-hierarchy", "colony-network")' in fonte
