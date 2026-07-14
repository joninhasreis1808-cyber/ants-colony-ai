"""Observador — nunca executa, apenas observa, aprende e avisa.

Monitora o ambiente em segundo plano e levanta achados úteis, sem incomodar:
"encontrei 4 duplicados", "backup atrasado 7 dias", "SSD 85% cheio". Ele
sugere; quem decide é o usuário (ou a rainha). Papel puramente consultivo.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Finding:
    kind: str          # duplicate / backup / disk / update / anomaly
    message: str
    severity: str = "info"   # info / warning / alert


class Observer:
    """Detecta anomalias e sugere melhorias sem agir."""

    def __init__(self) -> None:
        self._findings: list[Finding] = []

    def detect_anomalies(self, snapshot: dict) -> list[Finding]:
        """Analisa um retrato do ambiente e gera achados."""
        found: list[Finding] = []
        dups = snapshot.get("duplicates", 0)
        if dups:
            found.append(Finding("duplicate",
                                 f"Encontrei {dups} arquivos duplicados."))
        days = snapshot.get("backup_age_days", 0)
        if days >= 7:
            found.append(Finding("backup",
                                 f"Backup atrasado há {days} dias.",
                                 "warning"))
        disk = snapshot.get("disk_usage", 0)
        if disk >= 85:
            found.append(Finding("disk",
                                 f"Disco em {disk}% de uso.", "warning"))
        if snapshot.get("update_available"):
            found.append(Finding("update",
                                 "Há uma atualização importante disponível."))
        self._findings.extend(found)
        return found

    def suggest_improvements(self) -> list[str]:
        """Transforma achados em sugestões acionáveis."""
        tips = {"duplicate": "Posso remover os duplicados com sua permissão.",
                "backup": "Quer que eu agende um backup agora?",
                "disk": "Posso listar o que mais ocupa espaço.",
                "update": "Posso preparar a atualização para você revisar."}
        return [tips.get(f.kind, "Vale investigar.") for f in self._findings]

    def get_findings(self) -> list[dict]:
        return [{"kind": f.kind, "message": f.message,
                 "severity": f.severity} for f in self._findings]

    def clear(self) -> None:
        self._findings.clear()
