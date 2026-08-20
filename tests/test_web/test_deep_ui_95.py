"""Fase C (9.5): botão Pesquisa profunda + córtex honesto, sem tocar no legado."""
from pathlib import Path
WEB = Path(__file__).resolve().parents[2] / "web"


def test_deep_ui_integrado():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "js" / "deep_research_ui.js").read_text(encoding="utf-8")
    assert 'id="deep-btn"' in html and 'id="deep-cortex"' in html
    assert "/js/deep_research_ui.js" in html
    assert "__antDeep" in js and "ants:health" in js
    ab = (WEB / "js" / "api_bridge.js").read_text(encoding="utf-8")
    assert "__antDeep" in ab and "withFlag" in ab
    cam = (WEB / "js" / "bot_camera.js").read_text(encoding="utf-8")
    assert "exploradoras" in cam and "soldados" in cam
