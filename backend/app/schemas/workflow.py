from pydantic import BaseModel


class ReviewDecisionRequest(BaseModel):
    reviewer_name: str
    notes: str | None = None


class PipelineRunRequest(BaseModel):
    topic_query: str
    audience: str = "general audience"
