"""A4 · A/B real de estratégias por rota (roteiro de maestria).

Prova que duas rotas competem de verdade no mesmo tipo de objetivo: a atribuição
do braço é determinística e CAUSA a rota escolhida pelo planejador, missões reais
viram amostras, e o vencedor só é declarado quando a estatística sustenta.

E prova a garantia do incremento: sem experimento iniciado, o planejamento fica
idêntico ao de hoje.
"""
from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

import backend.evaluation.ab_experiment as AB
from backend.api.main import app
from backend.cognition.experience import signature
from backend.cognition.planner import _apply_experiment, get_planner
from backend.core import Task
from backend.evaluation.ab_experiment import ABRegistry, Arm, Experiment
from backend.hivemind.factory import build_hive

client = TestClient(app)


def _fresh() -> ABRegistry:
    AB._INSTANCE = None
    return AB.get_ab_registry()


class _Rota:
    """Rota mínima: só o que `_apply_experiment` toca."""

    def __init__(self, name: str, base: float, available: bool = True) -> None:
        self.name = name
        self._base = base
        self.available = available
        self.bias = 0.0

    def score(self) -> float:
        return 0.0 if not self.available else self._base + self.bias


# --- atribuição determinística ---------------------------------------------

def test_atribuicao_e_deterministica_e_reproduzivel():
    exp = Experiment(goal_signature="s", control=Arm("web_search"),
                     challenger=Arm("memory"))
    braco = exp.assign("quanto custa um telescópio")
    for _ in range(50):
        assert exp.assign("quanto custa um telescópio") == braco
    assert braco in ("control", "challenger")


def test_atribuicao_separa_objetivos_diferentes():
    exp = Experiment(goal_signature="s", control=Arm("a"), challenger=Arm("b"))
    bracos = {exp.assign(f"objetivo numero {i}") for i in range(40)}
    assert bracos == {"control", "challenger"}, "os dois braços devem receber carga"


def test_nao_aceita_ab_de_uma_rota_so():
    try:
        ABRegistry().start("s", "web_search", "web_search")
        assert False, "deveria recusar A/B com rotas iguais"
    except ValueError:
        pass


# --- o braço CAUSA a rota (A/B real, não observação passiva) ----------------

def test_o_braco_atribuido_VIRA_a_rota_escolhida():
    """O teste só passa se o viés inverter de fato uma ordem desfavorável."""
    reg = _fresh()
    goal = "comparar preços de telescópios amadores"
    exp = reg.start(signature(goal), control="web_search", challenger="memory")
    favorecida = exp.route_for(goal)
    perdedora = "memory" if favorecida == "web_search" else "web_search"

    # De propósito: a rota favorecida pelo experimento começa ATRÁS.
    def _par():
        return [_Rota(perdedora, 0.60), _Rota(favorecida, 0.50)]

    sem_experimento = _par()
    AB._INSTANCE = ABRegistry()          # registro vazio → nenhum viés
    _apply_experiment(sem_experimento, goal)
    assert sem_experimento[0].name == perdedora
    assert all(r.bias == 0.0 for r in sem_experimento)

    AB._INSTANCE = reg                   # experimento de volta
    com_experimento = _par()
    _apply_experiment(com_experimento, goal)
    assert com_experimento[0].name == favorecida, "o braço deve VIRAR a escolha"
    assert com_experimento[0].bias == AB.EXPERIMENT_BIAS


def test_o_experimento_nunca_ressuscita_rota_indisponivel():
    reg = _fresh()
    goal = "objetivo de teste do experimento"
    exp = reg.start(signature(goal), control="web_search", challenger="memory")
    favorecida = exp.route_for(goal)
    routes = [_Rota("web_search", 0.10, available=(favorecida != "web_search")),
              _Rota("memory", 0.10, available=(favorecida != "memory"))]
    _apply_experiment(routes, goal)
    indisponivel = [r for r in routes if r.name == favorecida][0]
    assert indisponivel.score() == 0.0, "indisponível continua fora, com viés ou sem"


def test_na_cartografa_real_o_experimento_nao_forca_rota_indisponivel():
    """Com a Cartógrafa REAL: 'reasoning' não existe para um cálculo, e nem o
    experimento a faz existir. O plano cai na rota disponível, sem quebrar."""
    reg = _fresh()
    goal = "quanto é 9 * 9"
    exp = reg.start(signature(goal), control="reasoning", challenger="reasoning_b")
    exp.challenger.route = "reasoning"          # os dois braços pedem a indisponível
    assert exp.route_for(goal) == "reasoning"
    plano = get_planner().plan(goal)
    assert plano.route.name != "reasoning"
    assert plano.route.available


def test_sem_experimento_o_plano_fica_identico():
    _fresh()
    goal = "quanto é 2+2"
    antes = get_planner().plan(goal).route.name
    assert AB.get_ab_registry().bias_for(goal) == {}
    assert get_planner().plan(goal).route.name == antes


# --- o veredito só sai quando a evidência sustenta -------------------------

def test_amostra_pequena_nao_declara_vencedor():
    exp = Experiment(goal_signature="s", control=Arm("a"), challenger=Arm("b"))
    for _ in range(3):
        exp.control.observe(True)
        exp.challenger.observe(False)
    v = exp.verdict()
    assert v["status"] == "coletando" and v["winner"] is None
    assert "amostra insuficiente" in v["reason"]


