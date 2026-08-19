"""T6 (9.4): fonte única de saúde (ants:health), sem polls duplicados."""
from pathlib import Path
WEB = Path(__file__).resolve().parents[2] / "web"


def test_footer_ouve_ants_health_sem_fetch_proprio():
    f = (WEB / "js" / "health_footer.js").read_text(encoding="utf-8")
    assert "ants:health" in f
    assert 'fetch(api + "/health"' not in f     # não faz mais fetch próprio


def test_app_e_a_fonte_unica_e_pausa_em_background():
    a = (WEB / "js" / "app.js").read_text(encoding="utf-8")
    assert 'CustomEvent("ants:health"' in a
    assert "document.hidden" in a and "beforeunload" in a
