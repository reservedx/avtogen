from __future__ import annotations

from app.config import settings


class RiskTierService:
    high_risk_terms = [
        "treatment",
        "лечени",
        "diagnosis",
        "диагноз",
        "dose",
        "dosage",
        "antibiotic",
        "антибиот",
        "prescription",
        "препарат",
        "medicine",
        "medication",
        "беремен",
        "pregnan",
    ]
    medium_risk_terms = [
        "blood",
        "fever",
        "pain",
        "infection",
        "discharge",
        "burning",
        "боль",
        "кров",
        "температур",
        "инфек",
        "жжение",
    ]

    def classify(self, *parts: str | None) -> str:
        lowered = " ".join(part or "" for part in parts).lower()
        if any(term in lowered for term in self.high_risk_terms):
            return "high"
        if any(term in lowered for term in self.medium_risk_terms):
            return "medium"
        return "low"

    def fast_lane_eligible(self, risk_tier: str, quality_report: dict) -> bool:
        if not settings.fast_publish_enabled:
            return False
        if risk_tier != "low":
            return False
        if quality_report.get("blockers"):
            return False
        if float(quality_report.get("quality_score", 0.0)) < settings.fast_lane_min_quality_score:
            return False
        if float(quality_report.get("risk_score", 100.0)) > settings.fast_lane_max_risk_score:
            return False
        return True
