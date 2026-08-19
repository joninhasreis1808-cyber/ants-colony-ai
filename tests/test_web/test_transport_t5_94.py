"""T5 (9.4): WebSocket primário + polling fallback, formato de evento preservado."""
from pathlib import Path
WEB = Path(__file__).resolve().parents[2] / "web"


def test_api_bridge_ws_primario_com_fallback():
    ab = (WEB / "js" / "api_bridge.js").read_text(encoding="utf-8")
    assert "new WebSocket(" in ab and "/hive/live/" in ab   # WS primário
    assert "startPolling" in ab                              # fallback polling
    assert "ants:task-tick" in ab and "ants:task-done" in ab # formato preservado
    assert "backfill" in ab.lower()                          # não perde eventos
