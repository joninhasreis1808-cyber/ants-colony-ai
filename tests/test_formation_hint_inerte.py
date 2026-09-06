"""O viés de desempenho não muda a formação — medido, não suposto.

`self_performance.py` dizia que a Rainha passava a recrutar "em vez de
sempre na mesma ordem fixa". A ordem é exatamente fixa. Este teste prende
os dois motivos independentes, para que a alegação não volte ao código sem
a medição voltar junto.

Não é um defeito a consertar às pressas: é o mesmo cenário que
`test_contract_net_recruiter_b04.py` já declara para o critério de custo —
motor pronto, elenco ainda sem duas castas disputando o mesmo estágio. O
que era defeito é a frase que afirmava um efeito inexistente.

Se um dia o elenco ganhar disputa de estágio, ou o crédito passar a ser
por bot, estes testes FALHAM — e é assim que se descobre que o motor
finalmente vale alguma coisa.
"""
from __future__ import annotations

import pytest

from backend.cognitive.self_performance import SelfPerformance
from backend.hivemind.factory import build_hive
from backend.hivemind.recruiter import _STAGE_ORDER, Recruiter


@pytest.fixture(scope="module")
def elenco():
    hive, _ = build_hive()
    return hive.recruiter._roster


def _rank(bot) -> int:
    """A primeira chave de `Recruiter._order`, reproduzida aqui."""
    melhor = len(_STAGE_ORDER)
    for i, estagio in enumerate(_STAGE_ORDER):
        prefixo = estagio.split("_")[0]
        if estagio in bot.skills or any(s.startswith(prefixo) for s in bot.skills):
            melhor = min(melhor, i)
    return melhor


def test_motivo_1_o_credito_e_por_missao_e_nao_por_bot():
    """`record()` carimba o desfecho da MISSÃO em toda a formação, então
    castas que correm juntas empatam por construção — o desempate por
    desempenho não pode desempatar nada."""
    sp = SelfPerformance()
    formacao = ["navigator", "extractor", "interpreter", "decider", "learner"]
    for i in range(6):
        sp.record(signature="pesquisa", route="seed_knowledge",
                  castes=formacao, success=(i != 3), duration=1.0)

    hint = sp.formation_hint()
    assert set(hint) == set(formacao)
    assert len(set(hint.values())) == 1, (
        f"as castas deixaram de empatar: {hint} — se o crédito passou a ser "
        f"por bot, o viés agora PODE desempatar e o cabeçalho de "
        f"self_performance.py precisa ser reescrito")
    assert hint["navigator"] == pytest.approx(5 / 6, abs=1e-4)


def test_motivo_2_nenhuma_casta_divide_estagio_com_outra(elenco):
    """O viés só desempata DENTRO de um estágio. No elenco de hoje cada
    estágio tem um ocupante só, então `rank()` já decide tudo e a chave do
    viés nunca chega a ser comparada."""
    por_estagio: dict[int, list[str]] = {}
    for bot in elenco:
        por_estagio.setdefault(_rank(bot), []).append(bot.name)

    disputas = {r: nomes for r, nomes in por_estagio.items() if len(nomes) > 1}
    assert not disputas, (
        f"o elenco ganhou disputa de estágio: {disputas} — o desempate por "
        f"desempenho passou a ser alcançável e precisa ser medido de verdade")
    assert len(por_estagio) == len(elenco), "cada casta ocupa um estágio só"


def test_a_formacao_e_a_mesma_com_e_sem_historico(elenco, monkeypatch):
    """A prova direta, sobre o `Recruiter` real: encher a meta-cognição de
    histórico enviesado não move um bot de lugar."""
    needs = ["navigate", "extract_text", "interpret_text", "decide", "learn"]
    rec = Recruiter(elenco)

    monkeypatch.setattr(Recruiter, "_formation_hint", staticmethod(lambda: {}))
    sem_historico = [b.name for b in rec.recruit(needs)]

    enviesado = {b.name: (0.9 if i % 2 else 0.1)
                 for i, b in enumerate(elenco)}
    monkeypatch.setattr(Recruiter, "_formation_hint",
                        staticmethod(lambda: enviesado))
    com_historico = [b.name for b in rec.recruit(needs)]

    assert sem_historico == com_historico, (
        "o viés passou a mover a formação — o que este teste documenta como "
        "impossível deixou de ser; refaça a medição e reescreva os docstrings")


def test_o_motor_funciona_quando_existe_disputa_de_verdade(monkeypatch):
    """A guarda do teste anterior: ele só prova algo se o viés FOSSE capaz
    de reordenar. Aqui, com duas castas sintéticas no mesmo estágio, ele
    reordena — logo o empate lá em cima vem do elenco, não de um viés
    quebrado nem de uma lista vazia.

    `monkeypatch` e não atribuição na classe: trocar `_formation_hint` na
    mão e desfazer com `del` APAGA o método original e vaza para toda a
    suíte (9 testes caíram assim ao escrever isto)."""
    class _Dublê:
        def __init__(self, nome: str) -> None:
            self.name, self.skills = nome, ["decide"]

    rec = Recruiter([_Dublê("A"), _Dublê("B")])

    monkeypatch.setattr(Recruiter, "_formation_hint", staticmethod(lambda: {}))
    assert [b.name for b in rec.recruit(["decide"])] == ["A", "B"]
    monkeypatch.setattr(Recruiter, "_formation_hint",
                        staticmethod(lambda: {"B": 0.9, "A": 0.1}))
    assert [b.name for b in rec.recruit(["decide"])] == ["B", "A"], (
        "o viés não reordena nem com disputa real — aí o teste do elenco "
        "acima estaria passando por vacuidade")


def test_o_elenco_real_nao_recruta_vazio(elenco):
    """A outra vacuidade possível: comparar duas listas vazias."""
    needs = ["navigate", "extract_text", "interpret_text", "decide", "learn"]
    assert len(Recruiter(elenco).recruit(needs)) == 5
