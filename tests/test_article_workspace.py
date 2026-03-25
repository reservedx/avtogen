from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.models import Article, ArticleVersion, Brief, Cluster, ContentTopic, EditorialReview, Image, PublishingJob, QualityReport
from app.db.session import SessionLocal
from app.main import app


def test_article_workspace_endpoint_returns_aggregate_payload() -> None:
    cluster = Cluster(name="Urinary Health", slug=f"urinary-{uuid4().hex[:8]}")
    topic = ContentTopic(
        cluster_id=cluster.id,
        working_title="Frequent urination with cystitis",
        target_query="frequent urination with cystitis",
        audience="general audience",
    )
    brief = Brief(topic_id=topic.id, version=1, brief_json={"primary_keyword": "test"}, prompt_snapshot="snapshot", model_name="stub")
    article = Article(topic_id=topic.id, brief_id=brief.id, title="Frequent urination with cystitis", slug=f"frequent-{uuid4().hex[:8]}", status="approved")
    version = ArticleVersion(
        article_id=article.id,
        version=1,
        content_markdown="# Title",
        content_html="<h1>Title</h1>",
        excerpt="Excerpt",
        meta_title="Meta title",
        meta_description="Meta description",
        faq_json={"items": []},
        schema_json={"@type": "Article"},
        word_count=100,
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
        db.add(
            Image(
                article_id=article.id,
                prompt="Prompt",
                alt_text="Alt",
                storage_url="https://example.com/image.png",
                local_path="C:/tmp/image.png",
                width=1024,
                height=1024,
                is_featured=True,
            )
        )
        db.add(
            QualityReport(
                article_version_id=version.id,
                report_json={"overall_status": "review"},
                quality_score=82,
                risk_score=24,
                blocking_issues_count=0,
                warning_count=2,
            )
        )
        db.add(
            EditorialReview(
                article_id=article.id,
                article_version_id=version.id,
                reviewer_name="Editor",
                decision="approved",
                notes="Looks good",
            )
        )
        db.add(
            PublishingJob(
                article_id=article.id,
                target_system="wordpress",
                status="published",
                request_payload={"title": article.title},
                response_payload={"id": 123},
            )
        )
        db.commit()
        article_id = str(article.id)

    with TestClient(app) as client:
        response = client.get(f"/api/v1/articles/{article_id}/workspace")
        assert response.status_code == 200
        payload = response.json()
        assert payload["article"]["id"] == article_id
        assert len(payload["versions"]) >= 1
        assert len(payload["images"]) == 1
        assert payload["latest_quality_report"]["quality_score"] == 82
        assert payload["publishing_job"]["status"] == "published"
        assert payload["editorial_reviews"][0]["reviewer_name"] == "Editor"
