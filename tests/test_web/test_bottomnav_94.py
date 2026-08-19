"""T4 (9.4): as 7 abas no bottom-nav do celular (antes só 4)."""
from pathlib import Path
import re
WEB = Path(__file__).resolve().parents[2] / "web"


def test_bottomnav_tem_as_7_abas():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    nav = re.search(r'<nav class="bottomnav">(.*?)</nav>', html, re.S)
    assert nav, "bottomnav não encontrado"
    body = nav.group(1)
    for tab in ("colony", "cognitive", "environment", "resources",
                "queen", "factory", "settings"):
        assert f'data-tab="{tab}"' in body, tab
