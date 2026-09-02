"""D · Movimento que informa (FASE D · roteiro de maestria).

Auditoria antes de escrever qualquer animação, medida no navegador:
`prefers-reduced-motion` **já era respeitado** — 15 elementos animando e 120
transicionando caem para **0 e 0** quando a pessoa pede menos movimento. Não
havia defeito de acessibilidade a corrigir.

Então a FASE D não podia ser enfeite. As duas coisas que este incremento faz:

  1. **O orçamento de movimento acompanha a incerteza.** Uma resposta
     `contestado` ou `sem_base` chega com ênfase; uma `verificado` chega quieta.
     O movimento é gasto onde a colônia está MENOS segura — isso é sinal.
  2. **O painel destaca só o que mudou.** Depois de cada missão os números do
     painel de consciência mudavam em SILÊNCIO: o aprendizado acontecia e
     ninguém via acontecer.

Duas regras que este arquivo trava:
  • movimento **nunca é o único canal** — a palavra e a cor carregam a
    informação inteira, e com `reduce` tudo fica parado sem perder nada;
  • **nada pisca sem ter mudado** — piscar à toa seria mentira visual.
"""
from __future__ import annotations

import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[2] / "web"
CARD_JS = (WEB / "js/epistemic_card.js").read_text(encoding="utf-8")
CARD_CSS = (WEB / "css/epistemic_card.css").read_text(encoding="utf-8")
AWARE_JS = (WEB / "js/colony_awareness.js").read_text(encoding="utf-8")
AWARE_CSS = (WEB / "css/colony_awareness.css").read_text(encoding="utf-8")


# ===  1 · o movimento acompanha a incerteza  =================================

def test_toda_manchete_do_backend_tem_severidade_declarada():
    from backend.cognition.epistemic_label import HEADLINES
    bloco = CARD_JS[CARD_JS.index("var HEAD = {"):CARD_JS.index("var EIXOS")]
    for h in HEADLINES:
        assert re.search(rf"{h}:\s*\{{[^}}]*sev:\s*\"(baixa|media|alta)\"", bloco), \
            f"a manchete '{h}' nao declara orcamento de movimento"


def test_so_as_manchetes_de_ALTA_incerteza_recebem_enfase():
    bloco = CARD_JS[CARD_JS.index("var HEAD = {"):CARD_JS.index("var EIXOS")]
    altas = set(re.findall(r"(\w+):\s*\{[^}]*sev:\s*\"alta\"", bloco))
    assert altas == {"contestado", "sem_base"}, \
        "a ênfase tem que ir para onde a colônia está menos segura"


def test_a_severidade_vai_para_o_DOM_como_atributo():
    assert 'card.setAttribute("data-sev"' in CARD_JS


def test_o_css_so_anima_com_enfase_o_data_sev_alta():
    assert '.epi-card[data-sev="alta"]' in CARD_CSS
    assert "epi-atencao" in CARD_CSS
    # a entrada calma vale para todos; a atenção, só para alta
    entrada = re.search(r"\.epi-card\[data-sev\]\s*\{([^}]*)\}", CARD_CSS)
    assert entrada and "epi-atencao" not in entrada.group(1)


def test_manchete_desconhecida_cai_num_padrao_sem_enfase():
    """Se o backend inventar uma manchete nova, o front não pode dar ênfase
    sem saber o que ela significa."""
    assert 'cls: "epi-mid", sev: "media"' in CARD_JS


# ===  2 · o painel destaca so o que mudou  ==================================

def test_o_painel_compara_com_a_pintura_anterior():
    assert "var anterior = {}" in AWARE_JS
    assert "anterior[sec] = novo" in AWARE_JS


def test_a_primeira_pintura_nunca_pisca():
    """Não havia com o que comparar — piscar ali seria ruído."""
    assert "if (antes !== undefined && antes !== novo)" in AWARE_JS


def test_a_classe_de_destaque_so_entra_em_linha_ausente_do_anterior():
    assert 'linhasAntes.indexOf(atual) === -1' in AWARE_JS
    assert 'classList.add("ca-mudou")' in AWARE_JS


def test_o_destaque_some_sozinho_e_a_informacao_fica():
    m = re.search(r"#ants-awareness \.ca-row\.ca-mudou\s*\{([^}]*)\}", AWARE_CSS)
    assert m, "falta a regra do destaque"
    assert "animation:" in m.group(1)
    assert "both" in m.group(1)      # termina no estado final, sem piscar de volta
    # o destaque é só fundo: não mexe no texto nem esconde nada
    assert "display" not in m.group(1) and "visibility" not in m.group(1)


# ===  3 · movimento nunca e o unico canal  ==================================

def test_os_dois_arquivos_desligam_o_movimento_sob_reduce():
    for css, alvo in ((CARD_CSS, ".epi-card[data-sev]"),
                      (AWARE_CSS, "#ants-awareness .ca-row.ca-mudou")):
        bloco = re.search(r"@media \(prefers-reduced-motion: reduce\)\s*\{(.*?)\n\}",
                          css, re.S)
        assert bloco, "falta o bloco de reduced-motion"
        assert alvo in bloco.group(1)
        assert "animation: none !important" in bloco.group(1)


def test_a_informacao_nao_depende_de_movimento():
    """A palavra e a cor já dizem tudo — o movimento é reforço redundante."""
    # a manchete continua sendo texto escapado no DOM
    assert "esc(meta.rot)" in CARD_JS
    # e a cor da severidade vem da classe, não da animação
    for cls in ("epi-ok", "epi-mid", "epi-bad"):
        assert f".epi-card .{cls}" in CARD_CSS


def test_nenhuma_animacao_infinita():
    """Movimento perpétuo é distração, e a WCAG desaconselha acima de 5s."""
    for css in (CARD_CSS, AWARE_CSS):
        assert "infinite" not in css


def test_as_animacoes_sao_curtas():
    """Cuidado com o regex: `.22s` (sem zero à esquerda) é 0.22, não 22."""
    duracoes = [float(d) for d in re.findall(r"animation:[^;]*?(\d*\.?\d+)s",
                                             CARD_CSS + AWARE_CSS)]
    assert duracoes, "esperava encontrar durações declaradas"
    assert all(0 < d <= 2.0 for d in duracoes), f"animação longa demais: {duracoes}"
    assert max(duracoes) < 1.7, f"a mais longa deveria ser o destaque: {duracoes}"
