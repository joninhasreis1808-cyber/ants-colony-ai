"""A5 · Meta-cognição real (roteiro de maestria).

Prova o critério do roteiro: **a formação da missão 11 usa os dados das 10
anteriores**. E prova a garantia de segurança do incremento: sem histórico, a
formação sai byte a byte igual à de hoje (viés zero, ordenação estável).
"""
from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

import backend.cognitive.self_performance as SP
from backend.api.main import app
from backend.core import Task
from backend.cognitive.self_performance import SelfPerformance
from backend.hivemind.factory import build_hive
from backend.hivemind.recruiter import Recruiter

client = TestClient(app)


def _fresh() -> SelfPerformance:
    SP._INSTANCE = None
    return SP.get_self_performance()


class _FakeBot:
    """Bot mínimo: só o que o Recruiter olha (nome + skills)."""

    def __init__(self, name: str, skills: list[str]) -> None:
        self.name = name
        self.skills = skills


# --- a memória de desempenho mede o que aconteceu --------------------------

def test_mede_sucesso_por_casta_tempo_por_rota_e_melhor_rota():
    sp = SelfPerformance()
    sp.record(signature="pesquisa", route="web_search",
              castes=["ScoutBot", "AnalystBot"], success=True, duration=2.0)
    sp.record(signature="pesquisa", route="web_search",
              castes=["ScoutBot"], success=False, duration=4.0)
    sp.record(signature="pesquisa", route="memory",
              castes=["AnalystBot"], success=False, duration=1.0)

    assert sp.total == 3
    assert sp.success_rate("ScoutBot") == 0.5      # 1 de 2
    assert sp.success_rate("AnalystBot") == 0.5    # 1 de 2
    assert sp.success_rate("NuncaVisto") is None   # não inventa
    assert sp.avg_time("web_search") == 3.0        # (2+4)/2
    assert sp.avg_time("rota_fantasma") is None
    assert sp.best_route("pesquisa") == "web_search"   # 0.5 > 0.0
    assert sp.best_route("outro_tipo") is None


def test_janela_recente_nao_cresce_sem_limite():
    sp = SelfPerformance()
    for i in range(SP._MAX_RECORDS + 25):
        sp.record(signature="s", route="r", castes=["B"], success=True, duration=1.0)
    assert sp.total == SP._MAX_RECORDS


# --- o critério do roteiro: a missão 11 usa as 10 anteriores ---------------

def test_formacao_da_missao_11_usa_os_dados_das_10_anteriores():
    sp = _fresh()
    # Dois bots do MESMO estágio (ambos "decide"): só o desempenho os separa.
    fraco = _FakeBot("BotFraco", ["decide"])
    forte = _FakeBot("BotForte", ["decide"])
    rec = Recruiter([fraco, forte])   # roster com o fraco primeiro

    # Sem histórico: a formação é a de hoje (ordem do roster preservada).
    assert [b.name for b in rec.recruit(["decide"])] == ["BotFraco", "BotForte"]

    # 10 missões reais: o forte entrega, o fraco não.
    for i in range(10):
        sp.record(signature="decidir", route="web_search", castes=["BotForte"],
                  success=True, duration=1.0)
        sp.record(signature="decidir", route="memory", castes=["BotFraco"],
                  success=False, duration=1.0)
    assert sp.total == 20

    # Missão 11: a Rainha consulta o desempenho e inverte a formação.
    assert [b.name for b in rec.recruit(["decide"])] == ["BotForte", "BotFraco"]


def test_o_vies_nunca_atravessa_o_fluxo_natural():
    sp = _fresh()
    # O decisor tem 100% de sucesso; o navegador, 0%. Ainda assim o fluxo
    # natural manda: navegar vem ANTES de decidir. O viés só desempata.
    sp.record(signature="s", route="r", castes=["Decisor"], success=True)
    sp.record(signature="s", route="r", castes=["Navegador"], success=False)
    rec = Recruiter([_FakeBot("Decisor", ["decide"]),
                     _FakeBot("Navegador", ["navigate"])])
    assert [b.name for b in rec.recruit(["decide", "navigate"])] == \
        ["Navegador", "Decisor"]


def test_sem_historico_o_vies_e_zero():
    _fresh()
    bots = [_FakeBot(f"Bot{i}", ["decide"]) for i in range(5)]
    rec = Recruiter(bots)
    assert [b.name for b in rec.recruit(["decide"])] == [b.name for b in bots]


# --- o laço vivo alimenta a meta-cognição sozinho --------------------------

def test_missoes_reais_alimentam_o_desempenho_proprio():
    sp = _fresh()
    assert sp.total == 0
    hive, _ = build_hive(db_path=":memory:")
    for objetivo in ("quanto é 2+2", "quanto é 9-4", "quanto é 3*3"):
        asyncio.run(hive.solve(Task(goal=objetivo)))
    assert sp.total == 3, "cada missão deveria registrar o desempenho próprio"
    d = sp.to_dict()
    assert d["routes"], "a rota real da missão deveria ter sido registrada"
    assert d["formation_hint"], "as castas que trabalharam deveriam ter taxa"
    # cálculo exato ancora → a colônia se mede como bem-sucedida
    assert all(0.0 <= v <= 1.0 for v in d["formation_hint"].values())


# --- observabilidade -------------------------------------------------------

def test_endpoint_expoe_o_desempenho_proprio():
    sp = _fresh()
    sp.record(signature="pesquisa", route="web_search", castes=["ScoutBot"],
              success=True, duration=2.5)
    r = client.get("/self-performance")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["formation_hint"]["ScoutBot"] == 1.0
    assert body["route_times"]["web_search"] == 2.5

    b = client.get("/self-performance/route/pesquisa")
    assert b.status_code == 200 and b.json()["best_route"] == "web_search"


def test_endpoint_nao_inventa_quando_nao_ha_missao():
    _fresh()
    body = client.get("/self-performance").json()
    assert body["total"] == 0
    assert body["formation_hint"] == {} and body["routes"] == []
    assert client.get("/self-performance/route/nada").json()["best_route"] is None
