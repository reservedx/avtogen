from __future__ import annotations

from openai import OpenAI

from app.config import settings


class OpenAIGateway:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key and not settings.use_stub_generation else None

    def generate_brief_json(self, research_pack: dict) -> dict | None:
        if self.client is None:
            return None
        return None

    def generate_draft_json(self, brief: dict, research_pack: dict) -> dict | None:
        if self.client is None:
            return None
        return None

    def generate_image_variants(self, article_title: str) -> list[dict] | None:
        if self.client is None:
            return None
        return None
