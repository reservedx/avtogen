from pydantic import BaseModel


class ReviewDecisionRequest(BaseModel):
    reviewer_name: str
    notes: str | None = None


class PipelineRunRequest(BaseModel):
    topic_query: str
    audience: str = "general audience"


class BulkPipelineRunRequest(BaseModel):
    topic_queries: list[str]
    audience: str = "general audience"


class BulkArticleActionRequest(BaseModel):
    article_ids: list[str]
    action: str
    reviewer_name: str | None = None
    notes: str | None = None


class BulkActionResult(BaseModel):
    article_id: str
    status: str
    detail: str | None = None


class BulkArticleActionResponse(BaseModel):
    requested: int
    completed: int
    results: list[BulkActionResult]


class BulkTopicFastLaneRequest(BaseModel):
    topic_ids: list[str]


class BulkTopicActionResult(BaseModel):
    topic_id: str
    status: str
    article_id: str | None = None
    detail: str | None = None


class BulkTopicFastLaneResponse(BaseModel):
    requested: int
    completed: int
    results: list[BulkTopicActionResult]


class DemoBootstrapRequest(BaseModel):
    topic_query: str = "frequent urination with cystitis"
    audience: str = "general audience"
    cluster_name: str = "Demo Cluster"


class DemoBootstrapResponse(BaseModel):
    cluster_id: str
    topic_id: str
    brief_id: str
    article_id: str
    quality_status: str
    quality_score: float
    risk_score: float
    sources_collected: int
    research_notes_extracted: int
    images_generated: int
