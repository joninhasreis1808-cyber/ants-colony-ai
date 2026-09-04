"""SiteSafetyCheck — a colônia julga um site ANTES de visitá-lo (item 7 do
Repertório da Colmeia, domínio novo v1-B).

"Vasculhe este site XXXX" / "verifique se este link é seguro" — a colônia
precisa de uma resposta bounded e testada para isso, sem inventar e sem
depender de API paga (I1 · custo zero: nada de Google Safe Browsing, nada
de VirusTotal — os dois exigem chave e cota).

O que este módulo REALMENTE detecta, com todas as letras (mesma disciplina
do B2 · cross_check): sinais estruturais da própria URL, determinísticos e
explicáveis. Não é antivírus — não baixa nem executa nada do site, não sabe
se o CONTEÚDO da página é malicioso. O que ele sabe: truques clássicos de
phishing que já aparecem na URL antes de qualquer requisição.

Assimetria (a mesma regra do ActionGate/cross_check/deliberação): um sinal
FRACO só pode pedir cautela (rebaixa para "suspeito"), nunca condenar
sozinho. Só sinais FORTES — esquema perigoso, credenciais embutidas na URL,
DNS que comprovadamente não resolve, ou uma assinatura já aprendida como
ameaça — resultam em "perigoso".

A checagem de DNS é opcional e best-effort: falha de rede (proxy bloqueado,
timeout, sandbox sem egress) declara "não verificável", nunca é tratada
como "o domínio não existe" — são coisas diferentes, e confundi-las seria
inventar um veredito que a colônia não tem base para dar.
"""
from __future__ import annotations

import re
import socket
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

# Só http(s) é navegável com segurança pelo corpo da colônia; qualquer outro
# esquema (javascript:, data:, file:, ftp:...) é vetor clássico de ataque.
_ALLOWED_SCHEMES = ("http", "https")

# Encurtadores conhecidos: o destino real não é verificável sem seguir o
# redirecionamento (rede) — declarado como suspeito, não como perigoso.
_SHORTENERS = ("bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd",
               "buff.ly", "cutt.ly", "rebrand.ly", "shorturl.at")

# TLDs historicamente associados a abuso por registro gratuito/anônimo — um
# sinal fraco, não uma condenação (domínios legítimos também os usam).
_SUSPECT_TLDS = (".tk", ".ml", ".ga", ".cf", ".gq", ".zip", ".mov", ".xyz")

_MAX_SUBDOMAINS = 4          # além disso, tentativa de imitar marca por camadas
_MAX_URL_LEN = 200            # URLs muito longas escondem parâmetros de rastreio/injeção


@dataclass
class SiteSafetyReport:
    """Veredito auditável — cada sinal que disparou fica escrito, nunca oculto."""

    url: str
    verdict: str = "seguro"      # seguro | suspeito | perigoso | invalido
    reasons: list[str] = field(default_factory=list)
    dns_checked: bool = False
    dns_note: str = "não verificado: checagem de rede não foi tentada"

    def to_dict(self) -> dict[str, Any]:
        return {"url": self.url, "verdict": self.verdict,
                "reasons": list(self.reasons),
                "dns_checked": self.dns_checked, "dns_note": self.dns_note}


