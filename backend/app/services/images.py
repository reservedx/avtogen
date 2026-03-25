from app.schemas.generation import ImageGenerationItem


class ImageGenerator:
    def generate(self, article_title: str) -> list[dict]:
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
