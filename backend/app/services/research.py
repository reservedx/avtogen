from __future__ import annotations


class ResearchPackBuilder:
    def build(
        self,
        topic: str,
        keyword: str,
        audience: str,
        intent: str,
        sources: list[dict],
        facts: list[dict],
    ) -> dict:
        source_summaries = [self._summarize_source(source) for source in sources]
        return {
            "topic": topic,
            "keyword": keyword,
            "intent": intent,
            "audience": audience,
            "source_summaries": source_summaries,
            "extracted_facts": facts,
            "disputed_claims": [],
            "important_entities": self._important_entities(topic, keyword, source_summaries),
            "recommended_disclaimers": self._recommended_disclaimers(keyword, source_summaries),
            "competitor_gaps": None,
            "suggested_internal_links": [],
            "banned_assertions": [
                "guaranteed cure",
                "doctor is not needed",
                "safe without a doctor",
            ],
            "required_citations": [source["url"] for source in source_summaries],
        }

    def _summarize_source(self, source: dict) -> dict:
        summary = source.get("summary") or source.get("cleaned_content") or source.get("raw_content") or ""
        return {
            "source_type": source.get("source_type", "other"),
            "url": source.get("url"),
            "title": source.get("title"),
            "reliability_score": source.get("reliability_score"),
            "published_at": source.get("published_at"),
            "summary": summary[:500],
        }

    def _important_entities(self, topic: str, keyword: str, sources: list[dict]) -> list[str]:
        seed_text = " ".join(
            [
                topic,
                keyword,
                *[source.get("title", "") for source in sources],
                *[source.get("summary", "") for source in sources],
            ]
        ).lower()
        known_entities = [
            "urinary tract",
            "bladder",
            "red flags",
            "symptoms",
            "pregnancy",
            "infection",
            "fever",
            "blood in urine",
        ]
        return [entity for entity in known_entities if entity in seed_text] or ["symptoms", "red flags"]

    def _recommended_disclaimers(self, keyword: str, sources: list[dict]) -> list[str]:
        disclaimers = ["This article is informational and does not replace medical consultation."]
        lower_keyword = keyword.lower()
        if any(term in lower_keyword for term in ["pain", "blood", "pregnan", "fever"]):
            disclaimers.append("Urgent symptoms or pregnancy-related concerns should be reviewed by a clinician.")
        if any(source.get("source_type") == "youtube" for source in sources):
            disclaimers.append("Video transcripts are used as supporting context and require confirmation with higher-trust references.")
        return disclaimers
