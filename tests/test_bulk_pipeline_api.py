from fastapi.testclient import TestClient

from app.main import app


def test_bulk_pipeline_run_endpoint_returns_batch_summary() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/pipeline/run-bulk",
            json={
                "topic_queries": [
                    "frequent urination with cystitis",
                    "burning during urination",
                ],
                "audience": "general audience",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["requested"] == 2
        assert payload["completed"] == 2
        assert len(payload["results"]) == 2
