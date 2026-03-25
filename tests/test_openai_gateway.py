from app.config import settings
from app.services.openai_gateway import OpenAIGateway


def test_openai_gateway_disabled_without_real_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "use_stub_generation", True)
    monkeypatch.setattr(settings, "openai_api_key", "changeme")
    gateway = OpenAIGateway()
    assert gateway.enabled is False
    assert gateway.generate_brief_json({"keyword": "test"}) is None
    assert gateway.generate_draft_json({"primary_keyword": "test"}, {"source_summaries": []}) is None
    assert gateway.generate_image_variants("Test title") is None


def test_openai_gateway_falls_back_to_none_on_api_error(monkeypatch) -> None:
    monkeypatch.setattr(settings, "use_stub_generation", False)
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    gateway = OpenAIGateway()

    class _FailingCompletions:
        def create(self, **_: object):
            raise RuntimeError("quota exceeded")

    class _FailingChat:
        completions = _FailingCompletions()

    class _FailingClient:
        chat = _FailingChat()

    gateway.client = _FailingClient()
    assert gateway.generate_brief_json({"keyword": "test"}) is None
