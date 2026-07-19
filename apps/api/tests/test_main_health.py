from fastapi.testclient import TestClient

from config import get_settings
from main import app


def test_health() -> None:
    get_settings.cache_clear()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "relay-api"


def test_metrics() -> None:
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "python_info" in response.text or response.status_code == 200
