from app.services.openai_gateway import OpenAIGateway


def test_openai_gateway_disabled_without_real_key() -> None:
    gateway = OpenAIGateway()
    assert gateway.enabled is False
    assert gateway.generate_brief_json({"keyword": "test"}) is None
    assert gateway.generate_draft_json({"primary_keyword": "test"}, {"source_summaries": []}) is None
    assert gateway.generate_image_variants("Test title") is None
