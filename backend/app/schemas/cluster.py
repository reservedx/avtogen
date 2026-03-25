from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMModel


class ClusterCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    parent_cluster_id: UUID | None = None


class ClusterRead(ORMModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    parent_cluster_id: UUID | None
    created_at: datetime
    updated_at: datetime
