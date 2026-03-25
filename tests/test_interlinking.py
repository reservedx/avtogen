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
