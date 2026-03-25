from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

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


class ManualSourceCreate(BaseModel):
    source_type: str = Field(default="manual")
    title: str
    url: HttpUrl
    author: str | None = None
    published_at: datetime | None = None
    raw_content: str
    cleaned_content: str | None = None
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0)
    ingestion_status: str = Field(default="manual")


class ReadinessItemRead(BaseModel):
    code: str
    label: str
    status: str
    detail: str


class LaunchReadinessRead(BaseModel):
    overall_status: str
    summary: str
    items: list[ReadinessItemRead]
