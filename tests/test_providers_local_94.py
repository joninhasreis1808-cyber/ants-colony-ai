"""T7 (9.4): LocalProvider sem urllib síncrono; degrada e tem caminho async."""
import asyncio
from pathlib import Path
from backend.providers.local_provider import LocalProvider

SRC = Path(__file__).resolve().parents[1] / "backend/providers/local_provider.py"


def test_sem_urllib_usa_httpx():
    code = SRC.read_text(encoding="utf-8")
    assert "urllib" not in code
    assert "httpx" in code


def test_degrada_para_regras_sem_ollama():
    lp = LocalProvider(ollama_url="http://127.0.0.1:1")   # ninguém escutando
    assert lp.detect_backend() == "rules"
    out = lp.generate("o que é uma colmeia")
    assert "[modo local]" in out


def test_caminho_async_nao_bloqueia():
    lp = LocalProvider(ollama_url="http://127.0.0.1:1")
    out = asyncio.run(lp.agenerate("o que é uma colmeia"))
    assert "[modo local]" in out
