class ReviewWorkflowService:
    def requires_manual_review(self, markdown_content: str) -> bool:
        risky_terms = ["treatment", "diagnosis", "dose", "antibiotic", "prescription"]
        lowered = markdown_content.lower()
        return any(term in lowered for term in risky_terms)
