from app.services.platform import QualityGateService


def test_quality_gate_blocks_insufficient_sources() -> None:
    report = QualityGateService().evaluate("## What is it?\n## FAQ\n## Conclusion\n## Sources", 1, 0, 0, True, 1)
    assert report["overall_status"] == "block"
    assert any(issue["code"] == "insufficient_sources" for issue in report["blockers"])


def test_quality_gate_flags_missing_research_coverage_and_manual_review_phrases() -> None:
    markdown = (
        "## What is it?\nThis section gives a treatment plan and dosage advice.\n\n"
        "## FAQ\nAnswers.\n\n"
        "## Conclusion\nDone.\n\n"
        "## Sources\n- https://example.org/source\n"
    )
    report = QualityGateService().evaluate(
        markdown,
        source_count=2,
        internal_link_count=1,
        image_count=1,
        has_meta=True,
        faq_count=1,
        research_pack={
            "important_entities": ["pregnancy", "blood in urine"],
            "required_citations": ["https://example.org/source"],
        },
        brief={"required_sections": ["when_to_see_doctor", "sources"]},
    )
    assert report["overall_status"] in {"review", "block"}
    assert any(item["code"] == "manual_review_medical_claim" for item in report["warnings"])
    assert any(
        item["code"] in {"source_coverage_weak", "brief_section_gap"}
        for item in (report["blockers"] + report["warnings"])
    )
