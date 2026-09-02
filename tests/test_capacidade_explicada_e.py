"""E · Capacidade que se explica (FASE E · roteiro de maestria).

O catálogo de ferramentas dizia `available: false` e parava aí. O dono via cinco
de seis ferramentas indisponíveis **sem nenhuma pista** do motivo nem do que
fazer a respeito — um "não" sem ação possível.

E havia uma pré-condição **escondida**: as ferramentas de arquivo passam pelo
`path_guard` além do escopo. `can_use()` só olhava o escopo, então uma ferramenta
podia aparecer como disponível e **falhar na hora de rodar**. A colônia prometia
o que não podia cumprir.

Aqui ela passa a declarar as duas coisas: por que não pode, e o que destrava.
E o remédio é EXECUTÁVEL — os testes aplicam o que ele manda e conferem que a
ferramenta destrava de verdade.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.permissions.device_scopes import get_device_scopes
from backend.permissions.path_guard import get_path_guard
from backend.tools.registry import get_tool_registry

client = TestClient(app)


def _zerado():
    """Estado sem permissão nenhuma — o que o dono vê na primeira vez."""
    get_path_guard().clear()
    for escopo in ("read_files", "write_files"):
        try:
            get_device_scopes().revoke(escopo)
        except Exception:  # noqa: BLE001 - revogar o que não existe é inofensivo
            pass
    return get_tool_registry()


# ===  o "nao" passa a vir com motivo e remedio  ==============================

def test_indisponivel_declara_o_motivo_e_o_caminho():
    r = _zerado()
    d = r.availability("read_file")
    assert d["available"] is False
    assert d["reason"] and d["remedy"]
    assert "escopo" in d["blockers"] and "pasta" in d["blockers"]


def test_a_pre_condicao_ESCONDIDA_do_path_guard_agora_aparece():
    """Antes: escopo concedido -> `available: true` -> a ferramenta falhava."""
    r = _zerado()
    get_device_scopes().grant("read_files")
    d = r.availability("read_file")
    assert d["available"] is False, "sem pasta autorizada, não está disponível"
    assert d["blockers"] == ["pasta"]
    assert "nenhuma pasta foi autorizada" in d["reason"]


def test_o_remedio_e_EXECUTAVEL_e_destrava_de_verdade():
    r = _zerado()
    assert r.availability("read_file")["available"] is False
    get_device_scopes().grant("read_files")          # metade do remédio
    assert r.availability("read_file")["blockers"] == ["pasta"]
    get_path_guard().allow("/home/user/dados")       # a outra metade
    d = r.availability("read_file")
    assert d["available"] is True
    assert d["remedy"] is None and d["blockers"] == []


def test_ferramenta_sem_pre_condicao_esta_disponivel_e_diz_isso():
    r = _zerado()
    d = r.availability("compute")
    assert d["available"] is True and d["blockers"] == []
    assert "satisfeit" in d["reason"]


def test_ferramenta_desconhecida_nao_inventa_remedio():
    d = _zerado().availability("ferramenta_que_nao_existe")
    assert d["available"] is False
    assert d["reason"] == "ferramenta desconhecida"
    assert d["remedy"] is None


# ===  o catalogo carrega a explicacao, sem quebrar quem ja o lia  ===========

def test_o_catalogo_ganha_motivo_sem_perder_o_campo_antigo():
    r = _zerado()
    catalogo = r.list()
    assert catalogo, "o registro não pode estar vazio"
    for t in catalogo:
        # o contrato antigo continua de pé
        for antigo in ("name", "capability", "description", "risk",
                       "scope", "available"):
            assert antigo in t, f"o campo '{antigo}' sumiu do catálogo"
        # e o novo vem junto
        for novo in ("reason", "remedy", "blockers"):
            assert novo in t


def test_toda_ferramenta_indisponivel_tem_remedio_nao_vazio():
    """Um 'não' sem saída é um beco. Nenhuma pode ficar sem caminho."""
    for t in _zerado().list():
        if not t["available"]:
            assert t["remedy"], f"{t['name']} diz não e não diz como destravar"
            assert t["blockers"], f"{t['name']} não declara o que bloqueia"


def test_ferramenta_disponivel_nao_carrega_remedio_inutil():
    for t in _zerado().list():
        if t["available"]:
            assert t["remedy"] is None and t["blockers"] == []


def test_o_detector_de_precondicao_olha_o_schema_e_nao_o_nome():
    """Adivinhar pelo nome quebraria numa ferramenta futura."""
    r = _zerado()
    from backend.tools.registry import Tool
    com_caminho = Tool(name="x", capability="CAN_READ_FILES", description="d",
                       executor=lambda a: None, input_schema={"path": "str"})
    sem_caminho = Tool(name="y", capability="CAN_READ_FILES", description="d",
                       executor=lambda a: None, input_schema={"expr": "str"})
    assert r._needs_path(com_caminho) is True
    assert r._needs_path(sem_caminho) is False


# ===  observabilidade  =======================================================

def test_o_endpoint_responde_a_pergunta_por_ferramenta():
    _zerado()
    r = client.get("/tools/read_file/availability")
    assert r.status_code == 200
    d = r.json()
    assert d["tool"] == "read_file" and d["available"] is False
    assert d["remedy"]


def test_o_endpoint_de_catalogo_continua_servindo_a_lista():
    r = client.get("/tools")
    assert r.status_code == 200
    tools = r.json()["tools"]
    assert tools and all("reason" in t for t in tools)


def test_o_endpoint_nao_exige_dono_para_PERGUNTAR_o_que_da_para_fazer():
    """Consultar capacidade é leitura; executar é que exige o dono."""
    assert client.get("/tools/compute/availability").status_code == 200
