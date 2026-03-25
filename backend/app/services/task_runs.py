from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import TaskRun


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TaskRunRecorder:
    def start(self, db: Session, task_type: str, entity_type: str, entity_id: UUID, input_json: dict[str, Any]) -> TaskRun:
        row = TaskRun(
            task_type=task_type,
            entity_type=entity_type,
            entity_id=entity_id,
            status="running",
            input_json=input_json,
            output_json={},
            started_at=utcnow(),
        )
        db.add(row)
        db.flush()
        return row

    def finish(self, db: Session, row: TaskRun, output_json: dict[str, Any]) -> TaskRun:
        row.status = "completed"
        row.output_json = output_json
        row.finished_at = utcnow()
        db.add(row)
        return row

    def fail(self, db: Session, row: TaskRun, error_message: str) -> TaskRun:
        row.status = "failed"
        row.error_message = error_message
        row.finished_at = utcnow()
        db.add(row)
        return row
