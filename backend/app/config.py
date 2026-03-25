from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.example"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="Women Health Content Platform", alias="APP_NAME")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    database_url: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5432/women_health", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    s3_endpoint_url: str = Field(default="http://localhost:9000", alias="S3_ENDPOINT_URL")
    s3_access_key: str = Field(default="minio", alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(default="minio123", alias="S3_SECRET_KEY")
    s3_bucket: str = Field(default="article-assets", alias="S3_BUCKET")
    openai_api_key: str = Field(default="changeme", alias="OPENAI_API_KEY")
    openai_brief_model: str = Field(default="gpt-5.4-mini", alias="OPENAI_BRIEF_MODEL")
    openai_draft_model: str = Field(default="gpt-5.4", alias="OPENAI_DRAFT_MODEL")
    openai_image_model: str = Field(default="gpt-image-1", alias="OPENAI_IMAGE_MODEL")
    auto_publish_enabled: bool = Field(default=False, alias="AUTO_PUBLISH_ENABLED")
    min_quality_score: float = Field(default=78, alias="MIN_QUALITY_SCORE")
    max_risk_score_for_auto_publish: float = Field(default=20, alias="MAX_RISK_SCORE_FOR_AUTO_PUBLISH")
    required_source_count: int = Field(default=2, alias="REQUIRED_SOURCE_COUNT")
    similarity_threshold: float = Field(default=0.86, alias="SIMILARITY_THRESHOLD")
    wordpress_base_url: str = Field(default="https://example.com", alias="WORDPRESS_BASE_URL")
    wordpress_username: str = Field(default="editor", alias="WORDPRESS_USERNAME")
    wordpress_app_password: str = Field(default="changeme", alias="WORDPRESS_APP_PASSWORD")
    use_stub_generation: bool = Field(default=True, alias="USE_STUB_GENERATION")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
