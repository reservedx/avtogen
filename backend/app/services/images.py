from __future__ import annotations

import base64
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.schemas.generation import ImageGenerationItem
from app.services.openai_gateway import OpenAIGateway


class ImageGenerator:
    def __init__(self, gateway: OpenAIGateway | None = None, output_dir: str | Path | None = None) -> None:
        self.gateway = gateway or OpenAIGateway()
        self.output_dir = Path(output_dir or settings.asset_storage_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

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

    def _write_image_file(self, article_slug: str, image_payload: dict, image_bytes: bytes) -> tuple[str, str]:
        article_dir = self.output_dir / article_slug
        article_dir.mkdir(parents=True, exist_ok=True)
        role = "featured" if image_payload.get("is_featured") else "inline"
        filename = f"{role}-{uuid4().hex[:10]}.png"
        path = article_dir / filename
        path.write_bytes(image_bytes)
        return str(path.resolve()), path.resolve().as_uri()

    def _generate_binary_asset(self, article_slug: str, image_payload: dict) -> dict:
        if self.gateway.client is None:
            return image_payload
        try:
            response = self.gateway.client.images.generate(
                model=settings.openai_image_model,
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
            local_path, storage_url = self._write_image_file(article_slug, image_payload, base64.b64decode(item.b64_json))
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
