from app.services.platform import QualityGateService


def test_quality_gate_blocks_insufficient_sources() -> None:
    report = QualityGateService().evaluate("## What is it?\n## FAQ\n## Conclusion\n## Sources", 1, 0, 0, True, 1)
    assert report["overall_status"] == "block"
    assert any(issue["code"] == "insufficient_sources" for issue in report["blockers"])
