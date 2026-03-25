from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMModel


class ResearchNoteRead(ORMModel):
    id: UUID
    topic_id: UUID
    source_id: UUID | None
    fact_type: str
    content: str
    confidence_score: float
    citation_data: dict
    created_at: datetime


class ResearchNoteExtractionResponse(BaseModel):
    extracted: int
