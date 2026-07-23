"""Testes do córtex determinístico (7.2 · Bloco D.1).

Cálculo exato, offline, sem `eval`, roteado antes da busca. Corrige a falha
do diagnóstico: √2809 → 53 com proveniência `computation`.
"""
from __future__ import annotations

import pytest

from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.providers.router import ProviderRouter
from backend.reasoning.deterministic import DeterministicCortex
from tests.conftest import FakeProvider


def test_raiz_quadrada_exata():
    c = DeterministicCortex()
    out = c.solve("Qual é a raiz quadrada de 2809?")
    assert out and out.kind == "sqrt"
    assert out.answer == "53"
    assert out.steps  # tem passos "como cheguei nisso"


def test_aritmetica_e_porcentagem_e_potencia():
    c = DeterministicCortex()
    assert c.solve("Quanto é 12*7+3?").answer == "87"
    assert c.solve("Qual é 15% de 200?").answer == "30"
    assert c.solve("Quanto é 2 elevado a 10?").answer == "1024"
    assert c.solve("7 ao quadrado").answer == "49"


def test_raiz_irracional_aproximada():
    c = DeterministicCortex()
    out = c.solve("raiz quadrada de 2")
    assert out and out.answer.startswith("1.4142")


def test_nao_calculavel_retorna_none():
    c = DeterministicCortex()
    assert c.solve("O que são feromônios?") is None
    assert c.solve("Quem venceu a eleição?") is None
    assert c.solve("") is None


def test_sem_eval_expressao_maliciosa_ignorada():
    c = DeterministicCortex()
    # Não deve executar código: sem dígitos+operador → não é cálculo.
    assert c.solve("__import__('os').system('ls')") is None


@pytest.mark.asyncio
async def test_hive_usa_computation_como_fonte():
    hive, _ = build_hive(
        db_path=":memory:", router=ProviderRouter([FakeProvider(results=[])])
    )
    task = await hive.solve(Task(goal="Qual é a raiz quadrada de 2809?"))
    r = task.result
    assert "53" in r["answer"]
    assert r["confidence"] == 1.0
    assert r["provenance"]["source"] == "computation"
    assert r["provenance"]["web"] == "web: nao necessario"
    assert r["computation"]["kind"] == "sqrt"
