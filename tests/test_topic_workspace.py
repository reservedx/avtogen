from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.models import Article, Brief, Cluster, ContentTopic, ResearchNote, Source
from app.db.session import SessionLocal
from app.main import app


def test_topic_workspace_returns_sources_notes_briefs_and_articles() -> None:
    cluster = Cluster(name="Topic Workspace", slug=f"topic-workspace-{uuid4().hex[:8]}")
    topic = ContentTopic(
        cluster_id=cluster.id,
        working_title="Frequent urination with cystitis",
        target_query="frequent urination with cystitis",
        audience="general audience",
    )
    brief = Brief(topic_id=topic.id, version=1, brief_json={"primary_keyword": "cystitis"}, prompt_snapshot="snapshot", model_name="stub")
    article = Article(topic_id=topic.id, brief_id=brief.id, title="Frequent urination with cystitis", slug=f"topic-article-{uuid4().hex[:8]}", status="draft")

    with SessionLocal() as db:
        db.add(cluster)
        db.flush()
        topic.cluster_id = cluster.id
        db.add(topic)
        db.flush()
        db.add(
            Source(
                topic_id=topic.id,
                source_type="manual",
                url="https://example.org/guideline",
                title="Guideline",
                author="Medical board",
                transcript_text=None,
                raw_content="Guideline raw content",
                cleaned_content="Guideline cleaned content",
                reliability_score=0.91,
                ingestion_status="ingested",
            )
        )
        brief.topic_id = topic.id
        db.add(brief)
        db.flush()
        db.add(
            ResearchNote(
                topic_id=topic.id,
                source_id=None,
                fact_type="red_flag",
                content="Blood in urine requires clinical review.",
                confidence_score=0.92,
                citation_data={"url": "https://example.org/guideline"},
            )
        )
        article.topic_id = topic.id
        article.brief_id = brief.id
        db.add(article)
        db.commit()
        topic_id = str(topic.id)

    with TestClient(app) as client:
        response = client.get(f"/api/v1/topics/{topic_id}/workspace")
        assert response.status_code == 200
        payload = response.json()
        assert payload["topic"]["id"] == topic_id
        assert len(payload["sources"]) == 1
        assert len(payload["research_notes"]) == 1
        assert len(payload["briefs"]) == 1
        assert len(payload["articles"]) == 1
