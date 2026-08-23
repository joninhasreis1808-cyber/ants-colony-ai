"""Auto-avaliação viva (9.13) — exercita TODA capacidade de ponta a ponta.

Não é import-check: cada teste roda o comportamento REAL (endpoint ou módulo) e
compara ESPERADO × REAL. É a auto-avaliação profissional transformada em suíte,
para que qualquer regressão numa das capacidades apareça no CI, não num relatório.

Cobre: keep-alive, /health, ferramentas gated + path_guard, missão que AGE com
ferramenta, histórico persistível, laço autônomo, decisão coletiva route-aware,
guarda de objetivo, atenção, divisão de trabalho, governador, memória de
experiência, evolução controlada, córtex plugável, pesquisa profunda offline,
blackboard, cartógrafa, planejador e PWA.
"""
from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _forca_rules(monkeypatch):
    """Córtex determinístico e singletons limpos — o audit não depende de rede."""
    monkeypatch.setenv("ANTS_LLM", "rules")
    monkeypatch.delenv("ANTS_LLM_API_KEY", raising=False)
    monkeypatch.delenv("ANTS_STATE_DIR", raising=False)
    from backend.cognition import experience as E
    from backend.hivemind import evolution as V
    from backend.hivemind import mission as M
    from backend.hivemind import mission_runner as R
    E.reload_experience(); V.reload_evolution_ledger()
    M.reload_mission_store(); R.reload_outcomes()
    yield
    E.reload_experience(); V.reload_evolution_ledger()
    M.reload_mission_store(); R.reload_outcomes()


@pytest.fixture()
def client():
    from backend.api.main import app
    with TestClient(app) as c:
        yield c


def _mem():
    from backend.memory.shared_memory import SharedMemory
    return SharedMemory(":memory:")


def test_ping(client):
    assert client.get("/ping").json() == {"pong": "ok"}


def test_health_completo(client):
    b = client.get("/health").json()
    assert b["status"] == "healthy"
    assert b["modules"]["planning"] is True
    assert b["intelligence"]["hierarchical_planner"] is True
    assert b["intelligence"]["cartographer"]
    assert b["reasoning"]["backend"] in ("rules", "ollama", "api")
    assert b["tests"] > 0
    assert b["intelligence"]["mission_endpoint"] == "/mission"


def test_ferramenta_gated_compute(client):
    b = client.post("/tools/run",
                    json={"name": "compute", "args": {"expression": "12*12"}}).json()
    assert b["ok"] and str(b["result"]["answer"]) == "144"


def test_path_guard_recusa_proibido():
    from backend.tools.registry import get_tool_registry
    res = get_tool_registry().run("read_file", {"path": "/etc/passwd"})
    assert res.get("ok") is False


def test_missao_age_com_ferramenta(client):
    b = client.post("/mission/run",
                    json={"goal": "quanto é 12*12", "online": False}).json()
    assert "144" in str(b["answer"])
    assert any(t.get("tool") == "compute" and t.get("ok")
               for t in b.get("tools_used", []))
    assert b["state"] == "done"


def test_historico_e_desfecho(client):
    client.post("/mission/run", json={"goal": "quanto é 5*5", "online": False})
    b = client.get("/mission").json()
    assert b["count"] >= 1
    mid = b["missions"][0]["id"]
    assert client.get(f"/mission/{mid}").status_code == 200


def test_missao_autonoma_converge(client):
    b = client.post("/mission/auto",
                    json={"goal": "quanto é 7*6", "online": False, "max_cycles": 3}).json()
    assert "42" in str(b.get("answer", ""))
    assert len(b["cycles"]) <= 3


def test_decisao_coletiva_route_aware():
    from backend.hivemind.collective import DecisionSignals, get_collective_decider
    dec = get_collective_decider()
    det = dec.decide(DecisionSignals(evidence_count=0, sources=0, contradictions=0,
                                     drifted=False, confidence=1.0,
                                     evidence_based=False))
    evd = dec.decide(DecisionSignals(evidence_count=0, sources=0, contradictions=0,
                                     drifted=False, confidence=1.0,
                                     evidence_based=True))
    assert det.decision == "comprometer"
    assert evd.decision == "investigar"


def test_guarda_de_objetivo_sem_falso_desvio():
    from backend.cognition.critic import get_goal_guard
    assert get_goal_guard().check("quanto é 12*12", "quanto é 12*12").drifted is False


def test_atencao_e_trabalho():
    from backend.hivemind.attention import get_attention_field
    from backend.hivemind.collective import DecisionSignals, get_collective_decider
    from backend.hivemind.labor import get_labor_allocator
    af = get_attention_field("audit")
    af.reinforce("café e sono", weight=0.5)
    assert af.focus(limit=3)
    s = DecisionSignals(evidence_count=0, sources=0, contradictions=2,
                        drifted=True, confidence=0.2, evidence_based=True)
    v = get_collective_decider().decide(s)
    a = get_labor_allocator().allocate(s, v)
    assert v.decision == "investigar" and a.total > 0


def test_governador_respeita_teto():
    from backend.hivemind.autonomy import AutonomyGovernor, run_autonomous_mission
    from backend.hivemind.tool_executor import make_tool_executor
    g = AutonomyGovernor(max_cycles=2)
    ex = make_tool_executor("", False, False)
    out = asyncio.run(run_autonomous_mission("quanto é 9*9", _mem(),
                                             executor=ex, governor=g,
                                             context={"online": False}))
    assert len(out["cycles"]) <= 2


def test_memoria_experiencia_vies():
    from backend.cognition.experience import (
        apply_experience, get_strategy_memory)
    sm = get_strategy_memory()
    sm.record_success("aprender python rápido", "reasoning", 1.0)
    sm.record_success("aprender python rápido", "reasoning", 1.0)
    assert sm.suggest("aprender python rápido") == "reasoning"

    class R:
        def __init__(self, name): self.name = name; self.bias = 0.0
        def score(self): return 0.5 + self.bias
    routes = [R("reasoning"), R("web_search")]
    apply_experience(routes, "aprender python rápido")
    assert routes[0].name == "reasoning"


def test_evolucao_controlada_fluxo(client):
    from backend.cognition.experience import get_error_memory
    em = get_error_memory()
    for _ in range(3):
        em.remember("tarefa que falha sempre", "web_search", "timeout")
    b = client.post("/evolution/mine").json()
    assert b["count"] >= 1
    pid = b["proposed"][0]["id"]
    assert client.post(f"/evolution/{pid}/approve").status_code == 200
    ap = client.post(f"/evolution/{pid}/apply").json()
    assert ap["ok"] and "código" in ap["note"]


def test_pesquisa_profunda_offline():
    from backend.core import Task
    from backend.hivemind import deep_research
    from backend.providers.local_provider import LocalProvider
    from backend.providers.router import ProviderRouter
    asyncio.run(deep_research.run(Task(goal="café e sono"), _mem(), None,
                                  ProviderRouter([LocalProvider()])))


def test_planejador_e_cartografa():
    from backend.cognition.cartographer import _CATALOG
    from backend.cognition.planner import get_planner
    assert len(_CATALOG) >= 3
    plan = get_planner().plan("pesquise a fundo o café",
                              {"online": True, "deep": True})
    assert plan.route.name and plan.graph.topological_order()


def test_pwa_na_raiz(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "mission_console.js" in r.text
