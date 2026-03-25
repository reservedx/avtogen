from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_keywords_api_create_and_list() -> None:
    with TestClient(app) as client:
        cluster_payload = {
            "name": f"Cluster {uuid4().hex[:6]}",
            "slug": f"cluster-{uuid4().hex[:6]}",
            "description": "Keyword intake test cluster",
        }
        cluster_response = client.post("/api/v1/clusters", json=cluster_payload)
        assert cluster_response.status_code == 200
        cluster_id = cluster_response.json()["id"]

        keyword_payload = {
            "cluster_id": cluster_id,
            "keyword": "frequent urination cystitis",
            "search_intent": "informational",
            "priority": 80,
            "status": "active",
            "notes": "Primary SEO keyword",
        }
        keyword_response = client.post("/api/v1/keywords", json=keyword_payload)
        assert keyword_response.status_code == 200
        keyword_id = keyword_response.json()["id"]

        list_response = client.get(f"/api/v1/keywords?cluster_id={cluster_id}")
        assert list_response.status_code == 200
        payload = list_response.json()
        assert any(item["id"] == keyword_id for item in payload)
