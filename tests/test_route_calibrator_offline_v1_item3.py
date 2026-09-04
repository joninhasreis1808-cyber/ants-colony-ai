"""RouteCalibrator (Precisão Offline v1 · item 3): os priors da Cartógrafa
deixam de ser só o chute do catálogo, para sempre — passam a puxar em
direção à taxa de acerto REAL de cada rota, medida pelas missões reais.

Reaproveita o MESMO sinal de acerto em camadas (B3, correctness_signal.py)
que já alimenta o ConfidenceCalibrator — não um sinal novo. Mesma lição do
#92: prova pela rota real (Hivemind._feed_calibrator, Cartographer.discover),
não só a peça isolada.
"""
from __future__ import annotations

import asyncio

from backend.cognition.cartographer import Cartographer
from backend.core import Task
from backend.evaluation.confidence_calibration import (
    RouteCalibrator, get_calibrator, get_route_calibrator,
)
from backend.hivemind.factory import build_hive
from backend.hivemind.hive import Hivemind


def _fresh() -> RouteCalibrator:
    import backend.evaluation.confidence_calibration as CC
    CC._ROUTE_INSTANCE = None
    return CC.get_route_calibrator()


def test_sem_amostra_suficiente_devolve_o_prior_intacto():
    rc = _fresh()
    assert rc.observed_rate("computation") is None
    assert rc.calibrate("computation", 0.98) == 0.98


def test_com_amostra_suficiente_puxa_em_direcao_a_taxa_real():
    rc = RouteCalibrator(min_samples=5, full_trust=20)
    for _ in range(5):
        rc.record("web_search", correct=False, weight=1.0)  # rota sempre errada
    rate = rc.observed_rate("web_search")
    assert rate == 0.0
    calibrado = rc.calibrate("web_search", prior=0.72)
    assert 0.0 < calibrado < 0.72, (
        "com 5 falhas confirmadas, o prior (0.72) precisa cair — mas só "
        "parcialmente, 5 de 20 amostras de confiança plena"
    )


def test_confianca_plena_faz_o_prior_convergir_para_a_taxa_observada():
    rc = RouteCalibrator(min_samples=5, full_trust=20)
    for _ in range(20):
        rc.record("web_search", correct=False, weight=1.0)
    calibrado = rc.calibrate("web_search", prior=0.72)
    assert calibrado == 0.0, (
        "com amostra plena (20/20), a taxa real observada deve dominar por "
        "completo sobre o chute do catálogo"
    )


def test_peso_do_sinal_conta_nao_so_a_contagem_bruta():
    rc = RouteCalibrator(min_samples=1, full_trust=10)
    rc.record("reasoning", correct=True, weight=3.0)   # sinal forte
    rc.record("reasoning", correct=False, weight=1.0)  # sinal fraco
    rate = rc.observed_rate("reasoning")
    assert rate == 0.75, f"esperava 3/(3+1)=0.75, achei {rate}"


def test_reset_zera_tudo():
    rc = RouteCalibrator(min_samples=1)
    rc.record("computation", correct=True)
    assert rc.observed_rate("computation") is not None
    rc.reset()
    assert rc.observed_rate("computation") is None


def test_cartografa_reflete_calibracao_de_verdade():
    """Prova pela peça de cima (Cartographer.discover), não só o
    RouteCalibrator isolado: uma rota historicamente ruim pontua mais
    baixo no mapa real de rotas."""
    rc = _fresh()
    for _ in range(20):
        rc.record("web_search", correct=False, weight=1.0)
    routes = Cartographer().discover("pesquise o clima de hoje",
                                     context={"online": True})
    web = next(r for r in routes if r.name == "web_search")
    assert web.success_probability < 0.72, (
        f"esperava success_probability calibrado abaixo do prior 0.72, "
        f"achei {web.success_probability}"
    )


def test_missao_real_alimenta_o_calibrador_de_rota():
    """Prova pela rota REAL (POST /hive/task via Hivemind.solve): uma
    missão de cálculo exato precisa deixar rastro no RouteCalibrator, não
    só no ConfidenceCalibrator por faixa de confiança."""
    rc = _fresh()
    cc = get_calibrator()
    cc.reset()
    hive, _ = build_hive(db_path=":memory:")
    asyncio.run(hive.solve(Task(goal="quanto é 9*9")))
    assert rc.raw_count("computation") >= 1, (
        "a missão real de cálculo exato precisa alimentar RouteCalibrator "
        "sob a rota 'computation' — mesmo sinal que já alimenta o "
        "ConfidenceCalibrator por faixa de confiança"
    )


def test_feed_calibrator_ignora_rota_vazia():
    rc = _fresh()
    Hivemind._feed_calibrator(0.8, "", False)
    assert rc.to_dict() == {}
