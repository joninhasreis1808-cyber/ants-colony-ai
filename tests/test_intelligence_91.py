"""Testes da inteligência offline leve (9.1) — sinônimos, fatos, analogia, tom."""
from __future__ import annotations

import pytest

from backend.cognitive.chain_of_thought import ChainOfThought
from backend.cognitive.response_composer import ResponseComposer
from backend.knowledge.facts_base import get_facts_base
from backend.nlp.synonyms import canonical_question, expand_query, synonyms
from backend.reasoning.analogy import AnalogyReasoner


# ---- Bloco A: sinônimos / expansão ----
def test_canonical_normaliza_variacoes():
    for v in ["me explique a fotossíntese", "defina a fotossíntese",
              "fala sobre a fotossíntese", "o que é a fotossíntese"]:
        assert canonical_question(v).startswith("o que e ")
    assert "o que e o que e" not in canonical_question("me explique o que é X")


def test_sinonimos_e_expansao():
    assert "automovel" in synonyms("carro")
    assert "carro" in synonyms("automovel")
    exp = expand_query("o que é um carro")
    assert "carro" in exp and "automovel" in exp


def test_expansao_sem_sinonimo_mantem_palavra():
    assert "fotossintese" in expand_query("o que é a fotossíntese")


# ---- Bloco B: base de fatos + regras + analogia ----
def test_fato_estruturado_responde_sem_web():
    fb = get_facts_base()
    fact = fb.lookup("o que é a água?")
    assert fact and fact["entity"] == "agua"
    assert "H2O" in fact["definition"] or "hidrogênio" in fact["definition"]


def test_lookup_por_alias():
    fb = get_facts_base()
    assert fb.lookup("me explique a IA")["entity"] == "inteligencia artificial"


def test_regra_se_entao_aplica():
    fb = get_facts_base()
    r = fb.apply_rules("quando tem chuva o chão fica molhado?")
    assert r and "molhado" in r


def test_pergunta_fora_da_base_nao_casa():
    fb = get_facts_base()
    assert fb.lookup("quem venceu a eleição de 2020?") is None


def test_analogia_encontra_caso_similar_e_adapta():
    ar = AnalogyReasoner(threshold=0.3)
    cases = [("como organizar uma pasta de downloads", "1. agrupar 2. mover"),
             ("o que é python", "linguagem de programação")]
    m = ar.find_similar("como organizar a pasta de fotos", cases)
    assert m and "organizar" in m.query
    texto = ar.adapt("como organizar a pasta de fotos", m)
    assert "analogia" in texto.lower()


# ---- Bloco C: composição fluente + cadeia ----
def test_composer_definicao_cita_proveniencia():
    out = ResponseComposer().definition("água", "A água é H2O.", "essencial: vida")
    assert "A água é H2O." in out and "base de conhecimento" in out


def test_composer_limitacao_continua_honesta():
    out = ResponseComposer().limitation("dado atual sem web")
    assert "não sei" in out.lower() and "inventar" in out.lower()


def test_composer_passos_numera():
    out = ResponseComposer().steps("Plano:", ["a", "b", "c"])
    assert "1. a" in out and "3. c" in out


def test_composer_web_cita_fontes():
    out = ResponseComposer().web("Resposta.", 3, ["pt.wikipedia.org"])
    assert "3 fonte" in out and "wikipedia" in out


def test_chain_of_thought_organiza_sem_inventar():
    ch = ChainOfThought().build("o que é a água", ["A água é H2O"],
                                "A água é essencial", "knowledge_base")
    assert ch.steps[0].startswith("Primeiro")
    assert any("Logo" in s for s in ch.steps)
    assert "H2O" in ch.text


# ---- Integração: pergunta de conceito → base (sem web) ----
@pytest.mark.asyncio
async def test_pipeline_responde_da_base(monkeypatch):
    from backend.api.routes.hive import _answer_from_knowledge
    from backend.core import Task

    task = Task(goal="me explique o que é a gravidade")
    emitted = []

    async def emit(msg, data=None):
        emitted.append(msg)

    handled = await _answer_from_knowledge(task, emit)
    assert handled is True
    assert task.result["provenance"]["source"] == "knowledge_base"
    assert task.result["provenance"]["chain"]["steps"]


# ---- Bloco D: consolidação por frequência + "Aprender isto" ----
def test_frequencia_sobe_com_uso():
    from backend.memory.answer_cache import get_answer_cache
    c = get_answer_cache()
    c.clear()
    c.put("o que é X", {"answer": "resposta", "source": "memory"})
    assert c.frequency("o que é X") == 0
    c.get("o que é X"); c.get("o que é X")
    assert c.frequency("o que é X") == 2
    assert c.most_frequent(1)[0][1] == 2


def test_endpoint_aprender_isto():
    from fastapi.testclient import TestClient
    from backend.api.main import app
    from backend.memory.answer_cache import get_answer_cache
    get_answer_cache().clear()
    client = TestClient(app)
    r = client.post("/hive/learn", json={"question": "o que é o Ant's",
                                         "answer": "um superorganismo digital"})
    assert r.status_code == 200 and r.json()["learned"] is True
    assert get_answer_cache().get("o que é o Ant's")["answer"] == "um superorganismo digital"
    # vazio → erro honesto
    assert client.post("/hive/learn", json={"question": "", "answer": ""}).status_code == 400


# ---- extras: cobertura de dispatch/utilidades ----
def test_composer_compose_dispatch():
    c = ResponseComposer()
    assert "cálculo exato" in c.compose("computation", {"value": "53"})
    assert "1. a" in c.compose("steps", {"title": "T:", "steps": ["a"]})
    assert "não sei" in c.compose("limitation", {}).lower()


def test_facts_has_e_regra():
    fb = get_facts_base()
    assert fb.has("o que é a internet") is True
    assert fb.has("qual o preço do dólar amanhã") is False


def test_chain_inclui_fonte():
    ch = ChainOfThought().build("q", ["ev"], "concl", "web_search")
    assert any("Fonte usada: web_search" in s for s in ch.steps)


def test_analogy_sem_casos_retorna_none():
    assert AnalogyReasoner().find_similar("qualquer", []) is None
