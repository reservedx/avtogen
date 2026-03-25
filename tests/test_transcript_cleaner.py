from app.services.platform import TranscriptCleaner


def test_transcript_cleaner_removes_timecodes_and_duplicates() -> None:
    cleaner = TranscriptCleaner()
    cleaned = cleaner.clean("00:01 Hello. 00:02 Hello. 00:10 See a doctor.")
    assert "00:01" not in cleaned
    assert cleaned.count("Hello") == 1
    assert "See a doctor" in cleaned
