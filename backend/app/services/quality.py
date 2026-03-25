from __future__ import annotations

from app.config import settings
from app.domain.enums import QualityOverallStatus


class QualityGateService:
    dangerous_phrases = [
        "guaranteed cure",
        "doctor is not needed",
        "diagnose yourself",
        "safe without a doctor",
    ]
    manual_review_phrases = [
        "treatment plan",
        "dosage",
        "dose",
        "take antibiotics",
        "prescription",
        "self-medicate",
    ]

    def evaluate(
        self,
        markdown_content: str,
        source_count: int,
        internal_link_count: int,
        image_count: int,
        has_meta: bool,
        faq_count: int,
        research_pack: dict | None = None,
        brief: dict | None = None,
    ) -> dict:
        blockers: list[dict] = []
        warnings: list[dict] = []
        quality_score = 100.0
        risk_score = 0.0

        for section in ["## What is it?", "## FAQ", "## Conclusion", "## Sources"]:
            if section not in markdown_content:
                blockers.append(
                    {
                        "code": "missing_section",
                        "message": f"Missing section: {section}",
                        "severity": "blocker",
                    }
                )
                quality_score -= 12

        if len(markdown_content.split()) < 900:
            warnings.append(
                {
                    "code": "low_word_count",
                    "message": "Draft is shorter than brief target.",
                    "severity": "warning",
                }
            )
            quality_score -= 15

        if source_count < settings.required_source_count:
            blockers.append(
                {
                    "code": "insufficient_sources",
                    "message": "At least two sources are required.",
                    "severity": "blocker",
                }
            )
            quality_score -= 20
            risk_score += 25

        if faq_count == 0:
            warnings.append(
                {"code": "empty_faq", "message": "FAQ is empty.", "severity": "warning"}
            )

        if internal_link_count == 0:
            warnings.append(
                {
                    "code": "missing_internal_links",
                    "message": "No internal links attached.",
                    "severity": "warning",
                }
            )

        if image_count == 0:
            warnings.append(
                {
                    "code": "missing_images",
                    "message": "No images attached.",
                    "severity": "warning",
                }
            )

        if not has_meta:
            blockers.append(
                {
                    "code": "missing_metadata",
                    "message": "Meta title or description missing.",
                    "severity": "blocker",
                }
            )

        lowered = markdown_content.lower()
        for phrase in self.dangerous_phrases:
            if phrase in lowered:
                blockers.append(
                    {
                        "code": "dangerous_claim",
                        "message": f"Banned claim detected: {phrase}",
                        "severity": "blocker",
                    }
                )
                risk_score += 30

        for phrase in self.manual_review_phrases:
            if phrase in lowered:
                warnings.append(
                    {
                        "code": "manual_review_medical_claim",
                        "message": f"Manual review required due to medical phrasing: {phrase}",
                        "severity": "warning",
                    }
                )
                risk_score += 18

        if research_pack:
            coverage = self._source_coverage(markdown_content, research_pack)
            if coverage["blocker"]:
                blockers.append(
                    {
                        "code": "source_coverage_weak",
                        "message": coverage["message"],
                        "severity": "blocker",
                    }
                )
                quality_score -= 15
                risk_score += 18
            elif coverage["warning"]:
                warnings.append(
                    {
                        "code": "source_coverage_partial",
                        "message": coverage["message"],
                        "severity": "warning",
                    }
                )
                quality_score -= 8

        if brief:
            missing_required = self._missing_required_sections(markdown_content, brief)
            for item in missing_required:
                warnings.append(
                    {
                        "code": "brief_section_gap",
                        "message": f"Brief-required section not represented clearly: {item}",
                        "severity": "warning",
                    }
                )
                quality_score -= 5

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
            "recommended_actions": self._recommended_actions(blockers, warnings, risk_score),
        }

    def _source_coverage(self, markdown_content: str, research_pack: dict) -> dict:
        lowered = markdown_content.lower()
        entities = [str(item).lower() for item in research_pack.get("important_entities", []) if item]
        matched_entities = [entity for entity in entities if entity in lowered]
        citations = [str(item) for item in research_pack.get("required_citations", []) if item]
        cited_urls = [url for url in citations if url in markdown_content]

        if entities and not matched_entities:
            return {
                "blocker": True,
                "warning": False,
                "message": "Draft does not visibly reflect important research entities.",
            }
        if citations and not cited_urls:
            return {
                "blocker": False,
                "warning": True,
                "message": "Draft does not surface any research citations in the rendered content.",
            }
        return {"blocker": False, "warning": False, "message": ""}

    def _missing_required_sections(self, markdown_content: str, brief: dict) -> list[str]:
        lowered = markdown_content.lower()
        missing: list[str] = []
        for item in brief.get("required_sections", []):
            normalized = str(item).replace("_", " ").lower()
            if normalized not in lowered:
                missing.append(str(item))
        return missing[:4]

    def _recommended_actions(
        self,
        blockers: list[dict],
        warnings: list[dict],
        risk_score: float,
    ) -> list[str]:
        actions = ["Run editorial review"]
        if blockers:
            actions.append("Resolve blockers before publishing")
        if any(item["code"] == "source_coverage_partial" for item in warnings):
            actions.append("Add visible citations or source-backed references")
        if risk_score > settings.max_risk_score_for_auto_publish:
            actions.append("Require manual approval before publishing")
        if any(item["code"] == "brief_section_gap" for item in warnings):
            actions.append("Regenerate weak or missing sections from the brief")
        return actions
