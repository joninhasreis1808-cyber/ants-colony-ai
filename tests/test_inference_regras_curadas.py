"""`InferenceEngine` com regras de verdade (Precisão Offline v1 · item 6).

O motor sempre esteve correto e testado — e sempre rodou VAZIO: `add_rule`
nunca era chamado em lugar nenhum, então `POST /mind/infer` encadeava
fatos contra zero regras e não derivava nada, nunca.

As regras que já existiam (`rules` de facts.json) não servem aqui: lá o
`if` são palavras a detectar no TEXTO da pergunta e o `then` é prosa de
explicação — conclusão em prosa nunca poderia ser condição de outra
regra, então nenhum encadeamento aconteceria. Daí a base própria, no
formalismo que este motor de fato usa.
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.reasoning.inference import (
    InferenceEngine, curated_rules, get_inference_engine,
)

RAIZ = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_construtor_cru_continua_vazio():
    """Quem monta a própria base (inclusive os testes que já existiam)
    não pode ser afetado pelas regras curadas."""
    assert InferenceEngine().rule_count() == 0


def test_singleton_vem_com_as_regras_curadas():
    motor = get_inference_engine()
    assert motor.rule_count() >= 20
    assert motor.rule_count() == len(curated_rules())


def test_encadeamento_de_varios_saltos_acontece_de_verdade():
    """O ponto do item: conclusão de uma regra sendo condição da próxima.
    `sol` → estrela → corpo celeste → tem massa → sofre gravidade."""
    motor = get_inference_engine()
    derivados = motor.infer(["sol"])
    for esperado in ("estrela", "corpo celeste", "tem massa", "sofre gravidade"):
        assert esperado in derivados
    assert motor.can_derive("sofre gravidade", ["sol"]) is True


def test_regra_de_conjuncao_exige_as_duas_condicoes():
    motor = get_inference_engine()
    # "organismo autotrófico" precisa de ser vivo E faz fotossíntese;
    # "planta" deriva os dois, "bactéria" só o primeiro.
    assert motor.can_derive("organismo autotrófico", ["planta"]) is True
    assert motor.can_derive("organismo autotrófico", ["bactéria"]) is False


def test_fato_sem_regra_nao_deriva_nada():
    motor = get_inference_engine()
    assert motor.infer(["pedra"]) == []
    assert motor.can_derive("ser vivo", ["pedra"]) is False


def test_explain_nao_fabrica_mais_a_justificativa():
    """Defeito real, achado ao ligar o motor e olhar a saída: `explain`
    pegava a PRIMEIRA regra com aquela conclusão, não a que disparou. Com
    o fato "planta", a cadeia afirmava "bactéria => ser vivo" — citando
    como causa algo que nunca esteve entre os fatos."""
    motor = get_inference_engine()
    cadeia = motor.explain("organismo autotrófico", ["planta"])
    assert any(p.startswith("planta => ser vivo") for p in cadeia)
    assert not any("bactéria" in p for p in cadeia), (
        "a cadeia não pode citar uma condição que não estava entre os fatos"
    )


def test_explain_so_cita_regras_com_condicoes_conhecidas():
    """Versão isolada e sintética do mesmo contrato, sem depender da base
    curada: duas regras levam à mesma conclusão, só uma é sustentável."""
    motor = InferenceEngine()
    motor.add_rule(["x"], "z")
    motor.add_rule(["y"], "z")
    cadeia = motor.explain("z", ["y"])
    assert cadeia == ["y => z"]


def test_rota_infer_deriva_e_mostra_a_cadeia():
    """Prova pela rota real, não só a peça isolada (lição do #92)."""
    r = client.post("/mind/infer",
                    json={"facts": ["feromônio"], "goal": "inteligência coletiva"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["rules_loaded"] >= 20, (
        "a rota precisa declarar quantas regras tem — antes rodava com "
        "zero e não havia como perceber isso pela resposta"
    )
    assert "estigmergia" in corpo["derived"]
    assert corpo["can_derive"] is True
    assert corpo["chain"], "a cadeia precisa mostrar QUAIS regras sustentaram"


def test_base_curada_e_valida_e_encadeavel():
    """Contrato do arquivo: toda conclusão é um símbolo curto (não prosa),
    e pelo menos uma conclusão é condição de outra regra — senão o motor
    de encadeamento não teria o que encadear."""
    dados = json.loads(
        (RAIZ / "backend/knowledge/data/inference_rules.json")
        .read_text(encoding="utf-8"))
    regras = dados["rules"]
    assert len(regras) >= 20
    conclusoes = {r["then"] for r in regras}
    condicoes = {c for r in regras for c in r["if"]}
    assert conclusoes & condicoes, "nenhuma conclusão serve de condição"
    for r in regras:
        assert len(r["then"].split()) <= 4, (
            f"conclusão em prosa não encadeia: {r['then']!r}"
        )
