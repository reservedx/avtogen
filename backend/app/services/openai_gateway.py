from __future__ import annotations

import json
from pydantic import ValidationError

from openai import OpenAI

from app.config import settings
from app.prompts.brief import BRIEF_SYSTEM_PROMPT
from app.prompts.draft import DRAFT_SYSTEM_PROMPT
from app.schemas.generation import BriefGenerationResult, DraftGenerationResult, ImageGenerationItem


class OpenAIGateway:
    def __init__(self) -> None:
        self.enabled = (
            bool(settings.openai_api_key)
            and settings.openai_api_key != "changeme"
            and not settings.use_stub_generation
        )
        self.image_model = settings.openai_image_model
        self.image_output_format = settings.openai_image_output_format
        self.client = OpenAI(api_key=settings.openai_api_key) if self.enabled else None

    def _json_completion(self, model: str, system_prompt: str, user_prompt: str, temperature: float) -> dict | list | None:
        if self.client is None:
            return None
        try:
            completion = self.client.chat.completions.create(
                model=model,
                temperature=temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = completion.choices[0].message.content
            return json.loads(content) if content else None
        except Exception:
            return None

    def _validate(self, schema: type, payload: dict | list | None) -> dict | list | None:
        if payload is None:
            return None
        try:
            validated = schema.model_validate(payload)
            return validated.model_dump()
        except ValidationError:
            return None

    def generate_brief_json(self, research_pack: dict) -> dict | None:
        payload = self._json_completion(
            model=settings.openai_brief_model,
            system_prompt=BRIEF_SYSTEM_PROMPT,
            user_prompt=(
                "Create a JSON brief for the following research pack.\n"
                "Return exactly this object shape with these keys only:\n"
                "{"
                "\"primary_keyword\": str,"
                "\"secondary_keywords\": [str],"
                "\"search_intent\": str,"
                "\"user_problem\": str,"
                "\"article_goal\": str,"
                "\"target_word_count\": int,"
                "\"tone\": str,"
                "\"reading_level\": str,"
                "\"outline\": [{\"heading\": str, \"level\": str}],"
                "\"required_sections\": [str],"
                "\"prohibited_sections\": [str],"
                "\"medical_safety_notes\": [str],"
                "\"faq_questions\": [str],"
                "\"internal_link_targets\": [str],"
                "\"schema_type\": str,"
                "\"meta_guidance\": {},"
                "\"image_guidance\": {}"
                "}\n\n"
                f"{research_pack}"
            ),
            temperature=0.2,
        )
        return self._validate(BriefGenerationResult, payload)

    def generate_draft_json(self, brief: dict, research_pack: dict) -> dict | None:
        payload = self._json_completion(
            model=settings.openai_draft_model,
            system_prompt=DRAFT_SYSTEM_PROMPT,
            user_prompt=(
                "Create a JSON article draft payload from this brief and research pack.\n"
                "Return exactly this object shape with these keys only:\n"
                "{"
                "\"title\": str,"
                "\"slug\": str,"
                "\"content_markdown\": str,"
                "\"excerpt\": str,"
                "\"meta_title\": str,"
                "\"meta_description\": str,"
                "\"faq_items\": [{\"question\": str, \"answer\": str}],"
                "\"schema_payload\": {},"
                "\"image_prompts\": [str],"
                "\"alt_texts\": [str]"
                "}\n\n"
                f"Brief: {brief}\n\nResearch pack: {research_pack}"
            ),
            temperature=0.4,
        )
        parsed = self._validate(DraftGenerationResult, payload)
        if parsed is None:
            return None
        parsed["faq_json"] = {"items": parsed.pop("faq_items")}
        parsed["schema_json"] = parsed.pop("schema_payload")
        parsed["content_html"] = parsed["content_markdown"]
        return parsed

    def generate_image_variants(self, article_title: str) -> list[dict] | None:
        payload = self._json_completion(
            model=settings.openai_draft_model,
            system_prompt=(
                "Return a JSON object with an 'items' array containing exactly 3 image prompt entries. "
                "Each item must have prompt, alt_text, storage_url, local_path, width, height, is_featured. "
                "One featured image and two inline images. Keep them medically neutral."
            ),
            user_prompt=f"Generate image prompt items for the article title: {article_title}",
            temperature=0.6,
        )
        if payload is None:
            return None
        items = payload.get("items", [])
        result = []
        for item in items:
            try:
                result.append(ImageGenerationItem.model_validate(item).model_dump())
            except ValidationError:
                return None
        return result
