class BriefGenerator:
    def prompt_snapshot(self, research_pack: dict) -> str:
        return (
            f"Brief generation for {research_pack['keyword']} "
            f"with {len(research_pack['source_summaries'])} sources"
        )

    def generate(self, research_pack: dict) -> dict:
        return {
            "primary_keyword": research_pack["keyword"],
            "secondary_keywords": ["symptoms", "causes", "when to see a doctor"],
            "search_intent": research_pack["intent"],
            "user_problem": "Reader wants a safe, evidence-aware overview.",
            "article_goal": "Explain symptoms, causes, warning signs, and limits of self-assessment.",
            "target_word_count": 1900,
            "tone": "calm, factual, supportive",
            "reading_level": "general audience",
            "outline": [
                {"heading": "What is it?", "level": "h2"},
                {"heading": "What are the main symptoms?", "level": "h2"},
                {"heading": "What causes it?", "level": "h2"},
                {"heading": "When should you see a doctor?", "level": "h2"},
                {"heading": "What should you avoid doing?", "level": "h2"},
                {"heading": "FAQ", "level": "h2"},
            ],
            "required_sections": [
                "introduction",
                "what_it_is",
                "symptoms",
                "possible_causes",
                "when_to_see_doctor",
                "what_not_to_do",
                "faq",
                "conclusion",
                "sources",
            ],
            "prohibited_sections": ["medication dosing", "guaranteed outcomes"],
            "medical_safety_notes": research_pack["recommended_disclaimers"],
            "faq_questions": [
                "How often is considered normal?",
                "Can the symptom persist after treatment?",
                "How is it different from other conditions?",
            ],
            "internal_link_targets": [],
            "schema_type": "Article",
            "meta_guidance": {"include_primary_keyword": True},
            "image_guidance": {"count": 3, "style": "neutral medical editorial illustration"},
        }
