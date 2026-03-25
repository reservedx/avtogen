from __future__ import annotations

from pathlib import Path

from app.db.models import Article, ArticleVersion, Image
from app.services.providers import WordPressAdapter


class PublishingService:
    def __init__(self, adapter: WordPressAdapter | None = None) -> None:
        self.adapter = adapter or WordPressAdapter()

    def publish_article(
        self,
        article: Article,
        version: ArticleVersion,
        images: list[Image],
    ) -> dict:
        payload = {
            "title": version.meta_title or article.title,
            "slug": article.slug,
            "content": version.content_html,
            "excerpt": version.excerpt,
            "status": "draft",
        }
        if article.cms_post_id:
            remote_post = self.adapter.update_post(article.cms_post_id, payload)
        else:
            remote_post = self.adapter.create_post(payload)

        uploaded_media = self._upload_images(images)
        featured_media_id = self._featured_media_id(uploaded_media)
        if featured_media_id:
            self.adapter.set_featured_image(str(remote_post["id"]), featured_media_id)

        self.adapter.update_meta(
            str(remote_post["id"]),
            {
                "meta_title": version.meta_title,
                "meta_description": version.meta_description,
            },
        )
        self.adapter.attach_schema(str(remote_post["id"]), version.schema_json or {})
        published_post = self.adapter.publish_post(str(remote_post["id"]))
        return {
            "post": published_post,
            "uploaded_media": uploaded_media,
            "featured_media_id": featured_media_id,
        }

    def _upload_images(self, images: list[Image]) -> list[dict]:
        uploaded_media: list[dict] = []
        for image in images:
            if not image.local_path:
                continue
            path = Path(image.local_path)
            if not path.exists() or not path.is_file():
                continue
            media = self.adapter.upload_media(path.name, path.read_bytes(), "image/png")
            uploaded_media.append(
                {
                    "image_id": str(image.id),
                    "remote_id": str(media["id"]),
                    "source_url": media.get("source_url"),
                    "is_featured": image.is_featured,
                }
            )
        return uploaded_media

    def _featured_media_id(self, uploaded_media: list[dict]) -> str | None:
        featured = next((item for item in uploaded_media if item["is_featured"]), None)
        return str(featured["remote_id"]) if featured else None
