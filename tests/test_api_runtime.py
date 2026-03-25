from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_settings_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(settings, "use_stub_generation", True)
    monkeypatch.setattr(settings, "openai_api_key", "changeme")
    with TestClient(app) as client:
        response = client.get("/api/v1/settings")
        assert response.status_code == 200
        payload = response.json()
        assert payload["database_is_sqlite"] is True
        assert payload["use_stub_generation"] is True
        assert payload["openai_enabled"] is False


def test_metrics_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        payload = response.json()
        assert "topics_count" in payload
        assert "task_runs_count" in payload


def test_analytics_summary_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/analytics/summary")
        assert response.status_code == 200
        payload = response.json()
        assert "article_status_counts" in payload
        assert "average_quality_score" in payload
