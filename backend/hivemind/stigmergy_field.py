"""Estigmergia vetorial — comunicação pelo ambiente, sem mensagens.

Na natureza, formigas quase nunca "conversam": elas alteram o ambiente e as
outras percebem. Aqui cada local (nó do conhecimento) carrega um vetor de
feromônios; bots marcam locais e outros percebem e agem. Os vetores evaporam
e se propagam pelas conexões — sinal distribuído, altamente escalável.
"""
from __future__ import annotations


# ── Estigmergia vetorial: cada local carrega um vetor de feromônios ──
# Dimensões: sucesso, perigo, novidade, complexidade, confiabilidade.
_DIMENSIONS = ("success", "danger", "novelty", "complexity", "reliability")


class PheromoneVectorField:
    """Campo vetorial de feromônios ancorado no ambiente (estigmergia).

    Bots não trocam mensagens: eles MARCAM locais (nós do conhecimento) e
    outros PERCEBEM essas marcas e agem. Os vetores evaporam com o tempo e
    se PROPAGAM para locais vizinhos, espalhando o sinal pela rede.
    """

    def __init__(self, decay: float = 0.05) -> None:
        self._field: dict[str, dict[str, float]] = {}
        self._neighbors: dict[str, set[str]] = {}
        self._decay = decay

    def mark_environment(
        self, location: str, dimension: str, intensity: float
    ) -> None:
        """Deposita feromônio numa dimensão de um local do ambiente."""
        if dimension not in _DIMENSIONS:
            return
        vec = self._field.setdefault(
            location, {d: 0.0 for d in _DIMENSIONS})
        vec[dimension] = min(1.0, vec[dimension] + intensity)

    def sense_environment(self, location: str) -> dict[str, float]:
        """Percebe o vetor de feromônios num local."""
        return dict(self._field.get(location,
                                    {d: 0.0 for d in _DIMENSIONS}))

    def connect(self, a: str, b: str) -> None:
        """Liga dois locais para permitir propagação de feromônio."""
        self._neighbors.setdefault(a, set()).add(b)
        self._neighbors.setdefault(b, set()).add(a)

    def propagate_pheromone(self, factor: float = 0.3) -> None:
        """Espalha uma fração do feromônio de cada local aos vizinhos."""
        additions: dict[str, dict[str, float]] = {}
        for loc, vec in self._field.items():
            for nb in self._neighbors.get(loc, ()):
                tgt = additions.setdefault(
                    nb, {d: 0.0 for d in _DIMENSIONS})
                for d in _DIMENSIONS:
                    tgt[d] += vec[d] * factor
        for loc, add in additions.items():
            vec = self._field.setdefault(
                loc, {d: 0.0 for d in _DIMENSIONS})
            for d in _DIMENSIONS:
                vec[d] = min(1.0, vec[d] + add[d])

    def evaporate(self) -> None:
        """Reduz todos os feromônios (esquecimento natural)."""
        for vec in self._field.values():
            for d in _DIMENSIONS:
                vec[d] = round(max(0.0, vec[d] - self._decay), 4)
