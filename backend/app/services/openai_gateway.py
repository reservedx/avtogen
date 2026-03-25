from __future__ import annotations

from openai import OpenAI

from app.config import settings
from app.prompts.brief import BRIEF_SYSTEM_PROMPT
from app.prompts.draft import DRAFT_SYSTEM_PROMPT
from app.schemas.generation import BriefGenerationResult, DraftGenerationResult, ImageGenerationItem


class OpenAIGateway:
    def __init__(self) -> None:
        self.enabled = bool(settings.openai_api_key) and settings.openai_api_key != "changeme" and not settings.use_stub_generation
        self.client = OpenAI(api_key=settings.openai_api_key) if self.enabled else None

    def generate_brief_json(self, research_pack: dict) -> dict | None:
        if self.client is None:
            return None
        completion = self.client.chat.completions.parse(
            model=settings.openai_brief_model,
            response_format=BriefGenerationResult,
            temperature=0.2,
            messages=[
                {"role": "system", "content": BRIEF_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Create a JSON brief for the following research pack.\n\n"
                        f"{research_pack}"
                    ),
                },
            ],
        )
        parsed = completion.choices[0].message.parsed
        return parsed.model_dump() if parsed else None

    def generate_draft_json(self, brief: dict, research_pack: dict) -> dict | None:
        if self.client is None:
            return None
        completion = self.client.chat.completions.parse(
            model=settings.openai_draft_model,
            response_format=DraftGenerationResult,
            temperature=0.4,
            messages=[
                {"role": "system", "content": DRAFT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Create a JSON article draft payload from this brief and research pack.\n\n"
                        f"Brief: {brief}\n\nResearch pack: {research_pack}"
                    ),
                },
            ],
        )
        parsed = completion.choices[0].message.parsed
        if not parsed:
            return None
        payload = parsed.model_dump()
        payload["faq_json"] = {"items": payload.pop("faq_items")}
        payload["schema_json"] = payload.pop("schema_payload")
        payload["content_html"] = payload["content_markdown"]
        return payload

    def generate_image_variants(self, article_title: str) -> list[dict] | None:
        if self.client is None:
            return None
        completion = self.client.chat.completions.parse(
            model=settings.openai_draft_model,
            response_format=list[ImageGenerationItem],
            temperature=0.6,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Return exactly 3 JSON image items for a women's health article. "
                        "One featured image and two inline images. Keep prompts medically neutral."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Generate image prompt items for the article title: {article_title}",
                },
            ],
        )
        parsed = completion.choices[0].message.parsed
        if not parsed:
            return None
        return [item.model_dump() for item in parsed]
