from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ORMModel


class SourceRead(ORMModel):
    id: UUID
    topic_id: UUID
    source_type: str
    url: str
    title: str
    author: str | None
    published_at: datetime | None
    transcript_text: str | None
    raw_content: str | None
    cleaned_content: str | None
    reliability_score: float | None
    ingestion_status: str
    created_at: datetime
    updated_at: datetime


class BriefRead(ORMModel):
    id: UUID
    topic_id: UUID
    version: int
    brief_json: dict
    prompt_snapshot: str
    model_name: str
    created_at: datetime


class ArticleRead(ORMModel):
    id: UUID
    topic_id: UUID
    brief_id: UUID
    current_version_id: UUID | None
    title: str
    slug: str
    status: str
    quality_score: float | None
    risk_score: float | None
    cms_post_id: str | None
    published_url: str | None
    created_at: datetime
    updated_at: datetime


class ArticleVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    article_id: UUID
    version: int
    content_markdown: str
    content_html: str
    excerpt: str | None
    meta_title: str
    meta_description: str
    faq_json: dict
    schema_payload: dict = Field(alias="schema_json")
    word_count: int
    created_by: str
    generation_context: dict
    created_at: datetime


class ImageRead(ORMModel):
    id: UUID
    article_id: UUID
    prompt: str
    alt_text: str
    storage_url: str | None
    local_path: str | None
    width: int | None
    height: int | None
    is_featured: bool
    moderation_status: str
    moderation_notes: str | None
    created_at: datetime


class EditorialReviewRead(ORMModel):
    id: UUID
    article_id: UUID
    article_version_id: UUID
    reviewer_name: str
    decision: str
    notes: str | None
    created_at: datetime


class TaskRunRead(ORMModel):
    id: UUID
    task_type: str
    entity_type: str
    entity_id: UUID
    status: str
    input_json: dict
    output_json: dict
    started_at: datetime
    finished_at: datetime | None
    error_message: str | None


class MetricsRead(BaseModel):
    clusters_count: int
    topics_count: int
    articles_count: int
    published_articles_count: int
    quality_reports_count: int
    task_runs_count: int


class CountBucketRead(BaseModel):
    key: str
    count: int


class AnalyticsSummaryRead(BaseModel):
    article_status_counts: list[CountBucketRead]
    source_type_counts: list[CountBucketRead]
    failed_task_counts: list[CountBucketRead]
    average_quality_score: float | None
    average_risk_score: float | None


class SettingsSummaryRead(BaseModel):
    app_name: str
    app_env: str
    api_prefix: str
    database_url: str
    database_is_sqlite: bool
    asset_storage_backend: str
    asset_storage_dir: str
    s3_bucket: str
    openai_enabled: bool
    auto_publish_enabled: bool
    fast_publish_enabled: bool
    auto_approve_low_risk: bool
    auto_publish_low_risk: bool
    use_stub_generation: bool
    openai_brief_model: str
    openai_draft_model: str
    openai_image_model: str
    min_quality_score: float
    max_risk_score_for_auto_publish: float
    fast_lane_min_quality_score: float
    fast_lane_max_risk_score: float
    required_source_count: int
    similarity_threshold: float


class RegenerateSectionRequest(BaseModel):
    section_heading: str = Field(default="FAQ")
    instructions: str | None = None


class ManualArticleVersionCreate(BaseModel):
    title: str | None = None
    slug: str | None = None
    excerpt: str | None = None
    meta_title: str
    meta_description: str
    content_markdown: str
    editor_name: str = Field(default="Editor")
    change_note: str | None = None


class ImageModerationRequest(BaseModel):
    moderator_name: str = Field(default="Editor")
    notes: str | None = None


class QualityReportRead(ORMModel):
    id: UUID
    article_version_id: UUID
    report_json: dict
    quality_score: float
    risk_score: float
    blocking_issues_count: int
    warning_count: int
    created_at: datetime


class PublishingJobRead(ORMModel):
    id: UUID
    article_id: UUID
    target_system: str
    status: str
    request_payload: dict
    response_payload: dict
    retry_count: int
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class ArticleWorkspaceRead(BaseModel):
    article: ArticleRead
    current_version: ArticleVersionRead | None
    versions: list[ArticleVersionRead]
    images: list[ImageRead]
    latest_quality_report: QualityReportRead | None
    publishing_job: PublishingJobRead | None
    editorial_reviews: list[EditorialReviewRead]
    topic: dict | None = None
    sources: list[dict] = []
    research_notes: list[dict] = []
    brief: dict | None = None
