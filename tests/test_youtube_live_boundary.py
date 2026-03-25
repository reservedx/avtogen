from datetime import datetime, timezone

from app.services.providers import (
    YouTubeDataApiSearchClient,
    YouTubeTranscriptProvider,
    YouTubeVideoSearchItem,
)


class _FakeHttpResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "items": [
                {
                    "id": {"videoId": "abc123"},
                    "snippet": {
                        "title": "Clinical overview",
                        "channelTitle": "Health Channel",
                        "description": "Overview",
                        "publishedAt": "2025-01-02T10:00:00Z",
                    },
                }
            ]
        }


class _FakeHttpClient:
    def get(self, *_: object, **__: object) -> _FakeHttpResponse:
        return _FakeHttpResponse()


class _FakeSearchClient:
    def search(self, topic_query: str) -> list[YouTubeVideoSearchItem]:
        return [
            YouTubeVideoSearchItem(
                video_id="video-1",
                title=f"Video for {topic_query}",
                channel_name="Medical Channel",
                description="Useful transcript source",
                published_at=datetime.now(timezone.utc),
            )
        ]


class _FakeTranscriptFetcher:
    def fetch(self, video_id: str) -> str:
        return f"00:01 Transcript for {video_id}. 00:05 See a doctor for red flags."


def test_youtube_data_api_search_client_parses_response() -> None:
    client = YouTubeDataApiSearchClient(api_key="test-key", http_client=_FakeHttpClient())
    items = client.search("urinary symptoms")
    assert len(items) == 1
    assert items[0].video_id == "abc123"
    assert items[0].channel_name == "Health Channel"


def test_youtube_provider_uses_live_boundary_objects() -> None:
    provider = YouTubeTranscriptProvider(
        search_client=_FakeSearchClient(),
        transcript_fetcher=_FakeTranscriptFetcher(),
    )
    items = provider.collect("urinary symptoms")
    assert len(items) == 1
    assert items[0]["url"].endswith("video-1")
    assert "00:01" not in items[0]["cleaned_content"]
