from app.services.sections import ArticleSectionRegenerator


def test_section_regenerator_replaces_requested_h2_body() -> None:
    markdown_content = (
        "# Title\n\n"
        "## FAQ\n"
        "Old faq body.\n\n"
        "## Conclusion\n"
        "Old conclusion body.\n"
    )
    updated = ArticleSectionRegenerator().regenerate(
        markdown_content,
        "FAQ",
        "Add clearer symptom follow-up guidance.",
    )
    assert "Old faq body." not in updated
    assert "Add clearer symptom follow-up guidance." in updated
    assert "Old conclusion body." in updated


def test_section_regenerator_appends_missing_section() -> None:
    markdown_content = "# Title\n\n## Introduction\nIntro body.\n"
    updated = ArticleSectionRegenerator().regenerate(markdown_content, "When to see a doctor")
    assert "## When to see a doctor" in updated