class SiteSafetyChecker:
    """Julga uma URL pelos sinais estruturais, antes de qualquer navegação."""

    def __init__(self) -> None:
        # Assinaturas aprendidas de sites já confirmados perigosos nesta
        # instância — mesmo padrão do ImmuneSystem (aprender, não só bloquear).
        self._known_dangerous: set[str] = set()

    def learn_dangerous(self, url: str) -> None:
        """Registra um site como perigoso — toda checagem futura o reconhece."""
        host = self._host_of(url)
        if host:
            self._known_dangerous.add(host)

    def check(self, url: str, resolve_dns: bool = True) -> SiteSafetyReport:
        """Avalia a URL. `resolve_dns=False` pula a checagem de rede (testes)."""
        report = SiteSafetyReport(url=url)
        try:
            parsed = urlparse(url)
        except ValueError:
            report.verdict = "invalido"
            report.reasons.append("URL malformada — não dá para nem interpretar")
            return report

        host = (parsed.hostname or "").lower()
        if not parsed.scheme or not host:
            report.verdict = "invalido"
            report.reasons.append("URL sem esquema ou host reconhecível")
            return report

        forte: list[str] = []
        fraco: list[str] = []

        if parsed.scheme not in _ALLOWED_SCHEMES:
            forte.append(f"esquema '{parsed.scheme}' não é navegável com segurança "
                        f"(só http/https)")
        if parsed.username or parsed.password:
            forte.append("credenciais embutidas na URL (user:senha@host) — "
                        "truque clássico para disfarçar o host real")
        if host in self._known_dangerous:
            forte.append(f"'{host}' já foi confirmado perigoso nesta colônia")

        if self._is_ip_literal(host):
            fraco.append("host é um endereço IP literal, não um domínio")
        if "xn--" in host:
            fraco.append("domínio em punycode — possível imitação visual "
                        "(homógrafo) de outro domínio")
        partes = host.split(".")
        if len(partes) - 2 > _MAX_SUBDOMAINS:
            fraco.append(f"{len(partes) - 2} subdomínios — padrão comum de "
                        f"tentar imitar uma marca por camadas")
        if any(host == s or host.endswith("." + s) for s in _SHORTENERS):
            fraco.append("encurtador de URL conhecido — o destino real não "
                        "é verificável sem seguir o redirecionamento")
        if any(host.endswith(t) for t in _SUSPECT_TLDS):
            fraco.append(f"TLD '{host.rsplit('.', 1)[-1]}' associado a "
                        f"abuso por registro gratuito — não é condenação sozinho")
        if len(url) > _MAX_URL_LEN:
            fraco.append(f"URL com {len(url)} caracteres — incomum para um "
                        f"link legítimo digitado ou compartilhado")

        if resolve_dns:
            self._check_dns(host, report, forte)

        report.reasons = forte + fraco
        if forte:
            report.verdict = "perigoso"
        elif fraco:
            report.verdict = "suspeito"
        return report

    def _check_dns(self, host: str, report: SiteSafetyReport,
                   forte: list[str]) -> None:
        """DNS é o único sinal de rede aqui — best-effort, nunca inventa."""
        try:
            socket.setdefaulttimeout(2.0)
            socket.gethostbyname(host)
            report.dns_checked = True
            report.dns_note = "domínio resolve — host existe na rede"
        except socket.gaierror:
            # Sinal real e forte: o nome comprovadamente não resolve.
            report.dns_checked = True
            report.dns_note = "domínio NÃO resolve — não existe ou está mal configurado"
            forte.append("DNS não resolve para este domínio")
        except Exception:  # noqa: BLE001 - qualquer outra falha é da REDE, não do site
            report.dns_checked = False
            report.dns_note = ("não verificável: falha de rede ao consultar DNS "
                               "(não é o mesmo que o domínio não existir)")

    @staticmethod
    def _is_ip_literal(host: str) -> bool:
        return bool(re.fullmatch(r"(\d{1,3}\.){3}\d{1,3}", host)) or ":" in host

    @staticmethod
    def _host_of(url: str) -> str:
        try:
            return (urlparse(url).hostname or "").lower()
        except ValueError:
            return ""


_INSTANCE: SiteSafetyChecker | None = None


def get_site_safety_checker() -> SiteSafetyChecker:
    """Singleton de processo — assinaturas aprendidas valem para toda a colônia."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = SiteSafetyChecker()
    return _INSTANCE


def reset_site_safety_checker() -> None:
    """Zera o singleton — usado por testes para isolamento."""
    global _INSTANCE
    _INSTANCE = None
