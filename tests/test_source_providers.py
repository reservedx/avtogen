from app.services.providers import ManualSourceProvider, YouTubeTranscriptProvider


def test_youtube_provider_returns_raw_and_cleaned_transcript_versions() -> None:
    provider = YouTubeTranscriptProvider()
    items = provider.collect("frequent urination with cystitis")
    assert len(items) == 1
    item = items[0]
    assert item["source_type"] == "youtube"
    assert item["transcript_text"]
    assert item["raw_content"]
    assert item["cleaned_content"]
    assert "00:01" in item["raw_content"]
    assert "00:01" not in item["cleaned_content"]


def test_manual_provider_returns_high_reliability_reference() -> None:
    item = ManualSourceProvider().collect("frequent urination with cystitis")[0]
    assert item["source_type"] == "manual"
    assert item["reliability_score"] == 0.85
    assert item["transcript_text"] is None
