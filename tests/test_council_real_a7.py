"""A7 · Conselho REAL + teoria da mente leve (roteiro de maestria).

`QueenCouncil` existia, mas era uma casca: `deliberate()` recebia os votos
prontos de fora e os membros nunca avaliavam nada. Aqui provamos que os
conselheiros formam a própria opinião a partir de sinais reais, se abstêm quando
não têm base, modelam a mente uns dos outros — e que o conselho sabe distinguir
convergência de redundância.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.cognitive.council_real import (
    BASES, MEMBERS, OptionEvidence, RealCouncil, get_real_council,
)
from backend.cognitive.queen_council import QueenCouncil

client = TestClient(app)


def _completa(a_melhor: bool = True):
    """Evidência com TODAS as bases apontando na mesma direção."""
    forte = OptionEvidence("A", sources=9, contradictions=0, grounded=True,
                           simulated_score=0.9, causal_support=4, past_success=0.8)
    fraca = OptionEvidence("B", sources=1, contradictions=6, grounded=False,
                           simulated_score=0.1, causal_support=0, past_success=0.1)
    return [forte, fraca] if a_melhor else [fraca, forte]


# --- os conselheiros opinam de verdade -------------------------------------

def test_cada_conselheiro_le_a_propria_base_e_opina_sozinho():
    v = RealCouncil().convene("qual rota?", _completa())
    assert v.winner == "A" and v.reached and v.consensus == "unânime"
    assert {o.member for o in v.opinions} == set(MEMBERS)
    for o in v.opinions:
        assert o.basis == BASES[o.member]
        assert o.choice == "A" and not o.abstained
        assert 0.0 < o.confidence <= 1.0


def test_o_critico_prefere_MENOS_contradicoes_nao_mais():
    """Cada regra tem sentido próprio — o crítico não é só 'mais é melhor'."""
    ev = [OptionEvidence("A", contradictions=8), OptionEvidence("B", contradictions=1)]
    v = RealCouncil().convene("q", ev)
    critico = [o for o in v.opinions if o.member == "critico"][0]
    assert critico.choice == "B"


def test_conselheiro_sem_base_se_abstem_em_vez_de_chutar():
    ev = [OptionEvidence("A", sources=9), OptionEvidence("B", sources=1)]
    v = RealCouncil().convene("q", ev)
    votantes = [o for o in v.opinions if not o.abstained]
    assert [o.member for o in votantes] == ["pesquisador"]
    assert set(v.abstentions) == set(MEMBERS) - {"pesquisador"}
    for o in v.opinions:
        if o.abstained:
            assert "abstenção" in o.reason and o.basis in BASES.values()


def test_base_que_nao_distingue_nada_tambem_gera_abstencao():
    """Ter dado não basta: se todas as opções empatam, não há o que opinar."""
    ev = [OptionEvidence("A", sources=5, contradictions=2),
          OptionEvidence("B", sources=5, contradictions=0)]
    v = RealCouncil().convene("q", ev)
    assert "pesquisador" in v.abstentions       # 5 e 5: empate
    assert "critico" not in v.abstentions       # 2 e 0: distingue


def test_evidencia_vazia_nao_produz_decisao_inventada():
    v = RealCouncil().convene("q", [OptionEvidence("A"), OptionEvidence("B")])
    assert v.winner is None and v.reached is False
    assert v.consensus == "sem quorum"
    assert len(v.abstentions) == len(MEMBERS)
    assert v.independence == 0


# --- teoria da mente leve ---------------------------------------------------

def test_quando_todos_concordam_o_modelo_do_outro_acerta():
    v = RealCouncil().convene("q", _completa())
    assert v.tom_accuracy == 1.0
    assert v.surprises == []


def test_quando_discordam_o_modelo_erra_e_o_conselho_registra_a_surpresa():
    # fontes apontam A; contradições apontam B — sinais genuinamente opostos
    ev = [OptionEvidence("A", sources=9, contradictions=7, grounded=True),
          OptionEvidence("B", sources=2, contradictions=0, grounded=False)]
    v = RealCouncil().convene("q", ev)
    assert v.tom_accuracy is not None and v.tom_accuracy < 1.0
    assert v.surprises, "a divergência tinha que aparecer como surpresa"
    assert any("previu que" in s for s in v.surprises)


def test_a_previsao_e_abstencao_para_quem_nao_tem_dado():
    ev = [OptionEvidence("A", sources=9), OptionEvidence("B", sources=1)]
    v = RealCouncil().convene("q", ev)
    pesq = [o for o in v.opinions if o.member == "pesquisador"][0]
    assert set(pesq.predictions.values()) == {None}, \
        "sem dado na base do outro, o modelo prevê abstenção"
    # ...e ele acertou: os outros realmente se abstiveram.
    for outro, previsto in pesq.predictions.items():
        assert previsto is None and outro in v.abstentions

    # Mas os abstinentes erram sobre ELE: quem não conseguiu decidir modela o
    # colega à própria imagem e prevê que ninguém decidiu. É a teoria da mente
    # falhando de um jeito legível — exatamente o que o conselho existe para
    # medir, em vez de fingir concordância.
    assert v.tom_accuracy is not None and v.tom_accuracy < 1.0
    assert all(f"votaria 'abstenção', mas foi 'A'" in s for s in v.surprises)
    assert len(v.surprises) == len(v.abstentions)


# --- convergência não é redundância -----------------------------------------

def test_decisao_apoiada_em_uma_base_so_e_marcada_como_fragil():
    ev = [OptionEvidence("A", sources=9), OptionEvidence("B", sources=1)]
    v = RealCouncil().convene("q", ev)
    assert v.winner == "A" and v.reached          # ganhou...
    assert v.independence == 1
    assert v.fragile is True                      # ...mas com uma base só
    assert "uma base só" in v.fragile_reason


def test_convergencia_de_bases_independentes_nao_e_fragil():
    v = RealCouncil().convene("q", _completa())
    assert v.independence == len(MEMBERS)
    assert v.fragile is False and v.fragile_reason == ""


def test_independencia_conta_so_as_bases_que_apoiam_o_vencedor():
    # sources, causal_support e grounded apontam A; contradictions aponta B.
    # 3 de 4 votos = 75%, acima do quórum de 70%.
    ev = [OptionEvidence("A", sources=9, causal_support=5, grounded=True,
                         contradictions=8),
          OptionEvidence("B", sources=1, causal_support=0, grounded=False,
                         contradictions=0)]
    v = RealCouncil().convene("q", ev)
    assert v.winner == "A" and v.consensus == "maioria"
    assert v.independence == 3, "o crítico votou em B; não sustenta o vencedor"
    assert v.fragile is False


def test_maioria_abaixo_do_quorum_nao_decide():
    """2 de 3 é 67%: o conselho prefere não decidir a decidir por pouco."""
    ev = [OptionEvidence("A", sources=9, causal_support=5, contradictions=8),
          OptionEvidence("B", sources=1, causal_support=0, contradictions=0)]
    v = RealCouncil().convene("q", ev)
    assert v.winner is None and v.reached is False
    assert v.consensus == "sem quorum"


# --- determinismo e integração ---------------------------------------------

def test_o_conselho_e_deterministico():
    a = RealCouncil().convene("q", _completa()).to_dict()
    b = RealCouncil().convene("q", _completa()).to_dict()
    assert a == b


def test_a_ordem_das_opcoes_nao_muda_o_veredito():
    a = RealCouncil().convene("q", _completa(True))
    b = RealCouncil().convene("q", _completa(False))
    assert a.winner == b.winner == "A"
    assert a.independence == b.independence


def test_a_casca_antiga_continua_funcionando_e_ganha_o_caminho_real():
    qc = QueenCouncil()
    pid = qc.convene("qual banco?", ["postgres", "sqlite"])
    qc.deliberate(pid, {"planner": "postgres", "critic": "postgres",
                        "verifier": "postgres", "researcher": "postgres",
                        "simulator": "postgres"})
    assert qc.decide(pid, "qual banco?").winner == "postgres"

    real = QueenCouncil.convene_real("qual banco?", _completa())
    assert real["winner"] == "A" and real["independence"] == len(MEMBERS)


# --- observabilidade --------------------------------------------------------

def test_endpoint_declara_quem_le_o_que():
    body = client.get("/council").json()
    assert body["members"] == list(MEMBERS)
    assert body["bases"]["critico"] == "contradictions"


def test_endpoint_reune_o_conselho_sobre_evidencia_real():
    r = client.post("/council", json={
        "question": "qual rota?",
        "evidence": [{"option": "A", "sources": 9, "contradictions": 0},
                     {"option": "B", "sources": 1, "contradictions": 5}]})
    assert r.status_code == 200
    body = r.json()
    assert body["winner"] == "A" and body["independence"] == 2
    assert body["fragile"] is False
    assert len(body["abstentions"]) == len(MEMBERS) - 2


def test_endpoint_nao_inventa_veredito_sem_evidencia():
    r = client.post("/council", json={"question": "q",
                                      "evidence": [{"option": "A"},
                                                   {"option": "B"}]})
    body = r.json()
    assert body["winner"] is None and body["consensus"] == "sem quorum"
    assert body["theory_of_mind"]["accuracy"] == 1.0   # todos previram abstenção


def test_singleton_do_conselho():
    assert get_real_council() is get_real_council()
