"""Testes das castas-base + formações da Rainha (7.2 · Bloco B)."""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.hivemind.castes_base import BASES, base_of, legacy_of, name_for
from backend.hivemind.formation import Queen

client = TestClient(app)


def test_seis_castas_base_e_compatibilidade():
    assert set(BASES) == {"exploradores", "construtores", "coletores",
                          "costureiros", "operarias", "soldados"}
    # camada de compatibilidade base ⇄ antiga (não quebra testes/rotas)
    assert legacy_of("exploradores") == "explorer"
    assert legacy_of("soldados") == "soldier"
    assert base_of("explorer") == "exploradores"
    assert base_of("soldier") == "soldados"


def test_formacao_pesquisa_poe_soldado_na_frente():
    q = Queen()
    f = q.form("pesquisar X e comparar com Y", paths=2)
    assert f.bots[0].caste == "soldados"          # soldado à frente
    assert f.counts()["exploradores"] == 2        # um por caminho (paralelo)
    assert "coletores" in f.counts()              # coletor compila


def test_formacao_por_tipo_de_missao():
    q = Queen()
    assert "construtores" in q.form("crie um app de notas").counts()
    assert "operarias" in q.form("clicar no botão enviar").counts()


def test_nome_de_missao_limita_escopo():
    # cada bot recebe um handle único → chama-se ESTE, não a casta inteira
    assert name_for("exploradores", 0) == "Explorador Alfa"
    assert name_for("exploradores", 1) == "Explorador Beta"
    q = Queen()
    f = q.form("pesquisar algo", paths=3)
    handles = [b.handle for b in f.bots if b.caste == "exploradores"]
    assert len(handles) == len(set(handles)) == 3


def test_release_nunca_abaixo_de_um():
    q = Queen()
    f = q.form("pesquisar algo", paths=3)
    assert q.release(f, "exploradores") is True      # 3→2
    assert q.release(f, "exploradores") is True      # 2→1
    assert q.release(f, "exploradores") is False     # trava em 1
    assert f.counts()["exploradores"] == 1
    assert q.release(f, "soldados") is False         # já estava em 1


def test_reinforce_acelera():
    q = Queen()
    f = q.form("pesquisar algo")
    before = f.counts().get("exploradores", 0)
    q.reinforce(f, "exploradores")
    assert f.counts()["exploradores"] == before + 1


def test_soldado_sacrificio_isola_ameaca():
    q = Queen()
    f = q.form("navegar em um site")
    report = q.scout_safety(f, "rm -rf / && format disk")
    assert report["threat"] is True
    assert report["sacrifice"] is True
    assert report["advance_allowed"] is False
    # rota segura libera o avanço
    safe = q.form("navegar em um site")
    ok = q.scout_safety(safe, "abrir a página inicial")
    assert ok["advance_allowed"] is True


def test_coletor_compila_antes_de_concluir_e_descarte_so_apos():
    from backend.hivemind.formation import FormationRegistry
    reg = FormationRegistry()
    f = reg.create("pesquisar algo")
    assert reg.discard(f.id) is False        # não pode descartar antes
    reg.queen.compile_and_send(f)
    assert f.compiled is True and f.status == "done"
    assert reg.discard(f.id) is True         # agora sim


def test_endpoints_formacao():
    created = client.post("/hive/formation",
                          json={"goal": "pesquisar algo", "paths": 2}).json()
    fid = created["id"]
    assert client.get("/hive/formations").status_code == 200
    # reinforce
    r = client.post(f"/hive/formation/{fid}/reinforce",
                    json={"caste": "exploradores"})
    assert r.status_code == 200 and r.json()["formation"]["counts"]["exploradores"] == 3
    # release trava em 1
    for _ in range(5):
        client.post(f"/hive/formation/{fid}/release",
                    json={"caste": "exploradores"})
    final = client.get("/hive/formations").json()["formations"]
    mine = [f for f in final if f["id"] == fid][0]
    assert mine["counts"]["exploradores"] == 1
    # X só após concluir
    assert client.delete(f"/hive/formation/{fid}").status_code == 409
    client.post(f"/hive/formation/{fid}/complete")
    assert client.delete(f"/hive/formation/{fid}").status_code == 200
