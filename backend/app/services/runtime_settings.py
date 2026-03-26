from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import RuntimeConfig

RUNTIME_CONFIG_KEY = "default"
MUTABLE_RUNTIME_FIELDS = {
    "auto_publish_enabled": bool,
    "fast_publish_enabled": bool,
    "auto_approve_low_risk": bool,
    "auto_publish_low_risk": bool,
    "use_stub_generation": bool,
    "min_quality_score": float,
    "max_risk_score_for_auto_publish": float,
    "fast_lane_min_quality_score": float,
    "fast_lane_max_risk_score": float,
    "required_source_count": int,
    "similarity_threshold": float,
    "default_medical_disclaimer": str,
}


def runtime_settings_snapshot() -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for field in MUTABLE_RUNTIME_FIELDS:
        snapshot[field] = getattr(settings, field)
    return snapshot


def apply_runtime_overrides(overrides: dict[str, Any]) -> None:
    for key, caster in MUTABLE_RUNTIME_FIELDS.items():
        if key not in overrides:
            continue
        value = overrides[key]
        if value is None:
            continue
        if caster is bool:
            coerced = bool(value)
        elif caster is int:
            coerced = int(value)
        elif caster is float:
            coerced = float(value)
        else:
            coerced = str(value)
        setattr(settings, key, coerced)


def load_runtime_overrides(db: Session) -> dict[str, Any]:
    row = db.get(RuntimeConfig, RUNTIME_CONFIG_KEY)
    overrides = row.settings_json if row and isinstance(row.settings_json, dict) else {}
    apply_runtime_overrides(overrides)
    return overrides


def runtime_override_keys(db: Session) -> list[str]:
    row = db.get(RuntimeConfig, RUNTIME_CONFIG_KEY)
    if not row or not isinstance(row.settings_json, dict):
        return []
    return sorted(row.settings_json.keys())


def save_runtime_overrides(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    row = db.get(RuntimeConfig, RUNTIME_CONFIG_KEY)
    if not row:
        row = RuntimeConfig(key=RUNTIME_CONFIG_KEY, settings_json={})
        db.add(row)
        db.flush()

    current = row.settings_json if isinstance(row.settings_json, dict) else {}
    for key in MUTABLE_RUNTIME_FIELDS:
        if key in payload:
            current[key] = payload[key]
    row.settings_json = current
    apply_runtime_overrides(current)
    db.commit()
    db.refresh(row)
    return row.settings_json
