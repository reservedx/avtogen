class ImageGenerator:
    def generate(self, article_title: str) -> list[dict]:
        return [
            {
                "prompt": f"Featured editorial illustration for {article_title}, neutral medical style, no gore",
                "alt_text": f"Featured editorial illustration for {article_title}",
                "storage_url": None,
                "local_path": None,
                "width": None,
                "height": None,
                "is_featured": True,
            },
            {
                "prompt": f"Inline educational illustration about symptoms related to {article_title}",
                "alt_text": f"Inline educational illustration about symptoms related to {article_title}",
                "storage_url": None,
                "local_path": None,
                "width": None,
                "height": None,
                "is_featured": False,
            },
            {
                "prompt": f"Inline consultation scene related to {article_title}, calm clinic atmosphere",
                "alt_text": f"Inline consultation scene related to {article_title}",
                "storage_url": None,
                "local_path": None,
                "width": None,
                "height": None,
                "is_featured": False,
            },
        ]
