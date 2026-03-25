from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_demo_bootstrap_endpoint_returns_ready_payload(monkeypatch) -> None:
    class FakeYoutubeProvider:
        def collect(self, _: str) -> list[dict]:
            return [
                {
                    "source_type": "youtube",
                    "url": f"https://youtube.com/watch?v={uuid4().hex[:8]}",
                    "title": "Demo transcript source",
                    "author": "Clinician",
                    "published_at": None,
                    "transcript_text": "raw transcript",
                    "raw_content": "00:01 Frequent urination can happen. 00:05 See a doctor for red flags.",
                    "cleaned_content": "Frequent urination can happen for several reasons. See a doctor for red flags.",
                    "reliability_score": 0.64,
                    "ingestion_status": "ingested",
                }
            ]

    class FakeManualProvider:
        def collect(self, _: str) -> list[dict]:
            return [
                {
                    "source_type": "manual",
                    "url": f"https://example.org/{uuid4().hex[:8]}",
                    "title": "Demo manual source",
                    "author": "Medical board",
                    "published_at": None,
                    "transcript_text": None,
                    "raw_content": "Medical guidance raw content",
                    "cleaned_content": "Medical guidance confirms red flags and symptom context.",
                    "reliability_score": 0.91,
                    "ingestion_status": "ingested",
                }
            ]

    monkeypatch.setattr("app.api.routes.YouTubeTranscriptProvider", FakeYoutubeProvider)
    monkeypatch.setattr("app.api.routes.ManualSourceProvider", FakeManualProvider)
    monkeypatch.setattr("app.services.openai_gateway.OpenAIGateway.generate_brief_json", lambda self, _: None)
    monkeypatch.setattr("app.services.openai_gateway.OpenAIGateway.generate_draft_json", lambda self, _brief, _pack: None)
    monkeypatch.setattr("app.services.openai_gateway.OpenAIGateway.generate_image_variants", lambda self, _: None)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/demo/bootstrap",
            json={
                "topic_query": "frequent urination with cystitis",
                "audience": "general audience",
                "cluster_name": f"Demo Cluster Test {uuid4().hex[:6]}",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["topic_id"]
        assert payload["article_id"]
        assert payload["brief_id"]
        assert payload["sources_collected"] >= 1
