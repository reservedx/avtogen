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
    created_at: datetime
    updated_at: datetime


class TopicWorkspaceRead(BaseModel):
    topic: TopicRead
    sources: list[dict]
    research_notes: list[dict]
    briefs: list[dict]
    articles: list[dict]
