from app.services.research import ResearchPackBuilder


def test_research_pack_builder_adds_youtube_disclaimer_and_entities() -> None:
    pack = ResearchPackBuilder().build(
        topic="Frequent urination with cystitis",
        keyword="frequent urination blood in urine",
        audience="general audience",
        intent="informational",
        sources=[
            {
                "source_type": "youtube",
                "url": "https://youtube.com/watch?v=demo",
                "title": "Urinary tract discussion",
                "summary": "Discusses fever and blood in urine red flags.",
                "reliability_score": 0.45,
            },
            {
                "source_type": "manual",
                "url": "https://example.org/guideline",
                "title": "Guideline",
                "summary": "Symptoms and red flags.",
                "reliability_score": 0.9,
            },
        ],
        facts=[],
    )
    assert "blood in urine" in pack["important_entities"]
    assert any("Video transcripts" in item for item in pack["recommended_disclaimers"])
