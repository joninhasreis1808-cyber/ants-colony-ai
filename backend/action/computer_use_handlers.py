"""Handlers das capacidades do Computer Use.

Extraídos de `computer_use.py` para manter cada arquivo enxuto. Cada função
recebe o escopo (Path), os parâmetros e devolve um Result. A validação de
escopo e whitelist vive aqui, junto das operações.
"""
from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

COMMAND_WHITELIST = frozenset({
    "ls", "cat", "echo", "pwd", "date", "wc", "head", "tail",
    "grep", "find", "python3", "python", "git",
})


@dataclass
class Result:
    ok: bool
    output: str = ""
    error: str = ""


def safe_path(scope: Path, raw: str) -> Path | None:
    """Resolve `raw` sob `scope` e recusa qualquer coisa fora dele."""
    try:
        target = (scope / raw).resolve()
    except (ValueError, OSError):
        return None
    if scope == target or scope in target.parents:
        return target
    return None


def read_file(scope: Path, params: dict) -> Result:
    path = safe_path(scope, params.get("path", ""))
    if path is None:
        return Result(False, error="fora do escopo permitido")
    if not path.is_file():
        return Result(False, error="arquivo não encontrado")
    return Result(True, output=path.read_text(encoding="utf-8")[:20000])


def write_file(scope: Path, params: dict) -> Result:
    path = safe_path(scope, params.get("path", ""))
    if path is None:
        return Result(False, error="fora do escopo permitido")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(params.get("content", "")), encoding="utf-8")
    return Result(True, output=f"escrito: {path.name}")


def list_dir(scope: Path, params: dict) -> Result:
    path = safe_path(scope, params.get("path", "."))
    if path is None or not path.is_dir():
        return Result(False, error="diretório inválido/fora do escopo")
    return Result(True, output="\n".join(sorted(p.name for p in path.iterdir())))


def search_files(scope: Path, params: dict) -> Result:
    pattern = params.get("pattern", "*")
    matches = [str(p.relative_to(scope))
               for p in scope.rglob(pattern)][:100]
    return Result(True, output="\n".join(matches))


def execute_cmd(scope: Path, params: dict, timeout: float) -> Result:
    parts = shlex.split(params.get("command", ""))
    if not parts or parts[0] not in COMMAND_WHITELIST:
        return Result(False, error=f"comando não permitido: "
                                   f"{parts[0] if parts else ''}")
    try:
        proc = subprocess.run(parts, cwd=scope, capture_output=True,
                              text=True, timeout=timeout)
        return Result(proc.returncode == 0, output=proc.stdout[:10000],
                      error=proc.stderr[:2000])
    except subprocess.TimeoutExpired:
        return Result(False, error="timeout")


def clipboard(scope: Path, params: dict) -> Result:
    return Result(True, output=str(params.get("text", "")))
