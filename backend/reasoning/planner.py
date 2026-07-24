"""Planejador determinístico — raciocínio puro que decompõe um objetivo.

Quando o pedido é "faça um plano / N passos / como organizar…", a colônia não
precisa de web nem de fato inato: ela RACIOCINA um plano ordenado, real e
adaptado ao objetivo. Offline, determinístico, honesto (source `reasoning`).

Não inventa fatos externos — apenas estrutura passos coerentes a partir do que
o próprio objetivo pede. Reconhece alguns domínios comuns (organizar/limpar,
estudar/aprender, pesquisar/comparar) e tem uma decomposição genérica sensata.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_TRIGGER = re.compile(
    r"\b(plano|planeje|planejar|passos?|como (organizar|fazer|criar|"
    r"aprender|estudar|melhorar)|organiz\w+|monte)\b", re.I)
_NUM = re.compile(r"(\d+)\s*passos?", re.I)


@dataclass
class Plan:
    """Um plano raciocinado, com passos ordenados e rastreáveis."""

    goal: str
    steps: list[str] = field(default_factory=list)
    confidence: float = 0.6

    @property
    def answer(self) -> str:
        head = "Plano raciocinado (sem fontes externas):"
        body = "\n".join(f"{i+1}. {s}" for i, s in enumerate(self.steps))
        return f"{head}\n{body}"

    def to_dict(self) -> dict:
        return {"goal": self.goal, "steps": self.steps,
                "confidence": self.confidence, "kind": "plan"}


# Modelos de passos por domínio (adaptados ao objetivo, não genéricos vazios).
def _steps_organizar(_: str) -> list[str]:
    return [
        "Fazer um inventário do que existe e agrupar por tipo/extensão.",
        "Criar categorias claras (ex.: Documentos, Imagens, Instaladores).",
        "Mover cada item para sua categoria e remover duplicados/obsoletos.",
        "Definir uma rotina de manutenção (revisar e limpar periodicamente).",
    ]


def _steps_estudar(_: str) -> list[str]:
    return [
        "Definir o objetivo de aprendizado e o nível atual.",
        "Reunir fontes confiáveis e dividir o tema em blocos.",
        "Estudar em ciclos curtos com prática ativa e revisão espaçada.",
        "Avaliar o progresso e ajustar o ritmo conforme os resultados.",
    ]


def _steps_pesquisar(_: str) -> list[str]:
    return [
        "Delimitar a pergunta e os critérios de comparação.",
        "Coletar dados de fontes independentes e registrar as origens.",
        "Comparar item a item, anotando prós, contras e incertezas.",
        "Concluir com uma recomendação justificada e as limitações.",
    ]


def _steps_generico(goal: str) -> list[str]:
    alvo = goal.strip().rstrip("?.").lower()
    return [
        f"Esclarecer o objetivo e o resultado esperado de: {alvo}.",
        "Levantar os recursos, restrições e dependências envolvidos.",
        "Executar em partes pequenas, verificando cada etapa.",
        "Revisar o resultado e registrar o que funcionou (aprendizado).",
    ]


class TaskPlanner:
    """Reconhece pedidos de plano e devolve um plano raciocinado."""

    def plan(self, goal: str) -> Plan | None:
        if not goal or not _TRIGGER.search(goal):
            return None
        low = goal.lower()
        if any(w in low for w in ("organiz", "limpar", "arrumar", "pasta")):
            steps = _steps_organizar(goal)
        elif any(w in low for w in ("estud", "aprend", "curso")):
            steps = _steps_estudar(goal)
        elif any(w in low for w in ("pesquis", "compar", "avali")):
            steps = _steps_pesquisar(goal)
        else:
            steps = _steps_generico(goal)
        m = _NUM.search(goal)
        if m:
            n = max(1, min(8, int(m.group(1))))
            steps = self._resize(steps, n, goal)
        return Plan(goal=goal, steps=steps)

    def _resize(self, steps: list[str], n: int, goal: str) -> list[str]:
        """Ajusta o plano ao número de passos pedido, sem enchimento vazio."""
        if len(steps) == n:
            return steps
        if len(steps) > n:
            # funde os últimos passos para caber, preservando o fechamento
            head = steps[:n - 1]
            tail = "; ".join(s.rstrip(".").lower() for s in steps[n - 1:])
            return head + [f"Por fim, {tail}."]
        # precisa de mais passos: acrescenta verificação/registro concretos
        extra = [
            "Validar o resultado parcial antes de seguir.",
            "Documentar decisões para repetir com menos esforço depois.",
            "Automatizar o que for repetitivo.",
        ]
        return (steps + extra)[:n]
