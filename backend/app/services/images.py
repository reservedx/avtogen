from __future__ import annotations

import base64
from pathlib import Path
from uuid import uuid4

from app.schemas.generation import ImageGenerationItem
from app.services.openai_gateway import OpenAIGateway
from app.services.storage import AssetStorageService


class ImageGenerator:
    def __init__(
        self,
        gateway: OpenAIGateway | None = None,
        output_dir: str | Path | None = None,
        storage: AssetStorageService | None = None,
    ) -> None:
        self.gateway = gateway or OpenAIGateway()
        self.storage = storage or AssetStorageService(output_dir=output_dir)

    def _fallback_variants(self, article_title: str) -> list[dict]:
        return [
            ImageGenerationItem(
                prompt=f"Featured editorial illustration for {article_title}, neutral medical style, no gore",
                alt_text=f"Featured editorial illustration for {article_title}",
                is_featured=True,
            ).model_dump(),
            ImageGenerationItem(
                prompt=f"Inline educational illustration about symptoms related to {article_title}",
                alt_text=f"Inline educational illustration about symptoms related to {article_title}",
                is_featured=False,
            ).model_dump(),
            ImageGenerationItem(
                prompt=f"Inline consultation scene related to {article_title}, calm clinic atmosphere",
                alt_text=f"Inline consultation scene related to {article_title}",
                is_featured=False,
            ).model_dump(),
        ]

    def _prompt_variants(self, article_title: str) -> list[dict]:
        return self.gateway.generate_image_variants(article_title) or self._fallback_variants(article_title)

    def _image_size(self, is_featured: bool) -> str:
        return "1536x1024" if is_featured else "1024x1024"

    def _generate_binary_asset(self, article_slug: str, image_payload: dict) -> dict:
        if self.gateway.client is None:
            return image_payload
        try:
            response = self.gateway.client.images.generate(
                model=self.gateway.image_model,
                prompt=image_payload["prompt"],
                size=self._image_size(bool(image_payload.get("is_featured"))),
                quality="medium",
                output_format="png",
                response_format="b64_json",
                n=1,
            )
            item = response.data[0]
            if not getattr(item, "b64_json", None):
                return image_payload
            role = "featured" if image_payload.get("is_featured") else "inline"
            local_path, storage_url = self.storage.persist_image(
                article_slug,
                role,
                base64.b64decode(item.b64_json),
            )
            updated = dict(image_payload)
            updated["local_path"] = local_path
            updated["storage_url"] = storage_url
            if updated.get("is_featured"):
                updated["width"] = 1536
                updated["height"] = 1024
            else:
                updated["width"] = 1024
                updated["height"] = 1024
            return updated
        except Exception:
            return image_payload

    def generate(self, article_title: str, article_slug: str | None = None) -> list[dict]:
        slug = article_slug or f"article-{uuid4().hex[:12]}"
        return [self._generate_binary_asset(slug, payload) for payload in self._prompt_variants(article_title)]
