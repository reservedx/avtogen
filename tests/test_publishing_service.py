from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.db.models import Article, ArticleVersion, Image
from app.services.publishing import PublishingService


class _FakeWordPressAdapter:
    def __init__(self) -> None:
        self.created_payloads: list[dict] = []
        self.updated_payloads: list[tuple[str, dict]] = []
        self.uploaded_files: list[tuple[str, bytes, str]] = []
        self.featured_calls: list[tuple[str, str]] = []
        self.meta_calls: list[tuple[str, dict]] = []
        self.schema_calls: list[tuple[str, dict]] = []
        self.publish_calls: list[str] = []

    def create_post(self, payload: dict) -> dict:
        self.created_payloads.append(payload)
        return {"id": 101, "link": "https://example.com/post-101"}

    def update_post(self, remote_id: str, payload: dict) -> dict:
        self.updated_payloads.append((remote_id, payload))
        return {"id": remote_id, "link": f"https://example.com/post-{remote_id}"}

    def upload_media(self, file_name: str, content: bytes, mime_type: str) -> dict:
        self.uploaded_files.append((file_name, content, mime_type))
        return {"id": len(self.uploaded_files) + 500, "source_url": f"https://example.com/media/{file_name}"}

    def set_featured_image(self, remote_post_id: str, media_id: str) -> dict:
        self.featured_calls.append((remote_post_id, media_id))
        return {"id": remote_post_id, "featured_media": media_id}

    def update_meta(self, remote_post_id: str, meta: dict) -> dict:
        self.meta_calls.append((remote_post_id, meta))
        return {"id": remote_post_id, "meta": meta}

    def attach_schema(self, remote_post_id: str, schema: dict) -> dict:
        self.schema_calls.append((remote_post_id, schema))
        return {"id": remote_post_id, "schema_json": schema}

    def publish_post(self, remote_post_id: str) -> dict:
        self.publish_calls.append(remote_post_id)
        return {"id": remote_post_id, "link": f"https://example.com/post-{remote_post_id}", "status": "publish"}


def _build_image(path: Path, is_featured: bool) -> Image:
    path.write_bytes(b"png-data")
    return Image(
        id=uuid4(),
        article_id=uuid4(),
        prompt="Prompt",
        alt_text="Alt",
        local_path=str(path),
        storage_url=None,
        width=1024,
        height=1024,
        is_featured=is_featured,
    )


def test_publishing_service_creates_post_and_uploads_featured_media(tmp_path) -> None:
    adapter = _FakeWordPressAdapter()
    service = PublishingService(adapter=adapter)
    article = Article(id=uuid4(), topic_id=uuid4(), brief_id=uuid4(), title="Title", slug="title")
    version = ArticleVersion(
        id=uuid4(),
        article_id=article.id,
        content_markdown="# Title",
        content_html="<h1>Title</h1>",
        excerpt="Excerpt",
        meta_title="Meta title",
        meta_description="Meta description",
        faq_json={},
        schema_json={"@type": "Article"},
        version=1,
        word_count=100,
        created_by="system",
        generation_context={},
    )
    featured = _build_image(tmp_path / "featured.png", True)
    inline = _build_image(tmp_path / "inline.png", False)

    result = service.publish_article(article, version, [featured, inline])

    assert adapter.created_payloads
    assert len(adapter.uploaded_files) == 2
    assert adapter.featured_calls == [("101", "501")]
    assert adapter.meta_calls[0][1]["meta_title"] == "Meta title"
    assert adapter.schema_calls[0][1] == {"@type": "Article"}
    assert adapter.publish_calls == ["101"]
    assert result["post"]["status"] == "publish"


def test_publishing_service_updates_existing_remote_post(tmp_path) -> None:
    adapter = _FakeWordPressAdapter()
    service = PublishingService(adapter=adapter)
    article = Article(
        id=uuid4(),
        topic_id=uuid4(),
        brief_id=uuid4(),
        title="Title",
        slug="title",
        cms_post_id="777",
    )
    version = ArticleVersion(
        id=uuid4(),
        article_id=article.id,
        content_markdown="# Title",
        content_html="<h1>Title</h1>",
        excerpt="Excerpt",
        meta_title="Meta title",
        meta_description="Meta description",
        faq_json={},
        schema_json={"@type": "Article"},
        version=2,
        word_count=100,
        created_by="system",
        generation_context={},
    )
    featured = _build_image(tmp_path / "featured.png", True)

    service.publish_article(article, version, [featured])

    assert not adapter.created_payloads
    assert adapter.updated_payloads[0][0] == "777"
