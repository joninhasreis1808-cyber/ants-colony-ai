"""SiteSafetyCheck (item 7 do Repertório da Colmeia) — domínio novo, sem
dependência paga: "verifique se este link é seguro" antes de navegar.

`resolve_dns=False` na maioria dos testes: o sinal de DNS é testado à parte
(mockando `socket.gethostbyname`), para não depender de rede real na suíte.
"""
from __future__ import annotations

import socket

import pytest

from backend.security.site_safety import (
    SiteSafetyChecker, get_site_safety_checker, reset_site_safety_checker,
)


@pytest.fixture(autouse=True)
def _isolada():
    reset_site_safety_checker()
    yield
    reset_site_safety_checker()


def _c() -> SiteSafetyChecker:
    return SiteSafetyChecker()


def test_url_comum_e_segura():
    r = _c().check("https://exemplo.com/pagina", resolve_dns=False)
    assert r.verdict == "seguro"
    assert r.reasons == []


def test_url_malformada_e_invalida():
    r = _c().check("http://[::1", resolve_dns=False)
    assert r.verdict == "invalido"


def test_sem_esquema_ou_host_e_invalido():
    r = _c().check("nao-e-uma-url-de-verdade", resolve_dns=False)
    assert r.verdict == "invalido"


def test_esquema_javascript_e_perigoso():
    r = _c().check("javascript:alert(1)", resolve_dns=False)
    assert r.verdict in ("perigoso", "invalido")   # sem host, cai em invalido primeiro
    r2 = _c().check("javascript://exemplo.com/%0aalert(1)", resolve_dns=False)
    assert r2.verdict == "perigoso"
    assert any("esquema" in x for x in r2.reasons)


def test_credenciais_na_url_e_perigoso():
    r = _c().check("https://usuario:senha@exemplo-falso.com/login", resolve_dns=False)
    assert r.verdict == "perigoso"
    assert any("credenciais" in x for x in r.reasons)


def test_host_ip_literal_e_so_suspeito_nao_perigoso():
    r = _c().check("http://192.168.1.1/admin", resolve_dns=False)
    assert r.verdict == "suspeito"
    assert any("IP literal" in x for x in r.reasons)


def test_punycode_e_suspeito():
    r = _c().check("https://xn--pypal-4ve.com/login", resolve_dns=False)
    assert r.verdict == "suspeito"
    assert any("punycode" in x for x in r.reasons)


def test_muitos_subdominios_e_suspeito():
    r = _c().check("https://login.secure.accounts.paypal.com.evil.ru/",
                   resolve_dns=False)
    assert r.verdict == "suspeito"
    assert any("subdomínio" in x for x in r.reasons)


def test_encurtador_conhecido_e_suspeito():
    r = _c().check("https://bit.ly/3xYzAbC", resolve_dns=False)
    assert r.verdict == "suspeito"
    assert any("encurtador" in x for x in r.reasons)


def test_tld_suspeita_e_suspeito():
    r = _c().check("https://promocao-imperdivel.tk/ganhe", resolve_dns=False)
    assert r.verdict == "suspeito"
    assert any("TLD" in x for x in r.reasons)


def test_url_muito_longa_e_suspeito():
    r = _c().check("https://exemplo.com/" + "a" * 250, resolve_dns=False)
    assert r.verdict == "suspeito"
    assert any("caracteres" in x for x in r.reasons)


def test_assimetria_muitos_sinais_fracos_juntos_nao_viram_perigoso():
    """A mesma regra do ActionGate/cross_check: sinal fraco pede cautela,
    nunca condena sozinho — mesmo empilhado."""
    r = _c().check("http://192.168.1.1.evil.tk/" + "x" * 250, resolve_dns=False)
    assert r.verdict == "suspeito", (
        "vários sinais FRACOS juntos ainda não são um sinal FORTE — "
        "escalar para 'perigoso' exigiria um sinal forte de verdade"
    )
    assert len(r.reasons) >= 2


def test_assinatura_aprendida_vira_perigoso_na_proxima_checagem():
    checker = _c()
    antes = checker.check("https://ja-visto-como-ruim.com/", resolve_dns=False)
    assert antes.verdict == "seguro"
    checker.learn_dangerous("https://ja-visto-como-ruim.com/")
    depois = checker.check("https://ja-visto-como-ruim.com/pagina2", resolve_dns=False)
    assert depois.verdict == "perigoso"
    assert any("já foi confirmado perigoso" in x for x in depois.reasons)


def test_sem_resolver_dns_fica_declarado_nao_tentado():
    r = _c().check("https://exemplo.com/", resolve_dns=False)
    assert r.dns_checked is False
    assert "não foi tentada" in r.dns_note


def test_dns_resolve_de_verdade_soma_confianca_sem_virar_reason(monkeypatch):
    monkeypatch.setattr(socket, "gethostbyname", lambda h: "93.184.216.34")
    r = _c().check("https://exemplo.com/", resolve_dns=True)
    assert r.dns_checked is True
    assert "resolve" in r.dns_note
    assert r.verdict == "seguro"


def test_dns_nao_resolve_e_um_sinal_forte_de_verdade(monkeypatch):
    def _falha(host):
        raise socket.gaierror("nao resolve")
    monkeypatch.setattr(socket, "gethostbyname", _falha)
    r = _c().check("https://dominio-que-nao-existe-xyzabc123.com/", resolve_dns=True)
    assert r.dns_checked is True
    assert r.verdict == "perigoso"
    assert any("DNS" in x for x in r.reasons)


def test_falha_de_rede_generica_nao_e_confundida_com_dominio_inexistente(monkeypatch):
    """socket.timeout/OSError de proxy bloqueado != "o domínio não existe" —
    confundir os dois seria inventar um veredito sem base."""
    def _falha(host):
        raise TimeoutError("proxy bloqueou")
    monkeypatch.setattr(socket, "gethostbyname", _falha)
    r = _c().check("https://exemplo.com/", resolve_dns=True)
    assert r.dns_checked is False
    assert "não verificável" in r.dns_note
    assert r.verdict == "seguro", (
        "uma falha de REDE não pode derrubar o veredito do site — só uma "
        "falha de NOME (gaierror) é sinal real"
    )


def test_get_site_safety_checker_e_singleton_de_processo():
    assert get_site_safety_checker() is get_site_safety_checker()


def test_singleton_aprende_e_todo_chamador_do_processo_ve():
    checker = get_site_safety_checker()
    checker.learn_dangerous("https://phishing-real.com/")
    r = get_site_safety_checker().check("https://phishing-real.com/x",
                                        resolve_dns=False)
    assert r.verdict == "perigoso"
