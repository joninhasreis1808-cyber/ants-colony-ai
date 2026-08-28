"""Planejador hierárquico (9.7 · FASE B · B2) — objetivo → TaskGraph.

Um Manus não pula direto para a ação: ele decompõe o objetivo em etapas
ordenadas, com dependências, e só então executa. Aqui a Rainha faz isso.

O planejador PRIMEIRO consulta a Cartógrafa (B1) para saber a melhor rota
disponível, e ENTÃO decompõe o objetivo no formato dessa rota — cada rota tem um
esqueleto de subtarefas próprio (cálculo é um passo só; pesquisa profunda é
planejar → explorar → compilar → verificar → sintetizar). O resultado é um
TaskGraph (DAG) pronto para o executor da missão (B5) rodar em ordem topológica.

Determinístico e offline (regras). O córtex plugável (9.5), quando presente,
apenas REFINA as descrições — nunca é obrigatório; a estrutura do plano é sempre
reproduzível.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.cognition.cartographer import Route, get_cartographer
from backend.cognition.experience import apply_experience
from backend.hivemind.task_graph import TaskGraph


@dataclass
class Plan:
    """Plano hierárquico: a rota escolhida + o grafo de subtarefas."""

    goal: str
    route: Route
    graph: TaskGraph

    def to_dict(self) -> dict:
        return {"goal": self.goal, "route": self.route.to_dict(),
                "graph": self.graph.to_dict()}


# Esqueletos de decomposição por rota. Cada tupla: (id, descrição, deps).
def _skeleton_deep_research(goal: str) -> list[tuple]:
    return [
        ("planejar", f"Rainha planeja as sub-perguntas de: {goal}", []),
        ("explorar", "Exploradoras pesquisam cada sub-pergunta na web", ["planejar"]),
        ("compilar", "Operárias compilam e deduplicam as fontes", ["explorar"]),
        ("verificar", "Soldados verificam se as evidências bastam", ["compilar"]),
        ("sintetizar", "Rainha sintetiza a resposta final com proveniência",
         ["verificar"]),
    ]


def _skeleton_web(goal: str) -> list[tuple]:
    return [
        ("buscar", f"Exploradoras buscam fontes para: {goal}", []),
        ("interpretar", "Operárias interpretam o material coletado", ["buscar"]),
        ("responder", "Rainha decide a resposta com base nas fontes",
         ["interpretar"]),
    ]


def _skeleton_reasoning(goal: str) -> list[tuple]:
    return [
        ("esclarecer", f"Esclarecer o objetivo e o resultado esperado: {goal}", []),
        ("levantar", "Levantar recursos, restrições e dependências", ["esclarecer"]),
        ("executar", "Executar em partes pequenas, verificando cada etapa",
         ["levantar"]),
        ("revisar", "Revisar o resultado e registrar o aprendizado", ["executar"]),
    ]


def _skeleton_device(goal: str) -> list[tuple]:
    return [
        ("identificar", f"Identificar o alvo do comando: {goal}", []),
        ("agir", "Soldados executam a ação com escopo verificado", ["identificar"]),
        ("confirmar", "Confirmar o resultado da ação no dispositivo", ["agir"]),
    ]


def _skeleton_single(goal: str, label: str) -> list[tuple]:
    return [("resolver", f"{label}: {goal}", [])]


_SKELETONS = {
    "deep_research": _skeleton_deep_research,
    "web_search": _skeleton_web,
    "reasoning": _skeleton_reasoning,
    "device_action": _skeleton_device,
    "computation": lambda g: _skeleton_single(g, "Cálculo exato"),
    "memory": lambda g: _skeleton_single(g, "Recuperar da memória da colônia"),
    "knowledge_base": lambda g: _skeleton_single(g, "Responder com conhecimento interno"),
}


class HierarchicalPlanner:
    """Decompõe um objetivo em um TaskGraph seguindo a melhor rota disponível."""

    def plan(self, goal: str, context: dict | None = None) -> Plan:
        routes = get_cartographer().discover(goal, context)
        apply_experience(routes, goal)          # viés da experiência (B3) na escolha
        route = get_cartographer().choose(routes)
        if route is None:                       # nada disponível → raciocínio puro
            route = [r for r in routes if r.name == "reasoning"][0]
            route.available = True
        skeleton = _SKELETONS.get(route.name, _skeleton_reasoning)(goal)
        graph = TaskGraph()
        # Confiança do nó = score REAL da rota escolhida (sinal medido, não
        # inventado). Prioridade fica neutra: não há sinal honesto por-etapa
        # ainda — o campo existe e é respeitado por quem tiver um. (FASE 1)
        route_score = route.score()
        for sid, desc, deps in skeleton:
            graph.add(sid, desc, deps, confidence=route_score)
        graph.topological_order()               # valida (sem ciclo) já no plano
        return Plan(goal=goal, route=route, graph=graph)


_INSTANCE: HierarchicalPlanner | None = None


def get_planner() -> HierarchicalPlanner:
    """Singleton de processo do planejador hierárquico."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = HierarchicalPlanner()
    return _INSTANCE
