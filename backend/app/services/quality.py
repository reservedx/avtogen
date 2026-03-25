from app.config import settings
from app.domain.enums import QualityOverallStatus


class QualityGateService:
    dangerous_phrases = [
        "guaranteed cure",
        "doctor is not needed",
        "diagnose yourself",
        "safe without a doctor",
    ]

    def evaluate(
        self,
        markdown_content: str,
        source_count: int,
        internal_link_count: int,
        image_count: int,
        has_meta: bool,
        faq_count: int,
    ) -> dict:
        blockers = []
        warnings = []
        quality_score = 100.0
        risk_score = 0.0
        for section in ["## What is it?", "## FAQ", "## Conclusion", "## Sources"]:
            if section not in markdown_content:
                blockers.append({
                    "code": "missing_section",
                    "message": f"Missing section: {section}",
                    "severity": "blocker",
                })
                quality_score -= 12
        if len(markdown_content.split()) < 900:
            warnings.append({
                "code": "low_word_count",
                "message": "Draft is shorter than brief target.",
                "severity": "warning",
            })
            quality_score -= 15
        if source_count < settings.required_source_count:
            blockers.append({
                "code": "insufficient_sources",
                "message": "At least two sources are required.",
                "severity": "blocker",
            })
            quality_score -= 20
            risk_score += 25
        if faq_count == 0:
            warnings.append({"code": "empty_faq", "message": "FAQ is empty.", "severity": "warning"})
        if internal_link_count == 0:
            warnings.append({
                "code": "missing_internal_links",
                "message": "No internal links attached.",
                "severity": "warning",
            })
        if image_count == 0:
            warnings.append({"code": "missing_images", "message": "No images attached.", "severity": "warning"})
        if not has_meta:
            blockers.append({
                "code": "missing_metadata",
                "message": "Meta title or description missing.",
                "severity": "blocker",
            })
        lowered = markdown_content.lower()
        for phrase in self.dangerous_phrases:
            if phrase in lowered:
                blockers.append({
                    "code": "dangerous_claim",
                    "message": f"Banned claim detected: {phrase}",
                    "severity": "blocker",
                })
                risk_score += 30
        status = QualityOverallStatus.passed.value
        if blockers:
            status = QualityOverallStatus.block.value
        elif warnings or risk_score > settings.max_risk_score_for_auto_publish:
            status = QualityOverallStatus.review.value
        return {
            "overall_status": status,
            "quality_score": max(0, quality_score),
            "risk_score": min(100, risk_score),
            "blockers": blockers,
            "warnings": warnings,
            "recommended_actions": ["Run editorial review", "Regenerate weak sections if needed"],
        }
