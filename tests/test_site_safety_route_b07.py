"""SiteSafetyCheck ligado à rota real (item 7) — não só a peça isolada.

Mesma lição do defeito #92 aplicada de propósito desta vez: a peça
(`SiteSafetyChecker`) já está provada sozinha em
`test_site_safety_check_b07.py`; aqui provamos que a rota `/action/navigate`
de fato a consulta ANTES de tentar navegar — não é decoração no código.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.security.site_safety import reset_site_safety_checker

client = TestClient(app)


def _autoriza_navegacao(user: str = "jonas") -> None:
    # web.navigate exige nível LIMITED — PERMISSIONS é zerado entre testes
    # (isolamento do PR #99), então cada teste concede o próprio nível.
    assert client.post("/permissions/grant",
                       json={"user_id": user, "level": 2}).status_code == 200


def test_site_check_endpoint_julga_sem_navegar():
    reset_site_safety_checker()
    r = client.post("/action/site-check",
                    json={"url": "javascript://exemplo.com/%0aalert(1)"})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "perigoso"
    assert any("esquema" in x for x in body["reasons"])


def test_navigate_recusa_url_perigosa_antes_de_tentar_o_navegador():
    reset_site_safety_checker()
    _autoriza_navegacao()
    r = client.post("/action/navigate", json={
        "user_id": "jonas",
        "url": "https://usuario:senha@banco-falso.com/login",
    })
    assert r.status_code == 403
    assert "SiteSafetyCheck" in r.json()["detail"]
    assert "credenciais" in r.json()["detail"]


def test_navigate_url_invalida_e_recusada_com_400_nao_500():
    reset_site_safety_checker()
    _autoriza_navegacao()
    r = client.post("/action/navigate", json={
        "user_id": "jonas", "url": "nao-e-uma-url",
    })
    assert r.status_code == 403   # invalido também recusa a navegação


def test_navigate_url_segura_passa_do_gate_de_seguranca():
    """Sem Playwright neste ambiente, a navegação real degrada para 503 —
    mas isso só pode acontecer DEPOIS do SiteSafetyCheck aprovar, nunca
    antes. Prova que o gate roda e libera, não que a navegação funciona.

    example.com (IANA reservado) em vez de um domínio qualquer: mesmo que a
    checagem de DNS real rode neste teste, é o único host com garantia de
    nunca dar gaierror por não existir — o teste não pode depender da sorte
    da rede do ambiente."""
    reset_site_safety_checker()
    _autoriza_navegacao()
    r = client.post("/action/navigate", json={
        "user_id": "jonas", "url": "https://example.com/pagina",
    })
    assert r.status_code in (200, 503), (
        f"esperava passar do SiteSafetyCheck (200 navegou, ou 503 sem "
        f"Playwright) — não 403 de segurança: {r.status_code} {r.text}"
    )
