"""Composição de resposta com tom consistente (9.1 · C.2) — sem alucinar.

Camada final que transforma o resultado bruto (fato/busca/cálculo/raciocínio)
numa resposta fluente, clara e com tom próprio e CONSISTENTE do Ant's. Não gera
texto do nada: apenas organiza, conecta e apresenta bem o que a colônia
realmente apurou, citando a proveniência. Templates por tipo de resposta.
Puro stdlib.
"""
from __future__ import annotations

# Rótulo humano da proveniência (o "selo" em linguagem natural).
_PROV_LABEL = {
    "computation": "cálculo exato", "knowledge_base": "base de conhecimento",
    "seed_knowledge": "conhecimento próprio", "memory": "memória",
    "web_search": "busca na web", "reasoning": "raciocínio próprio",
    "analogy": "analogia com um caso anterior", "none": "sem fonte",
}


def _prov(source: str, n_sources: int = 0) -> str:
    label = _PROV_LABEL.get(source, source or "—")
    if source == "web_search" and n_sources:
        return f"{label} ({n_sources} fonte(s))"
    return label


class ResponseComposer:
    """Monta a resposta final, fluente e honesta, por tipo."""

    def definition(self, term: str, definition: str, extras: str = "",
                   source: str = "knowledge_base") -> str:
        base = definition.strip()
        if extras:
            base += f" {extras.strip()}"
        return f"{base}\n\n— {_prov(source)}."

    def computation(self, value: str, steps: list[str] | None = None) -> str:
        out = f"O resultado é {value}."
        if steps:
            out += "\n\nComo cheguei: " + "; ".join(steps[-3:])
        return out + f"\n\n— {_prov('computation')}."

    def comparison(self, a: str, b: str, points: list[str]) -> str:
        lines = "\n".join(f"• {p}" for p in points if p)
        return f"Comparando {a} e {b}:\n{lines}\n\n— {_prov('reasoning')}."

    def steps(self, title: str, steps: list[str],
              source: str = "reasoning") -> str:
        body = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        return f"{title}\n{body}\n\n— {_prov(source)}."

    def web(self, answer: str, n_sources: int, domains: list[str] | None = None) -> str:
        out = answer.strip()
        if domains:
            out += "\n\nFontes: " + ", ".join(domains[:3])
        return out + f"\n\n— {_prov('web_search', n_sources)}."

    def limitation(self, gap: str = "") -> str:
        base = ("Não encontrei base suficiente para afirmar isso com honestidade. "
                "Prefiro dizer que não sei a inventar.")
        if gap:
            base += f" (o que faltou: {gap})"
        return base + f"\n\n— {_prov('none')}."

    def compose(self, kind: str, payload: dict) -> str:
        """Despacha para o template do tipo, sempre citando a proveniência."""
        p = payload or {}
        if kind == "definition":
            return self.definition(p.get("term", ""), p.get("definition", ""),
                                   p.get("extras", ""), p.get("source", "knowledge_base"))
        if kind == "computation":
            return self.computation(p.get("value", ""), p.get("steps"))
        if kind == "steps":
            return self.steps(p.get("title", ""), p.get("steps", []),
                             p.get("source", "reasoning"))
        if kind == "web":
            return self.web(p.get("answer", ""), p.get("n_sources", 0),
                            p.get("domains"))
        if kind == "limitation":
            return self.limitation(p.get("gap", ""))
        return (p.get("answer", "") or "").strip()


_INSTANCE: ResponseComposer | None = None


def get_composer() -> ResponseComposer:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = ResponseComposer()
    return _INSTANCE
