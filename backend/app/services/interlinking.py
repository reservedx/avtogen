from __future__ import annotations

import re
from hashlib import sha1

from app.config import settings


class InterlinkingService:
    TOKEN_RE = re.compile(r"[a-z0-9а-яё]+", re.IGNORECASE)

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

    def cannibalization_hash(self, text: str) -> str:
        tokens = sorted(self._tokenize(text))
        normalized = " ".join(tokens)
        return sha1(normalized.encode("utf-8")).hexdigest()[:16]

    def looks_cannibalized(self, candidate_slug: str, published_slugs: list[str]) -> bool:
        return any(candidate_slug == slug for slug in published_slugs) or any(
            candidate_slug in slug or slug in candidate_slug for slug in published_slugs if slug
        )

    def similarity_score(self, left: str, right: str) -> float:
        left_tokens = self._tokenize(left)
        right_tokens = self._tokenize(right)
        if not left_tokens or not right_tokens:
            return 0.0
        intersection = len(left_tokens & right_tokens)
        union = len(left_tokens | right_tokens)
        return round(intersection / union, 4) if union else 0.0

    def find_cannibalization_candidates(self, candidate_text: str, existing_items: list[dict]) -> dict:
        normalized_candidate = self._normalized_text(candidate_text)
        matches = []
        for item in existing_items:
            comparison_text = item.get("comparison_text") or item.get("title") or item.get("slug") or ""
            score = self.similarity_score(normalized_candidate, comparison_text)
            slug_overlap = self.looks_cannibalized(
                self._slug_like(candidate_text),
                [self._slug_like(item.get("slug") or comparison_text)],
            )
            if score == 0 and not slug_overlap:
                continue
            matches.append(
                {
                    "entity_id": item.get("entity_id") or item.get("id"),
                    "entity_type": item.get("entity_type", "article"),
                    "title": item.get("title") or comparison_text,
                    "slug": item.get("slug"),
                    "similarity_score": max(score, 1.0 if slug_overlap else score),
                    "slug_overlap": slug_overlap,
                }
            )
        matches.sort(key=lambda item: item["similarity_score"], reverse=True)
        max_score = matches[0]["similarity_score"] if matches else 0.0
        return {
            "flagged": self.similarity_flag(max_score),
            "max_score": max_score,
            "matches": matches[:5],
        }

    def similarity_flag(self, score: float) -> bool:
        return score >= settings.similarity_threshold

    def _tokenize(self, text: str) -> set[str]:
        return {token.lower() for token in self.TOKEN_RE.findall(text) if len(token) > 2}

    def _normalized_text(self, text: str) -> str:
        return " ".join(sorted(self._tokenize(text)))

    def _slug_like(self, text: str) -> str:
        return "-".join(sorted(self._tokenize(text)))
