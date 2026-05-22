"""Optional GET /api/v1/retrieval/metrics-export (disabled by default)."""

from fastapi.testclient import TestClient

from app.main import app


def test_metrics_export_returns_404_when_disabled():
    client = TestClient(app)
    response = client.get("/api/v1/retrieval/metrics-export")
    assert response.status_code == 404
