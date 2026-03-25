from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMModel


class TopicCreate(BaseModel):
    cluster_id: UUID
    keyword_id: UUID | None = None
    working_title: str
    target_query: str
    audience: str
    content_type: str = "blog_post"


class TopicRead(ORMModel):
    id: UUID
    cluster_id: UUID
    keyword_id: UUID | None
    working_title: str
    target_query: str
    audience: str
    content_type: str
    status: str
    cannibalization_hash: str | None
    created_at: datetime
    updated_at: datetime


class TopicWorkspaceRead(BaseModel):
    topic: TopicRead
    sources: list[dict]
    research_notes: list[dict]
    briefs: list[dict]
    articles: list[dict]


class BulkTopicCreateRequest(BaseModel):
    cluster_id: UUID | None = None
    cluster_name: str = "Bulk Imported Topics"
    audience: str = "general audience"
    content_type: str = "blog_post"
    topic_queries: list[str]


class BulkTopicCreateResult(BaseModel):
    topic_id: str
    working_title: str
    status: str


class BulkTopicCreateResponse(BaseModel):
    cluster_id: str
    created: int
    skipped: int
    results: list[BulkTopicCreateResult]


class CannibalizationMatchRead(BaseModel):
    entity_id: str | None
    entity_type: str
    title: str | None
    slug: str | None
    similarity_score: float
    slug_overlap: bool


class CannibalizationReportRead(BaseModel):
    topic_id: UUID
    candidate_text: str
    flagged: bool
    max_score: float
    matches: list[CannibalizationMatchRead]
