"""ToolRegistry (9.6 · FASE A) — o catálogo único das "mãos" da colônia.

A Mente Colmeia NUNCA chama uma ferramenta direto: pede ao registro, que valida
a capacidade e a permissão (Scope Guard) ANTES de executar. Capacidade ("sei
fazer") ≠ permissão ("posso fazer"): sem o escopo concedido, a ferramenta é
recusada com honestidade. Toda execução é auditável. Puro stdlib.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from backend.permissions.device_scopes import get_device_scopes
from backend.permissions.path_guard import get_path_guard
from backend.tools import capabilities as caps
from backend.tools import compute_tools, file_tools, write_tools


@dataclass
class Tool:
    """Uma ferramenta declarada: o que faz, o que exige, e como executar."""

    name: str
    capability: str
    description: str
    executor: Callable[[dict], Any]
    input_schema: dict = field(default_factory=dict)

    @property
    def scope(self) -> Optional[str]:
        return caps.scope_for(self.capability)

    @property
    def risk(self) -> str:
        return caps.risk_for(self.capability)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "capability": self.capability,
                "description": self.description, "input_schema": self.input_schema,
                "scope": self.scope, "risk": self.risk}


class ToolRegistry:
    """Registra ferramentas e as executa SÓ após validar capacidade+permissão."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def can_use(self, name: str) -> bool:
        """Tem a ferramenta E o escopo dela concedido agora?"""
        t = self.get(name)
        if not t:
            return False
        return not t.scope or get_device_scopes().is_granted(t.scope)

    def availability(self, name: str) -> dict[str, Any]:
        """Por que esta ferramenta pode (ou não pode) ser usada AGORA.

        `can_use` respondia sim/não e o catálogo repetia esse sim/não seco: o
        dono via cinco ferramentas indisponíveis sem nenhuma pista do motivo nem
        do que fazer a respeito. Aqui a colônia declara as duas coisas.

        E declara também a pré-condição que ficava ESCONDIDA: as ferramentas de
        arquivo passam pelo `path_guard` além do escopo. Sem pasta autorizada,
        elas apareciam como disponíveis e falhavam na hora de rodar — a colônia
        prometia o que não podia cumprir.
        """
        t = self.get(name)
        if not t:
            return {"available": False, "reason": "ferramenta desconhecida",
                    "remedy": None, "blockers": ["desconhecida"]}

        bloqueios: list[str] = []
        motivos: list[str] = []
        remedios: list[str] = []

        if t.scope and not get_device_scopes().is_granted(t.scope):
            bloqueios.append("escopo")
            motivos.append(f"o escopo '{t.scope}' não está concedido")
            remedios.append(f"conceda o escopo '{t.scope}' nas permissões")

        if self._needs_path(t) and not get_path_guard().allowed_dirs():
            bloqueios.append("pasta")
            motivos.append("nenhuma pasta foi autorizada para leitura/escrita")
            remedios.append("autorize ao menos uma pasta no guarda de caminhos")

        if not bloqueios:
            return {"available": True,
                    "reason": "escopo e pré-condições satisfeitos",
                    "remedy": None, "blockers": []}
        return {"available": False, "reason": "; ".join(motivos),
                "remedy": "; ".join(remedios), "blockers": bloqueios}

    @staticmethod
    def _needs_path(t: "Tool") -> bool:
        """A ferramenta opera sobre caminhos? (passa pelo path_guard)"""
        campos = set((t.input_schema or {}).keys())
        return bool(campos & {"path", "src", "dest", "dir"})

    def list(self) -> list[dict[str, Any]]:
        """Catálogo honesto: cada ferramenta, se está disponível E POR QUÊ.

        O `available` continua no mesmo lugar e com o mesmo significado — quem
        já lia esse campo não quebra. O que vem junto agora é o motivo e o
        caminho para destravar.
        """
        out = []
        for t in self._tools.values():
            disp = self.availability(t.name)
            out.append(dict(t.to_dict(), available=disp["available"],
                            reason=disp["reason"], remedy=disp["remedy"],
                            blockers=disp["blockers"]))
        return out

    def run(self, name: str, args: dict | None = None) -> dict[str, Any]:
        """Valida (Scope Guard) e executa; devolve resultado OU recusa honesta."""
        t = self.get(name)
        if not t:
            return {"tool": name, "allowed": False, "ok": False,
                    "reason": "ferramenta desconhecida"}
        if t.scope and not get_device_scopes().is_granted(t.scope):
            return {"tool": name, "allowed": False, "ok": False,
                    "capability": t.capability,
                    "reason": f"escopo '{t.scope}' não concedido — a colônia SABE "
                              f"fazer ({t.capability}), mas não PODE agora"}
        try:
            result = t.executor(args or {})
            return {"tool": name, "allowed": True, "ok": True,
                    "capability": t.capability, "result": result}
        except PermissionError as exc:      # 2ª guarda (ex.: path_guard)
            return {"tool": name, "allowed": False, "ok": False, "reason": str(exc)}
        except Exception as exc:             # noqa: BLE001 - erro real, não recusa
            return {"tool": name, "allowed": True, "ok": False, "reason": str(exc)}


_INSTANCE: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = ToolRegistry()
        # Ferramentas iniciais: READ-ONLY, atrás do path_guard (seguras).
        _INSTANCE.register(Tool(
            "list_dir", caps.CAP_FS_READ,
            "Lista o conteúdo de uma pasta autorizada",
            file_tools.list_dir, {"path": "string"}))
        _INSTANCE.register(Tool(
            "read_file", caps.CAP_FS_READ,
            "Lê o início de um arquivo autorizado (texto)",
            file_tools.read_file, {"path": "string"}))
        # FASE D (9.8): "mãos" que MODIFICAM — dry-run por padrão, confirm:true
        # para agir; sempre atrás do path_guard e do escopo write_files.
        _INSTANCE.register(Tool(
            "write_file", caps.CAP_FS_WRITE,
            "Escreve texto num arquivo autorizado (dry-run salvo confirm:true)",
            write_tools.write_file,
            {"path": "string", "content": "string", "confirm": "bool?"}))
        _INSTANCE.register(Tool(
            "make_dir", caps.CAP_FS_WRITE,
            "Cria uma pasta autorizada (dry-run salvo confirm:true)",
            write_tools.make_dir, {"path": "string", "confirm": "bool?"}))
        _INSTANCE.register(Tool(
            "delete_path", caps.CAP_FS_DELETE,
            "Apaga um arquivo ou pasta vazia autorizada (dry-run salvo confirm:true)",
            write_tools.delete_path, {"path": "string", "confirm": "bool?"}))
        # Cálculo exato: puro, sem escopo de device (capacidade ≠ permissão).
        _INSTANCE.register(Tool(
            "compute", caps.CAP_COMPUTE,
            "Resolve uma expressão aritmética exata (offline, sem eval)",
            compute_tools.compute, {"expression": "string"}))
    return _INSTANCE
