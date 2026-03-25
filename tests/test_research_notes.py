from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.services.facts import ResearchNoteExtractor


def test_research_note_extractor_classifies_multiple_fact_types() -> None:
    rows = ResearchNoteExtractor().extract_rows(
        [
            {
                "id": uuid4(),
                "source_type": "youtube",
                "url": "https://youtube.com/watch?v=test",
                "title": "Symptoms and red flags",
                "reliability_score": 0.72,
                "cleaned_content": (
                    "Frequent urination is a common symptom in urinary tract problems. "
                    "Fever or blood in urine are urgent red flags and should prompt medical review. "
                    "Inflammation can cause the urge to urinate more often than usual."
                ),
            }
        ]
    )
    fact_types = {row["fact_type"] for row in rows}
    assert "symptom" in fact_types
    assert "red_flag" in fact_types
    assert "cause" in fact_types


def test_collect_sources_extracts_and_lists_research_notes(monkeypatch) -> None:
    class FakeYoutubeProvider:
        def collect(self, _: str) -> list[dict]:
            return [
                {
                    "source_type": "youtube",
                    "url": f"https://youtube.com/watch?v={uuid4().hex[:8]}",
                    "title": "Cystitis symptoms overview",
                    "author": "Clinician",
                    "published_at": None,
                    "transcript_text": "raw transcript",
                    "raw_content": "00:01 Frequent urination is a common symptom. Fever means urgent medical review.",
                    "cleaned_content": (
                        "Frequent urination is a common symptom when bladder irritation is present. "
                        "Fever means urgent medical review when urinary symptoms are getting worse."
                    ),
                    "reliability_score": 0.62,
                    "ingestion_status": "ingested",
                }
            ]

    class FakeManualProvider:
        def collect(self, _: str) -> list[dict]:
            return []

    monkeypatch.setattr("app.api.routes.YouTubeTranscriptProvider", FakeYoutubeProvider)
    monkeypatch.setattr("app.api.routes.ManualSourceProvider", FakeManualProvider)

    with TestClient(app) as client:
        cluster_response = client.post(
            "/api/v1/clusters",
            json={
                "name": f"Cluster {uuid4().hex[:6]}",
                "slug": f"cluster-{uuid4().hex[:6]}",
                "description": "Research notes test",
            },
        )
        cluster_id = cluster_response.json()["id"]
        topic_response = client.post(
            "/api/v1/topics",
            json={
                "cluster_id": cluster_id,
                "working_title": "Frequent urination with cystitis",
                "target_query": "frequent urination with cystitis",
                "audience": "general audience",
                "content_type": "blog_post",
            },
        )
        topic_id = topic_response.json()["id"]

        collect_response = client.post(f"/api/v1/topics/{topic_id}/collect-sources")
        assert collect_response.status_code == 200
        assert collect_response.json()["research_notes_extracted"] >= 2

        notes_response = client.get(f"/api/v1/topics/{topic_id}/research-notes")
        assert notes_response.status_code == 200
        notes_payload = notes_response.json()
        assert len(notes_payload) >= 2
        assert any(note["fact_type"] == "red_flag" for note in notes_payload)

        extract_response = client.post(f"/api/v1/topics/{topic_id}/extract-research-notes")
        assert extract_response.status_code == 200
        assert extract_response.json()["extracted"] >= 2
