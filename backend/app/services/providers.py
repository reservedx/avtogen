from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

import httpx
from slugify import slugify

from app.config import settings
from app.services.transcript import TranscriptCleaner


class SourceProvider(Protocol):
    def collect(self, topic_query: str) -> list[dict]:
        ...


class YouTubeSearchClient(Protocol):
    def search(self, topic_query: str) -> list["YouTubeVideoSearchItem"]:
        ...


class TranscriptFetcher(Protocol):
    def fetch(self, video_id: str) -> str:
        ...


@dataclass
class YouTubeVideoSearchItem:
    video_id: str
    title: str
    channel_name: str
    description: str
    published_at: datetime | None = None


@dataclass
class YouTubeVideoRecord:
    video_id: str
    title: str
    channel_name: str
    description: str
    transcript_text: str
    published_at: datetime | None = None

    @property
    def url(self) -> str:
        return f"https://youtube.com/watch?v={self.video_id}"


class YouTubeDataApiSearchClient:
    def __init__(
        self,
        api_key: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key or settings.youtube_api_key
        self.http_client = http_client or httpx.Client(timeout=20.0)
        self.base_url = "https://www.googleapis.com/youtube/v3/search"

    def search(self, topic_query: str) -> list[YouTubeVideoSearchItem]:
        if not self.api_key or self.api_key == "changeme":
            return []
        params = {
            "part": "snippet",
            "q": topic_query,
            "key": self.api_key,
            "type": "video",
            "maxResults": settings.youtube_max_results,
            "safeSearch": "moderate",
        }
        if settings.youtube_region_code:
            params["regionCode"] = settings.youtube_region_code
        if settings.youtube_relevance_language:
            params["relevanceLanguage"] = settings.youtube_relevance_language

        response = self.http_client.get(self.base_url, params=params)
        response.raise_for_status()
        payload = response.json()
        items: list[YouTubeVideoSearchItem] = []
        for item in payload.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            snippet = item.get("snippet", {})
            if not video_id:
                continue
            items.append(
                YouTubeVideoSearchItem(
                    video_id=video_id,
                    title=snippet.get("title", ""),
                    channel_name=snippet.get("channelTitle", "Unknown channel"),
                    description=snippet.get("description", ""),
                    published_at=_parse_youtube_datetime(snippet.get("publishedAt")),
                )
            )
        return items


class YouTubeTranscriptApiFetcher:
    def __init__(self, languages: list[str] | None = None) -> None:
        raw_languages = languages or [
            item.strip() for item in settings.youtube_transcript_languages.split(",") if item.strip()
        ]
        self.languages = raw_languages or ["en"]

    def fetch(self, video_id: str) -> str:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except ImportError:
            return ""

        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=self.languages)
        except Exception:
            return ""

        return " ".join(part.get("text", "") for part in transcript if part.get("text"))


class YouTubeTranscriptProvider:
    def __init__(
        self,
        search_client: YouTubeSearchClient | None = None,
        transcript_fetcher: TranscriptFetcher | None = None,
    ) -> None:
        self.cleaner = TranscriptCleaner()
        self.search_client = search_client or (
            YouTubeDataApiSearchClient() if settings.youtube_enabled else None
        )
        self.transcript_fetcher = transcript_fetcher or YouTubeTranscriptApiFetcher()

    def collect(self, topic_query: str) -> list[dict]:
        records = self._search(topic_query)
        return [self._to_source_payload(record) for record in records if record.transcript_text.strip()]

    def _search(self, topic_query: str) -> list[YouTubeVideoRecord]:
        if self.search_client:
            items = self.search_client.search(topic_query)
            records: list[YouTubeVideoRecord] = []
            for item in items:
                transcript = self.transcript_fetcher.fetch(item.video_id) if self.transcript_fetcher else ""
                if not transcript:
                    continue
                records.append(
                    YouTubeVideoRecord(
                        video_id=item.video_id,
                        title=item.title or f"YouTube research for {topic_query}",
                        channel_name=item.channel_name or "Unknown channel",
                        description=item.description or "",
                        transcript_text=transcript,
                        published_at=item.published_at,
                    )
                )
            if records:
                return records
        return [self._fallback_record(topic_query)]

    def _fallback_record(self, topic_query: str) -> YouTubeVideoRecord:
        return YouTubeVideoRecord(
            video_id=f"demo-{slugify(topic_query)}",
            title=f"YouTube research for {topic_query}",
            channel_name="Medical Channel",
            description="Educational discussion of symptoms, warning signs, and when to seek clinician review.",
            transcript_text=(
                "00:01 Frequent urination can happen for different reasons. "
                "00:02 Frequent urination can happen for different reasons. "
                "00:15 See a doctor for fever or blood. "
                "00:21 This video is educational and does not replace diagnosis."
            ),
            published_at=datetime.now(timezone.utc),
        )

    def _to_source_payload(self, record: YouTubeVideoRecord) -> dict:
        cleaned = self.cleaner.clean(record.transcript_text)
        return {
            "source_type": "youtube",
            "url": record.url,
            "title": record.title,
            "author": record.channel_name,
            "published_at": record.published_at,
            "transcript_text": record.transcript_text,
            "raw_content": record.transcript_text,
            "cleaned_content": cleaned,
            "summary": self._summary_from_cleaned(cleaned),
            "reliability_score": 0.45,
            "ingestion_status": "completed",
        }

    def _summary_from_cleaned(self, cleaned_transcript: str) -> str:
        sentence = cleaned_transcript.split(".")[0].strip()
        return (
            f"{sentence}. Transcript is used as one supporting source, not the only evidence base."
            if sentence
            else "Transcript captured as a supporting source."
        )


class ManualSourceProvider:
    def collect(self, topic_query: str) -> list[dict]:
        return [
            {
                "source_type": "manual",
                "url": f"https://example.org/guideline/{slugify(topic_query)}",
                "title": f"Manual reference for {topic_query}",
                "author": "Editorial Research",
                "published_at": None,
                "transcript_text": None,
                "raw_content": "Curated guideline excerpt.",
                "cleaned_content": "Curated guideline excerpt.",
                "summary": "Trusted manually supplied reference.",
                "reliability_score": 0.85,
                "ingestion_status": "completed",
            }
        ]


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


def _parse_youtube_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
