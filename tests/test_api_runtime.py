from fastapi.testclient import TestClient

from app.main import app


def test_settings_endpoint() -> None:
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