def test_diferenca_pequena_fica_inconclusiva():
    exp = Experiment(goal_signature="s", control=Arm("a"), challenger=Arm("b"))
    for i in range(20):
        exp.control.observe(i % 2 == 0)        # 50%
        exp.challenger.observe(i % 2 == 1)     # 50%
    v = exp.verdict()
    assert v["status"] == "inconclusivo" and v["winner"] is None
    assert v["z"] == 0.0


def test_separacao_clara_declara_o_vencedor_com_z():
    exp = Experiment(goal_signature="s", control=Arm("a"), challenger=Arm("b"))
    for i in range(12):
        exp.control.observe(i != 0)            # 11/12
        exp.challenger.observe(i < 2)          # 2/12
    v = exp.verdict()
    assert v["status"] == "decidido" and v["winner"] == "control"
    assert v["z"] > 1.96
    assert v["control"]["rate"] > v["challenger"]["rate"]


def test_braco_sem_tentativa_nao_tem_taxa_zero_e_sim_nenhuma():
    a = Arm("web_search")
    assert a.rate is None and a.avg_duration is None
    a.observe(True, duration=2.0)
    assert a.rate == 1.0 and a.avg_duration == 2.0


def test_experimento_decidido_para_de_receber_vies():
    reg = _fresh()
    goal = "objetivo que vai ser decidido"
    exp = reg.start(signature(goal), control="web_search", challenger="memory")
    assert reg.bias_for(goal) != {}
    for i in range(12):
        exp.control.observe(i != 0)
        exp.challenger.observe(i < 2)
    exp.close()
    assert not exp.running
    assert reg.bias_for(goal) == {}, "experimento encerrado não enviesa mais"


# --- missões reais alimentam o experimento ---------------------------------

def test_missoes_reais_viram_amostras_do_braco_certo():
    reg = _fresh()
    goal = "quanto é 2+2"
    exp = reg.start(signature(goal), control="computation", challenger="memory")
    esperado = exp.assign(goal)

    hive, _ = build_hive(db_path=":memory:")
    for _ in range(3):
        asyncio.run(hive.solve(Task(goal=goal)))

    assert exp.arm(esperado).trials == 3, "as 3 missões devem cair no MESMO braço"
    assert exp.arm("control" if esperado == "challenger" else "challenger").trials == 0
    assert exp.verdict()["status"] == "coletando"   # 3 amostras não decidem nada


def test_o_laco_fecha_na_missao_real_braco_escolhe_rota_e_desfecho_volta():
    """A prova do A/B REAL: o braço decide a rota e o desfecho volta ao braço."""
    from backend.hivemind.mission_runner import run_mission
    from backend.memory.shared_memory import SharedMemory

    reg = _fresh()
    goal = "quanto é 9 * 9"
    # As DUAS rotas disponíveis de verdade para um cálculo (medido na Cartógrafa:
    # computation 0.559, memory 0.320). O id é FIXO de propósito: com ele o
    # objetivo cai no desafiante, então o teste sempre prova o caso difícil —
    # o experimento tirando a missão da rota que ela escolheria sozinha.
    assert get_planner().plan(goal).route.name == "computation", \
        "sem experimento, a colônia escolheria o cálculo exato"

    exp = Experiment(goal_signature=signature(goal), control=Arm("computation"),
                     challenger=Arm("memory"), id="ab-fixo-1")
    reg._items[exp.id] = exp
    assert exp.assign(goal) == "challenger"

    out = asyncio.run(run_mission(goal, SharedMemory(":memory:")))

    # 1) o braço CAUSOU a rota: a missão foi para 'memory', não para 'computation'
    assert out["route"]["name"] == "memory"
    assert out["route"]["bias"] >= AB.EXPERIMENT_BIAS
    # 2) o desfecho voltou para o MESMO braço
    assert exp.challenger.trials == 1
    assert exp.control.trials == 0


def test_missao_sem_experimento_ativo_nao_registra_nada():
    reg = _fresh()
    hive, _ = build_hive(db_path=":memory:")
    asyncio.run(hive.solve(Task(goal="quanto é 8-3")))
    assert reg.list() == []


# --- observabilidade -------------------------------------------------------

def test_endpoints_iniciam_e_expoem_o_experimento():
    _fresh()
    r = client.post("/experiments", json={"goal_signature": "preco telescopio",
                                          "control": "web_search",
                                          "challenger": "deep_research"})
    assert r.status_code == 200
    exp_id = r.json()["experiment"]["id"]

    g = client.get(f"/experiments/{exp_id}")
    assert g.status_code == 200
    body = g.json()
    assert body["status"] == "coletando" and body["winner"] is None
    assert body["control"]["route"] == "web_search"
    assert body["control"]["rate"] is None       # nunca inventa taxa

    assert len(client.get("/experiments").json()["experiments"]) == 1
    assert client.get("/experiments/nao-existe").status_code == 404


def test_endpoint_recusa_ab_invalido():
    _fresh()
    r = client.post("/experiments", json={"goal_signature": "x",
                                          "control": "memory",
                                          "challenger": "memory"})
    assert r.status_code == 400
