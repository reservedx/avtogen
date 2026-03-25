from app.services.interlinking import InterlinkingService


def test_interlinking_service_limits_unique_anchors() -> None:
    suggestions = InterlinkingService().suggest_links(
        [
            {"id": "1", "title": "Article One", "cluster_id": "c1"},
            {"id": "2", "title": "Article One", "cluster_id": "c1"},
            {"id": "3", "title": "Article Three", "cluster_id": "c1"},
        ],
        cluster_id="c1",
        max_links=5,
    )
    assert len(suggestions) == 2
    assert suggestions[0]["anchor_text"] == "Article One"


def test_interlinking_service_flags_cannibalization_candidates() -> None:
    report = InterlinkingService().find_cannibalization_candidates(
        "frequent urination with cystitis symptoms",
        [
            {
                "entity_id": "a1",
                "entity_type": "article",
                "title": "Cystitis symptoms with frequent urination",
                "slug": "cystitis-symptoms-frequent-urination",
            },
            {
                "entity_id": "a2",
                "entity_type": "article",
                "title": "Unrelated topic",
                "slug": "unrelated-topic",
            },
        ],
    )
    assert report["max_score"] > 0
    assert report["matches"][0]["entity_id"] == "a1"
