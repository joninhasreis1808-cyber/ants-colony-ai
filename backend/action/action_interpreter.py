"""Interpretador de comando de ação (8.1 · B.1).

Transforma uma mensagem `action_device` numa intenção estruturada
`{verb, target_type, target, args, scope}` — sem inventar: só reconhece o que
os executores do 8.0 sabem fazer. Determinístico, offline, PT-BR.
"""
from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass, field

# verbo(s) → (verbo canônico, tipo de alvo, escopo exigido)
_VERB_MAP = {
    "list": ("list", "folder", "read_files"),
    "listar": ("list", "folder", "read_files"), "liste": ("list", "folder", "read_files"),
    "lista": ("list", "folder", "read_files"), "mostre": ("list", "folder", "read_files"),
    "encontre": ("search", "folder", "read_files"), "procure": ("search", "folder", "read_files"),
    "procurar": ("search", "folder", "read_files"), "busque": ("search", "folder", "read_files"),
    "buscar": ("search", "folder", "read_files"),
    "abra": ("open", "app", "run_apps"), "abrir": ("open", "app", "run_apps"),
    "abre": ("open", "app", "run_apps"), "inicie": ("open", "app", "run_apps"),
    "iniciar": ("open", "app", "run_apps"), "execute": ("open", "app", "run_apps"),
    "rode": ("open", "app", "run_apps"),
    "feche": ("close", "app", "run_apps"), "fechar": ("close", "app", "run_apps"),
    "mova": ("move", "file", "write_files"), "mover": ("move", "file", "write_files"),
    "renomeie": ("rename", "file", "write_files"), "renomear": ("rename", "file", "write_files"),
    "apague": ("delete", "file", "write_files"), "apagar": ("delete", "file", "write_files"),
    "delete": ("delete", "file", "write_files"), "exclua": ("delete", "file", "write_files"),
    "copie": ("copy", "file", "write_files"), "copiar": ("copy", "file", "write_files"),
    "organize": ("organize", "folder", "write_files"), "organizar": ("organize", "folder", "write_files"),
    "clique": ("click", "ui_element", "control_input"), "digite": ("type", "ui_element", "control_input"),
    "capture": ("screenshot", "screen", "screen_capture"), "capturar": ("screenshot", "screen", "screen_capture"),
}
_STOP = {"o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
         "na", "no", "em", "para", "minha", "meu", "meus", "minhas", "meu",
         "arquivo", "arquivos", "pasta", "app", "aplicativo", "programa", "chamado"}
_PASTAS_CONHECIDAS = {"downloads": "~/Downloads", "documentos": "~/Documents",
                      "documents": "~/Documents", "imagens": "~/Pictures",
                      "area de trabalho": "~/Desktop", "desktop": "~/Desktop"}


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c)).strip()


@dataclass
class ActionIntent:
    verb: str
    target_type: str
    target: str
    scope: str
    args: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"verb": self.verb, "target_type": self.target_type,
                "target": self.target, "scope": self.scope, "args": self.args}


class ActionInterpreter:
    """Lê o comando e devolve a intenção estruturada."""

    def interpret(self, message: str) -> ActionIntent | None:
        low = _norm(message)
        verb_key = next((v for v in _VERB_MAP if re.search(
            r"(^|\s)" + re.escape(v) + r"(\s|$)", low)), None)
        if not verb_key:
            return None
        verb, ttype, scope = _VERB_MAP[verb_key]
        rest = low.split(verb_key, 1)[1].strip()
        # URL/navegador → tipo url
        if "navegador" in rest or "url" in rest or "site" in rest:
            ttype, scope = "url", "run_apps"
        target = self._extract_target(rest, ttype)
        return ActionIntent(verb, ttype, target, scope)

    def _extract_target(self, rest: str, ttype: str) -> str:
        rest = re.sub(r"\b(no|na)\s+navegador\b", "", rest).strip()
        if ttype == "folder":
            for name, path in _PASTAS_CONHECIDAS.items():
                if name in rest:
                    return os.path.expanduser(path)
        # remove stopwords, mantém o miolo (nome do app/arquivo/pasta)
        tokens = [w for w in re.findall(r"[\w./~-]+", rest) if w not in _STOP]
        target = " ".join(tokens).strip() or rest.strip()
        if ttype == "folder" and target:
            return os.path.expanduser(target)
        return target


_INSTANCE: ActionInterpreter | None = None


def get_action_interpreter() -> ActionInterpreter:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = ActionInterpreter()
    return _INSTANCE
