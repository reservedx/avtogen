from app.config import settings


class InterlinkingService:
    def suggest_links(self, published_articles: list[dict], cluster_id: str | None = None, max_links: int = 5) -> list[dict]:
        suggestions = []
        seen_anchors = set()
        for article in published_articles:
            if cluster_id and article.get("cluster_id") != cluster_id:
                continue
            anchor = article.get("title") or article.get("slug") or "related article"
            if anchor.lower() in seen_anchors:
                continue
            seen_anchors.add(anchor.lower())
            suggestions.append(
                {
                    "target_article_id": article["id"],
                    "anchor_text": anchor,
                    "placement_context": "related-reading",
                }
            )
            if len(suggestions) >= max_links:
                break
        return suggestions

    def looks_cannibalized(self, candidate_slug: str, published_slugs: list[str]) -> bool:
        return any(candidate_slug == slug for slug in published_slugs) or any(
            candidate_slug in slug or slug in candidate_slug for slug in published_slugs if slug
        )

    def similarity_flag(self, score: float) -> bool:
        return score >= settings.similarity_threshold
