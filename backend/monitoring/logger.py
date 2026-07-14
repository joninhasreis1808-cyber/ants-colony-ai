"""Logs estruturados em JSON (≤40 linhas, sem dependências).

Uma linha JSON por evento — fácil de indexar (Loki, ELK) e de ler em dev.
"""
from __future__ import annotations

import json
import sys
import time
from typing import Any


class StructuredLogger:
    def __init__(self, service: str = "ants", stream=None) -> None:
        self.service = service
        self.stream = stream or sys.stdout

    def log(self, level: str, msg: str, **fields: Any) -> dict:
        record = {"ts": round(time.time(), 3), "level": level,
                  "service": self.service, "msg": msg, **fields}
        try:
            self.stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            self.stream.flush()
        except Exception:
            pass
        return record

    def info(self, msg: str, **f: Any) -> dict:
        return self.log("info", msg, **f)

    def warning(self, msg: str, **f: Any) -> dict:
        return self.log("warning", msg, **f)

    def error(self, msg: str, **f: Any) -> dict:
        return self.log("error", msg, **f)
