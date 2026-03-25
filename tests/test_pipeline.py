from app.workflows.pipeline import ArticlePipeline


def test_pipeline_routes_to_review() -> None:
    result = ArticlePipeline().run("frequent urination with cystitis", "women seeking information")
    assert result["status"] == "in_review"
    assert len(result["sources"]) >= 2
