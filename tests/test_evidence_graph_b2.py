"""Grafo de evidência com independência de fonte (item 3 do Repertório da
Colmeia, estende B2 · cross_check).

O B2 original comparava cada rota contra UMA "principal" — um leque, não um
grafo. Isso deixava dois pontos cegos que este teste prova corrigidos:

  1. um conflito numérico entre a SEGUNDA e a TERCEIRA rota nunca aparecia se
     nenhuma das duas fosse a principal;
  2. duas rotas que só concordam INDIRETAMENTE (A concorda com B, B concorda
     com C, mas A e C nunca comparadas por texto de forma favorável) nunca
     contavam como confirmação — mesmo sendo, de fato, evidência convergente.

Os detectores continuam os mesmos dois sinais declarados (número e léxico),
determinísticos, sem modelo de linguagem — só o grafo de comparação mudou de
leque para completo.
"""
from __future__ import annotations

from backend.cognition.cross_check import Claim, cross_check


def _c(fonte: str, texto: str, conf: float = 0.6) -> Claim:
    return Claim(fonte, texto, conf)


def test_grafo_detecta_conflito_entre_duas_rotas_que_nao_sao_a_principal():
    """No leque antigo, só reasoning (a principal) era comparada — e reasoning
    não cita número nenhum, então o conflito real (100 x 200) ficava invisível."""
    r = cross_check([
        _c("reasoning", "isto depende do contexto e da estação"),
        _c("computation", "o resultado e 100"),
        _c("web_search", "a resposta e 200"),
    ], 0.7)
    assert r.verdict == "divergente"
    assert len(r.conflicts) == 1
    par = {r.conflicts[0]["a"], r.conflicts[0]["b"]}
    assert par == {"computation", "web_search"}
    assert any(e["relacao"] == "diverge" for e in r.edges)


def test_grafo_capta_confirmacao_transitiva_que_o_leque_antigo_perdia():
    """own_memory concorda com web_search, web_search concorda com reasoning,
    mas own_memory x reasoning direto fica ABAIXO do piso léxico. O leque
    antigo (só principal x outros) contaria apenas web_search como confirmação;
    o grafo enxerga reasoning também, porque a convergência é real — só não é
    direta."""
    r = cross_check([
        _c("own_memory", "o cafe colombiano tem sabor forte"),
        _c("web_search", "cafe forte tem muita cafeina"),
        _c("reasoning", "cafeina forte demais atrapalha o sono"),
    ], 0.6)

    from backend.cognition.cross_check import _LEXICAL_FLOOR, lexical_overlap
    direto = lexical_overlap("o cafe colombiano tem sabor forte",
                             "cafeina forte demais atrapalha o sono")
    assert direto < _LEXICAL_FLOOR, "o fixture precisa ficar abaixo do piso direto"

    assert r.verdict == "confirmado"
    assert r.agreeing == ["reasoning", "web_search"]
    assert not r.conflicts


def test_edges_expoe_o_grafo_completo_nao_so_o_veredito_final():
    r = cross_check([
        _c("own_memory", "o cafe colombiano tem sabor forte"),
        _c("web_search", "cafe forte tem muita cafeina"),
        _c("reasoning", "cafeina forte demais atrapalha o sono"),
    ], 0.6)
    relacoes = {(e["a"], e["b"]): e["relacao"] for e in r.edges}
    assert len(relacoes) == 2, "3 rotas = 3 pares possíveis, um fica abaixo do piso"
    assert all(v == "concorda" for v in relacoes.values())


def test_conflito_em_par_nao_principal_ainda_expoe_quem_concordou():
    """Divergência derruba o veredito, mas o grafo não some com a concordância
    que também existia — transparência total, não escolha de qual sinal mostrar."""
    r = cross_check([
        _c("own_memory", "o cafe e forte e tem muita cafeina"),
        _c("web_search", "cafe forte com muita cafeina, 100mg por xicara"),
        _c("computation", "o calculo da cafeina da 200mg por xicara"),
    ], 0.7)
    assert r.verdict == "divergente"
    assert r.agreeing, "own_memory e web_search concordam mesmo com o conflito alhures"
