"""T8 (9.4): contador de testes real via /health, sem número fixo."""
from pathlib import Path
from fastapi.testclient import TestClient
from backend.api.main import app, _count_tests
WEB = Path(__file__).resolve().parents[2] / "web"
client = TestClient(app)


def test_health_conta_testes_real():
    n = client.get("/health").json().get("tests")
    assert isinstance(n, int) and n > 0 and n == _count_tests()


def test_index_sem_numero_fixo():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "529" not in html and "534 testes" not in html
    for i in ("test-count", "stat-tests", "chip-tests"):
        assert f'id="{i}"' in html
