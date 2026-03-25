from base64 import b64encode

import httpx
from slugify import slugify

from app.config import settings
from app.services.transcript import TranscriptCleaner


class YouTubeTranscriptProvider:
    def __init__(self) -> None:
        self.cleaner = TranscriptCleaner()

    def collect(self, topic_query: str) -> list[dict]:
        raw = (
            "00:01 Frequent urination can happen for different reasons. "
            "00:02 Frequent urination can happen for different reasons. "
            "00:15 See a doctor for fever or blood."
        )
        return [{
            "source_type": "youtube",
            "url": f"https://youtube.com/watch?v=demo-{slugify(topic_query)}",
            "title": f"YouTube research for {topic_query}",
            "author": "Medical Channel",
            "raw_content": raw,
            "cleaned_content": self.cleaner.clean(raw),
            "summary": "Transcript is used as one supporting source, not the only evidence base.",
            "reliability_score": 0.45,
            "ingestion_status": "completed",
        }]


class ManualSourceProvider:
    def collect(self, topic_query: str) -> list[dict]:
        return [{
            "source_type": "manual",
            "url": f"https://example.org/guideline/{slugify(topic_query)}",
            "title": f"Manual reference for {topic_query}",
            "author": "Editorial Research",
            "raw_content": "Curated guideline excerpt.",
            "cleaned_content": "Curated guideline excerpt.",
            "summary": "Trusted manually supplied reference.",
            "reliability_score": 0.85,
            "ingestion_status": "completed",
        }]


class WordPressAdapter:
    def __init__(self) -> None:
        token = b64encode(
            f"{settings.wordpress_username}:{settings.wordpress_app_password}".encode("utf-8")
        ).decode("utf-8")
        self.headers = {"Authorization": f"Basic {token}"}
        self.base_api = f"{settings.wordpress_base_url.rstrip('/')}/wp-json/wp/v2"

    def create_post(self, payload: dict) -> dict:
        return self._post("/posts", payload)

    def update_post(self, remote_id: str, payload: dict) -> dict:
        return self._post(f"/posts/{remote_id}", payload)

    def upload_media(self, file_name: str, content: bytes, mime_type: str) -> dict:
        response = httpx.post(
            f"{self.base_api}/media",
            headers={
                **self.headers,
                "Content-Disposition": f'attachment; filename="{file_name}"',
                "Content-Type": mime_type,
            },
            content=content,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    def set_featured_image(self, remote_post_id: str, media_id: str) -> dict:
        return self.update_post(remote_post_id, {"featured_media": media_id})

    def publish_post(self, remote_post_id: str) -> dict:
        return self.update_post(remote_post_id, {"status": "publish"})

    def update_meta(self, remote_post_id: str, meta: dict) -> dict:
        return self.update_post(remote_post_id, {"meta": meta})

    def attach_schema(self, remote_post_id: str, schema: dict) -> dict:
        return self.update_meta(remote_post_id, {"schema_json": schema})

    def _post(self, path: str, payload: dict) -> dict:
        response = httpx.post(
            f"{self.base_api}{path}", headers=self.headers, json=payload, timeout=30.0
        )
        response.raise_for_status()
        return response.json()
