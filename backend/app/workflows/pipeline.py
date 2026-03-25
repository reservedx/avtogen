from app.services.platform import (
    BriefGenerator,
    DraftGenerator,
    InterlinkingService,
    ManualSourceProvider,
    OpenAIGateway,
    QualityGateService,
    ResearchNoteExtractor,
    ResearchPackBuilder,
    RiskTierService,
    ReviewWorkflowService,
    YouTubeTranscriptProvider,
)


class ArticlePipeline:
    def __init__(self) -> None:
        self.youtube_provider = YouTubeTranscriptProvider()
        self.manual_provider = ManualSourceProvider()
        self.research_builder = ResearchPackBuilder()
        self.fact_extractor = ResearchNoteExtractor()
        self.brief_generator = BriefGenerator()
        self.draft_generator = DraftGenerator()
        self.quality_gate = QualityGateService()
        self.risk_service = RiskTierService()
        self.review_service = ReviewWorkflowService()
        self.interlinking = InterlinkingService()
        self.openai_gateway = OpenAIGateway()

    def run(self, topic_query: str, audience: str) -> dict:
        sources = self.youtube_provider.collect(topic_query) + self.manual_provider.collect(topic_query)
        if not sources:
            return {"status": "stopped", "reason": "no_sources"}
        facts = [
            {
                "fact_type": row["fact_type"],
                "content": row["content"],
                "confidence_score": row["confidence_score"],
                "citations": [row["citation_data"]] if row.get("citation_data") else [],
            }
            for row in self.fact_extractor.extract_rows(sources)
        ]
        research_pack = self.research_builder.build(topic_query, topic_query, audience, "informational", sources, facts)
        brief = self.openai_gateway.generate_brief_json(research_pack) or self.brief_generator.generate(research_pack)
        draft = self.openai_gateway.generate_draft_json(brief, research_pack) or self.draft_generator.generate(brief, research_pack)
        risk_tier = self.risk_service.classify(topic_query, draft["title"], draft["content_markdown"])
        quality = self.quality_gate.evaluate(
            draft["content_markdown"],
            len(sources),
            0,
            0,
            True,
            len(draft["faq_json"]["items"]),
            research_pack=research_pack,
            brief=brief,
            risk_tier=risk_tier,
        )
        fast_lane = self.risk_service.fast_lane_eligible(risk_tier, quality)
        needs_review = (
            self.review_service.requires_manual_review(draft["content_markdown"])
            or (quality["overall_status"] != "pass" and not fast_lane)
            or risk_tier != "low"
        )
        slug = draft.get("slug", "")
        cannibalization_flag = self.interlinking.looks_cannibalized(slug, [])
        return {
            "status": "in_review" if needs_review or cannibalization_flag else "approved",
            "risk_tier": risk_tier,
            "fast_lane_eligible": fast_lane,
            "research_pack": research_pack,
            "brief": brief,
            "draft": draft,
            "quality_report": quality,
            "sources": sources,
            "internal_link_suggestions": self.interlinking.suggest_links([], None),
            "cannibalization_flag": cannibalization_flag,
        }
