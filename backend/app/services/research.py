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
        return {
            "topic": topic,
            "keyword": keyword,
            "intent": intent,
            "audience": audience,
            "source_summaries": sources,
            "extracted_facts": facts,
            "disputed_claims": [],
            "important_entities": ["urinary tract", "red flags", "symptoms"],
            "recommended_disclaimers": [
                "This article is informational and does not replace medical consultation."
            ],
            "competitor_gaps": None,
            "suggested_internal_links": [],
            "banned_assertions": [
                "guaranteed cure",
                "doctor is not needed",
                "safe without a doctor",
            ],
            "required_citations": [source["url"] for source in sources],
        }
