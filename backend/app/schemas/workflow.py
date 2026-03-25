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
