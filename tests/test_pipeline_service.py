from app.application.pipeline_service import PipelineService


def test_pipeline_service_preview_contains_task_outputs() -> None:
    result = PipelineService().run_preview(
        "frequent urination with cystitis",
        "women seeking information",
    )
    assert "quality_report" in result
    assert "internal_link_suggestions" in result
    assert result["research_pack"]["extracted_facts"]
