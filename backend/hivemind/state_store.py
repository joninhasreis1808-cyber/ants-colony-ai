"""Persistência de estado (9.12 · Passo 2) — a colônia lembra entre reinícios.

Guarda em disco, de forma OPT-IN, o que a colônia aprendeu: a memória de
experiência (B3) e o livro-razão de evolução (FASE H). Se `ANTS_STATE_DIR` não
estiver definido, tudo continua só em memória de processo (comportamento atual —
nenhum teste é afetado). Quando definido, cada mutação grava um JSON atômico.

Puro stdlib. Escrita atômica (arquivo temporário + os.replace) para nunca deixar
um arquivo meio-escrito se o processo cair no meio.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional


def state_dir() -> Optional[Path]:
    d = (os.environ.get("ANTS_STATE_DIR") or "").strip()
    return Path(d) if d else None


def state_path(name: str) -> Optional[Path]:
    """Caminho do arquivo de estado, ou None se a persistência está desligada."""
    d = state_dir()
    return (d / name) if d else None


def load_json(path: Optional[Path], default: Any) -> Any:
    if not path or not Path(path).exists():
        return default
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - arquivo corrompido → recomeça limpo
        return default


def save_json(path: Optional[Path], data: Any) -> None:
    if not path:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    # default=str: um desfecho de missão carrega snapshots ricos; se algo raro
    # não for serializável, vira texto em vez de derrubar a persistência.
    tmp.write_text(json.dumps(data, ensure_ascii=False, default=str),
                   encoding="utf-8")
    os.replace(tmp, p)          # troca atômica
