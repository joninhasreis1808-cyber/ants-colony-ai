"""Agente arquiteto — cuida da saúde da arquitetura, nunca do usuário.

Analisa métricas do sistema (latência, memória, acoplamento, erros) e
PROPÕE melhorias — nunca as aplica sozinho. Toda proposta é pensada para
passar por benchmark antes de qualquer adoção. Melhoria contínua, com
prudência.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Proposal:
    area: str
    suggestion: str
    expected_gain: str


class ArchitectAgent:
    """Diagnostica a arquitetura e sugere melhorias (sem aplicá-las)."""

    def analyze_architecture(self, metrics: dict) -> dict:
        """Relatório de saúde a partir de métricas do sistema."""
        issues = []
        if metrics.get("avg_latency", 0) > 1.0:
            issues.append("latência alta")
        if metrics.get("ram_mb", 0) > 250:
            issues.append("uso de memória elevado")
        if metrics.get("error_rate", 0) > 0.1:
            issues.append("taxa de erros acima do ideal")
        return {"healthy": not issues, "issues": issues}

    def propose_improvements(self, metrics: dict) -> list[Proposal]:
        """Gera propostas de melhoria conforme os problemas achados."""
        report = self.analyze_architecture(metrics)
        proposals: list[Proposal] = []
        for issue in report["issues"]:
            if "latência" in issue:
                proposals.append(Proposal(
                    "desempenho", "adicionar cache na camada quente",
                    "menor latência"))
            elif "memória" in issue:
                proposals.append(Proposal(
                    "memória", "podar bots ociosos mais cedo",
                    "menor uso de RAM"))
            elif "erros" in issue:
                proposals.append(Proposal(
                    "robustez", "reforçar validação nas entradas",
                    "menos falhas"))
        return proposals

    def simulate_change(self, proposal: Proposal) -> dict:
        """Estimativa (sandbox) do efeito de uma proposta, sem aplicá-la."""
        return {"proposal": proposal.suggestion, "safe": True,
                "note": "requer benchmark antes de adotar"}
