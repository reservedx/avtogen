from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.models import Article, Brief, Cluster, ContentTopic
from app.db.session import SessionLocal
from app.main import app


def test_topic_cannibalization_endpoint_returns_similar_matches() -> None:
    cluster = Cluster(name="Cannibalization", slug=f"cannibalization-{uuid4().hex[:8]}")
    topic = ContentTopic(
        cluster_id=cluster.id,
        working_title="Frequent urination with cystitis",
        target_query="frequent urination cystitis",
        audience="general audience",
        cannibalization_hash="hash-a",
    )
    other_topic = ContentTopic(
        cluster_id=cluster.id,
        working_title="Cystitis symptoms and frequent urination",
        target_query="cystitis symptoms frequent urination",
        audience="general audience",
        cannibalization_hash="hash-b",
    )
    brief = Brief(topic_id=topic.id, version=1, brief_json={"primary_keyword": "cystitis"}, prompt_snapshot="snapshot", model_name="stub")
    article = Article(
        topic_id=topic.id,
        brief_id=brief.id,
        title="Cystitis symptoms frequent urination guide",
        slug="cystitis-symptoms-frequent-urination-guide",
        status="published",
    )

    with SessionLocal() as db:
        db.add(cluster)
        db.flush()
        topic.cluster_id = cluster.id
        other_topic.cluster_id = cluster.id
        db.add(topic)
        db.add(other_topic)
        db.flush()
        brief.topic_id = topic.id
        db.add(brief)
        db.flush()
        article.topic_id = topic.id
        article.brief_id = brief.id
        db.add(article)
        db.commit()
        topic_id = str(other_topic.id)

    with TestClient(app) as client:
        response = client.get(f"/api/v1/topics/{topic_id}/cannibalization-check")
        assert response.status_code == 200
        payload = response.json()
        assert payload["max_score"] > 0
        assert len(payload["matches"]) >= 1
