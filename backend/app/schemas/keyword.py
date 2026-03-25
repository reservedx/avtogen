from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMModel


class KeywordCreate(BaseModel):
    cluster_id: UUID
    keyword: str
    search_intent: str = "informational"
    priority: int = 50
    status: str = "active"
    notes: str | None = None


class KeywordRead(ORMModel):
    id: UUID
    cluster_id: UUID
    keyword: str
    search_intent: str
    priority: int
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
