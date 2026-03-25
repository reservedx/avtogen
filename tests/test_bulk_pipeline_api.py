from fastapi.testclient import TestClient
from uuid import uuid4

from app.db.models import Article, ArticleVersion, Brief, Cluster, ContentTopic
from app.db.session import SessionLocal
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


def test_bulk_article_action_endpoint_runs_quality_checks() -> None:
    suffix = uuid4().hex[:8]
    cluster = Cluster(name="Bulk Ops", slug=f"bulk-ops-{suffix}")
    topic = ContentTopic(
        cluster_id=cluster.id,
        working_title="Frequent urination with cystitis",
        target_query="frequent urination with cystitis",
        audience="general audience",
    )
    brief = Brief(topic_id=topic.id, version=1, brief_json={"required_sections": []}, prompt_snapshot="snapshot", model_name="stub")
    article = Article(
        topic_id=topic.id,
        brief_id=brief.id,
        title="Frequent urination with cystitis",
        slug=f"frequent-urination-with-cystitis-{suffix}",
        status="draft",
    )
    version = ArticleVersion(
        article_id=article.id,
        version=1,
        content_markdown="## What is it?\ntext\n\n## FAQ\ntext\n\n## Conclusion\ntext\n\n## Sources\n- src",
        content_html="<h2>What is it?</h2>",
        excerpt="Excerpt",
        meta_title="Meta",
        meta_description="Description",
        faq_json={"items": [{"question": "Q", "answer": "A"}]},
        schema_json={"@type": "Article"},
        word_count=1000,
        created_by="system",
        generation_context={},
    )

    with SessionLocal() as db:
        db.add(cluster)
        db.flush()
        topic.cluster_id = cluster.id
        db.add(topic)
        db.flush()
        brief.topic_id = topic.id
        db.add(brief)
        db.flush()
        article.topic_id = topic.id
        article.brief_id = brief.id
        db.add(article)
        db.flush()
        version.article_id = article.id
        db.add(version)
        db.flush()
        article.current_version_id = version.id
        db.commit()
        article_id = str(article.id)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/articles/bulk-action",
            json={"article_ids": [article_id], "action": "run_quality_check"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["requested"] == 1
        assert payload["completed"] == 1
        assert payload["results"][0]["status"] == "completed"
