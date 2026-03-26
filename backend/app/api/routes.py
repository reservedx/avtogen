from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.application.pipeline_service import PipelineService
from app.config import settings
from app.db.models import Article, ArticleVersion, Brief, Cluster, ContentTopic, EditorialReview, Image, Keyword, PublishingJob, QualityReport, ResearchNote, Source, TaskRun
from app.db.session import get_db
from app.schemas.article import AnalyticsSummaryRead, ArticleRead, ArticleVersionRead, ArticleWorkspaceRead, BriefRead, EditorialReviewRead, ImageModerationRequest, ImageRead, ImageReviewQueueItemRead, ManualArticleVersionCreate, MetricsRead, PublishingJobRead, QualityReportRead, RegenerateSectionRequest, RuntimeSettingsUpdate, SettingsSummaryRead, SourceRead, TaskRunRead
from app.schemas.auth import AuthSessionRead
from app.schemas.cluster import ClusterCreate, ClusterRead
from app.schemas.keyword import KeywordCreate, KeywordRead
from app.schemas.research import LaunchReadinessRead, ManualSourceCreate, ResearchNoteExtractionResponse, ResearchNoteRead
from app.schemas.topic import BulkTopicCreateRequest, BulkTopicCreateResponse, BulkTopicCreateResult, CannibalizationReportRead, TopicCreate, TopicRead, TopicWorkspaceRead
from app.schemas.workflow import BulkActionResult, BulkArticleActionRequest, BulkArticleActionResponse, BulkImageModerationRequest, BulkImageModerationResponse, BulkImageModerationResult, BulkPipelineRunRequest, BulkTopicActionResult, BulkTopicFastLaneRequest, BulkTopicFastLaneResponse, DemoBootstrapRequest, DemoBootstrapResponse, PipelineRunRequest, ReviewDecisionRequest
from app.services.auth import ROLE_CAPABILITIES, get_current_role, require_role
from app.services.platform import ArticleSectionRegenerator, BriefGenerator, DraftGenerator, ImageGenerator, InterlinkingService, LaunchReadinessService, ManualSourceProvider, OpenAIGateway, PublishingService, QualityGateService, ResearchNoteExtractor, ResearchPackBuilder, RiskTierService, YouTubeTranscriptProvider
from app.services.runtime_settings import runtime_override_keys, runtime_settings_snapshot, save_runtime_overrides

router = APIRouter()


def _fact_rows(db: Session, topic_id: UUID) -> list[dict]:
    notes = db.query(ResearchNote).filter(ResearchNote.topic_id == topic_id).order_by(ResearchNote.created_at.asc()).all()
    return [
        {
            "fact_type": note.fact_type,
            "content": note.content,
            "confidence_score": note.confidence_score,
            "citations": [note.citation_data] if note.citation_data else [],
        }
        for note in notes
    ]


def _run_quality_check_for_article(db: Session, article: Article) -> dict:
    if not article.current_version_id:
        raise HTTPException(status_code=404, detail="Article not found")
    version = db.get(ArticleVersion, article.current_version_id)
    image_count = db.query(Image).filter(Image.article_id == article.id).count()
    topic = db.get(ContentTopic, article.topic_id)
    source_rows = [
        {
            "source_type": source.source_type,
            "url": source.url,
            "title": source.title,
            "summary": source.cleaned_content or source.raw_content or "",
            "reliability_score": source.reliability_score,
            "published_at": source.published_at,
        }
        for source in db.query(Source).filter(Source.topic_id == article.topic_id).all()
    ]
    brief_row = db.get(Brief, article.brief_id)
    research_pack = None
    risk_tier = "medium"
    if topic:
        risk_tier = RiskTierService().classify(topic.working_title, topic.target_query, version.content_markdown)
        research_pack = ResearchPackBuilder().build(
            topic.working_title,
            topic.target_query,
            topic.audience,
            "informational",
            source_rows,
            _fact_rows(db, topic.id),
        )
    report = QualityGateService().evaluate(
        version.content_markdown,
        source_count=len(source_rows),
        internal_link_count=0,
        image_count=image_count,
        has_meta=bool(version.meta_title and version.meta_description),
        faq_count=len(version.faq_json.get("items", [])),
        research_pack=research_pack,
        brief=brief_row.brief_json if brief_row else None,
        risk_tier=risk_tier,
    )
    row = QualityReport(
        article_version_id=version.id,
        report_json=report,
        quality_score=report["quality_score"],
        risk_score=report["risk_score"],
        blocking_issues_count=len(report["blockers"]),
        warning_count=len(report["warnings"]),
    )
    article.quality_score = report["quality_score"]
    article.risk_score = report["risk_score"]
    db.add(row)
    return report


def _research_pack_for_topic(db: Session, topic: ContentTopic) -> tuple[dict, list[Source]]:
    topic_sources = db.query(Source).filter(Source.topic_id == topic.id).order_by(Source.created_at.asc()).all()
    source_rows = [
        {
            "source_type": source.source_type,
            "url": source.url,
            "title": source.title,
            "reliability_score": source.reliability_score,
            "summary": source.cleaned_content or source.raw_content or "",
            "published_at": source.published_at,
        }
        for source in topic_sources
    ]
    research_pack = ResearchPackBuilder().build(
        topic.working_title,
        topic.target_query,
        topic.audience,
        "informational",
        source_rows,
        _fact_rows(db, topic.id),
    )
    return research_pack, topic_sources


def _ensure_topic_sources(db: Session, topic: ContentTopic) -> list[Source]:
    existing = db.query(Source).filter(Source.topic_id == topic.id).all()
    if existing:
        return existing
    providers = [YouTubeTranscriptProvider(), ManualSourceProvider()]
    collected: list[dict] = []
    for provider in providers:
        collected.extend(provider.collect(topic.target_query))
    existing_urls: set[str] = set()
    for item in collected:
        if item["url"] in existing_urls:
            continue
        existing_urls.add(item["url"])
        db.add(Source(topic_id=topic.id, **item))
    db.flush()
    topic_sources = db.query(Source).filter(Source.topic_id == topic.id).all()
    ResearchNoteExtractor().extract_for_topic(db, topic.id, topic_sources)
    db.flush()
    return topic_sources


def _apply_fast_lane_outcome(
    db: Session,
    article: Article,
    version: ArticleVersion,
    topic: ContentTopic,
    report: dict,
    images: list[Image] | None = None,
) -> None:
    risk_tier = report.get("risk_tier", RiskTierService().classify(topic.working_title, topic.target_query, version.content_markdown))
    fast_lane = RiskTierService().fast_lane_eligible(risk_tier, report)
    if fast_lane and settings.auto_approve_low_risk:
        article.status = "approved"
        if settings.auto_publish_low_risk and settings.auto_publish_enabled:
            publish_images = images if images is not None else db.query(Image).filter(Image.article_id == article.id).all()
            response = PublishingService().publish_article(article, version, publish_images)
            remote_post = response["post"]
            article.cms_post_id = str(remote_post["id"])
            article.published_url = remote_post.get("link")
            article.status = "published"


def _create_article_for_topic(db: Session, topic: ContentTopic, brief: Brief, research_pack: dict) -> tuple[Article, ArticleVersion]:
    gateway = OpenAIGateway()
    draft_generator = DraftGenerator()
    draft = gateway.generate_draft_json(brief.brief_json, research_pack) or draft_generator.generate(brief.brief_json, research_pack)
    article = Article(topic_id=topic.id, brief_id=brief.id, title=draft["title"], slug=draft["slug"], status="draft")
    db.add(article)
    db.flush()
    version = ArticleVersion(
        article_id=article.id,
        version=1,
        content_markdown=draft["content_markdown"],
        content_html=draft["content_html"],
        excerpt=draft["excerpt"],
        meta_title=draft["meta_title"],
        meta_description=draft["meta_description"],
        faq_json=draft["faq_json"],
        schema_json=draft["schema_json"],
        word_count=len(draft["content_markdown"].split()),
        created_by="system",
        generation_context={
            "brief_id": str(brief.id),
            "generation_mode": "openai" if gateway.enabled else "stub",
            "image_prompts": draft["image_prompts"],
            "alt_texts": draft["alt_texts"],
        },
    )
    db.add(version)
    db.flush()
    article.current_version_id = version.id
    return article, version


def _ensure_article_images(db: Session, article: Article) -> list[Image]:
    existing = db.query(Image).filter(Image.article_id == article.id).order_by(Image.created_at.asc()).all()
    if existing:
        return existing
    created: list[Image] = []
    for image_payload in ImageGenerator().generate(article.title, article.slug):
        image = Image(article_id=article.id, moderation_status="generated", **image_payload)
        db.add(image)
        created.append(image)
    db.flush()
    return created


def _approved_images_ready(images: list[Image]) -> bool:
    if not images:
        return False
    featured = [image for image in images if image.is_featured]
    if not featured:
        return False
    return all(image.moderation_status == "approved" for image in images) and all(image.moderation_status == "approved" for image in featured)


def _regenerate_image_asset(image: Image, db: Session) -> None:
    image.moderation_status = "needs_regeneration"
    article = db.get(Article, image.article_id)
    if not article:
        return
    regenerated = ImageGenerator().generate(article.title, article.slug)
    replacement_payload = next(
        (
            item for item in regenerated
            if bool(item.get("is_featured")) == bool(image.is_featured)
        ),
        regenerated[0] if regenerated else None,
    )
    if replacement_payload:
        image.prompt = replacement_payload["prompt"]
        image.alt_text = replacement_payload["alt_text"]
        image.storage_url = replacement_payload.get("storage_url")
        image.local_path = replacement_payload.get("local_path")
        image.width = replacement_payload.get("width")
        image.height = replacement_payload.get("height")
        image.moderation_status = "generated"


@router.get("/settings", response_model=SettingsSummaryRead)
def get_settings_summary(db: Session = Depends(get_db)) -> SettingsSummaryRead:
    runtime_snapshot = runtime_settings_snapshot()
    return SettingsSummaryRead(
        app_name=settings.app_name,
        app_env=settings.app_env,
        api_prefix=settings.api_prefix,
        database_url=settings.database_url,
        database_is_sqlite=settings.database_is_sqlite,
        asset_storage_backend=settings.asset_storage_backend,
        asset_storage_dir=settings.asset_storage_dir,
        s3_bucket=settings.s3_bucket,
        openai_enabled=settings.openai_enabled,
        auto_publish_enabled=settings.auto_publish_enabled,
        fast_publish_enabled=settings.fast_publish_enabled,
        auto_approve_low_risk=settings.auto_approve_low_risk,
        auto_publish_low_risk=settings.auto_publish_low_risk,
        use_stub_generation=settings.use_stub_generation,
        openai_brief_model=settings.openai_brief_model,
        openai_draft_model=settings.openai_draft_model,
        openai_image_model=settings.openai_image_model,
        min_quality_score=settings.min_quality_score,
        max_risk_score_for_auto_publish=settings.max_risk_score_for_auto_publish,
        fast_lane_min_quality_score=settings.fast_lane_min_quality_score,
        fast_lane_max_risk_score=settings.fast_lane_max_risk_score,
        required_source_count=settings.required_source_count,
        similarity_threshold=settings.similarity_threshold,
        default_medical_disclaimer=settings.default_medical_disclaimer,
        runtime_override_keys=runtime_override_keys(db),
    )


@router.get("/auth/session", response_model=AuthSessionRead)
def get_auth_session(current_role: str = Depends(get_current_role)) -> AuthSessionRead:
    return AuthSessionRead(
        role=current_role,
        auth_enabled=settings.auth_enabled,
        allowed_capabilities=ROLE_CAPABILITIES.get(current_role, []),
    )


@router.post("/settings/runtime", response_model=SettingsSummaryRead, dependencies=[Depends(require_role("admin"))])
def update_runtime_settings(payload: RuntimeSettingsUpdate, db: Session = Depends(get_db)) -> SettingsSummaryRead:
    save_runtime_overrides(db, payload.model_dump())
    runtime_snapshot = runtime_settings_snapshot()
    return SettingsSummaryRead(
        app_name=settings.app_name,
        app_env=settings.app_env,
        api_prefix=settings.api_prefix,
        database_url=settings.database_url,
        database_is_sqlite=settings.database_is_sqlite,
        asset_storage_backend=settings.asset_storage_backend,
        asset_storage_dir=settings.asset_storage_dir,
        s3_bucket=settings.s3_bucket,
        openai_enabled=settings.openai_enabled,
        auto_publish_enabled=settings.auto_publish_enabled,
        fast_publish_enabled=settings.fast_publish_enabled,
        auto_approve_low_risk=settings.auto_approve_low_risk,
        auto_publish_low_risk=settings.auto_publish_low_risk,
        use_stub_generation=settings.use_stub_generation,
        openai_brief_model=settings.openai_brief_model,
        openai_draft_model=settings.openai_draft_model,
        openai_image_model=settings.openai_image_model,
        min_quality_score=settings.min_quality_score,
        max_risk_score_for_auto_publish=settings.max_risk_score_for_auto_publish,
        fast_lane_min_quality_score=settings.fast_lane_min_quality_score,
        fast_lane_max_risk_score=settings.fast_lane_max_risk_score,
        required_source_count=settings.required_source_count,
        similarity_threshold=settings.similarity_threshold,
        default_medical_disclaimer=settings.default_medical_disclaimer,
        runtime_override_keys=runtime_override_keys(db),
    )


@router.get("/metrics", response_model=MetricsRead)
def get_metrics(db: Session = Depends(get_db)) -> MetricsRead:
    return MetricsRead(
        clusters_count=db.query(Cluster).count(),
        topics_count=db.query(ContentTopic).count(),
        articles_count=db.query(Article).count(),
        published_articles_count=db.query(Article).filter(Article.status == "published").count(),
        quality_reports_count=db.query(QualityReport).count(),
        task_runs_count=db.query(TaskRun).count(),
    )


@router.get("/launch-readiness", response_model=LaunchReadinessRead)
def get_launch_readiness(db: Session = Depends(get_db)) -> LaunchReadinessRead:
    return LaunchReadinessRead(
        **LaunchReadinessService().evaluate(
            topics_count=db.query(ContentTopic).count(),
            articles_count=db.query(Article).count(),
            published_articles_count=db.query(Article).filter(Article.status == "published").count(),
        )
    )


@router.get("/analytics/summary", response_model=AnalyticsSummaryRead)
def get_analytics_summary(db: Session = Depends(get_db)) -> AnalyticsSummaryRead:
    article_status_counts = [
        {"key": str(status), "count": int(count)}
        for status, count in db.query(Article.status, func.count(Article.id)).group_by(Article.status).all()
    ]
    source_type_counts = [
        {"key": str(source_type), "count": int(count)}
        for source_type, count in db.query(Source.source_type, func.count(Source.id)).group_by(Source.source_type).all()
    ]
    failed_task_counts = [
        {"key": str(task_type), "count": int(count)}
        for task_type, count in db.query(TaskRun.task_type, func.count(TaskRun.id)).filter(TaskRun.status == "failed").group_by(TaskRun.task_type).all()
    ]
    avg_quality = db.query(func.avg(Article.quality_score)).scalar()
    avg_risk = db.query(func.avg(Article.risk_score)).scalar()
    return AnalyticsSummaryRead(
        article_status_counts=article_status_counts,
        source_type_counts=source_type_counts,
        failed_task_counts=failed_task_counts,
        average_quality_score=round(float(avg_quality), 2) if avg_quality is not None else None,
        average_risk_score=round(float(avg_risk), 2) if avg_risk is not None else None,
    )


@router.get("/task-runs", response_model=list[TaskRunRead])
def list_task_runs(db: Session = Depends(get_db)) -> list[TaskRun]:
    return db.query(TaskRun).order_by(TaskRun.started_at.desc()).limit(100).all()


@router.post("/clusters", response_model=ClusterRead, dependencies=[Depends(require_role("admin", "editor", "operator"))])
def create_cluster(payload: ClusterCreate, db: Session = Depends(get_db)) -> Cluster:
    cluster = Cluster(**payload.model_dump())
    db.add(cluster)
    db.commit()
    db.refresh(cluster)
    return cluster


@router.get("/clusters", response_model=list[ClusterRead])
def list_clusters(db: Session = Depends(get_db)) -> list[Cluster]:
    return db.query(Cluster).order_by(Cluster.created_at.desc()).all()


@router.post("/keywords", response_model=KeywordRead, dependencies=[Depends(require_role("admin", "editor", "operator"))])
def create_keyword(payload: KeywordCreate, db: Session = Depends(get_db)) -> Keyword:
    cluster = db.get(Cluster, payload.cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    keyword = Keyword(**payload.model_dump())
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword


@router.get("/keywords", response_model=list[KeywordRead])
def list_keywords(cluster_id: UUID | None = None, db: Session = Depends(get_db)) -> list[Keyword]:
    query = db.query(Keyword)
    if cluster_id:
        query = query.filter(Keyword.cluster_id == cluster_id)
    return query.order_by(Keyword.priority.desc(), Keyword.created_at.desc()).all()


@router.post("/topics", response_model=TopicRead, dependencies=[Depends(require_role("admin", "editor", "operator"))])
def create_topic(payload: TopicCreate, db: Session = Depends(get_db)) -> ContentTopic:
    topic = ContentTopic(**payload.model_dump())
    topic.cannibalization_hash = InterlinkingService().cannibalization_hash(f"{topic.working_title} {topic.target_query}")
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@router.post("/topics/bulk-create", response_model=BulkTopicCreateResponse, dependencies=[Depends(require_role("admin", "editor", "operator"))])
def bulk_create_topics(payload: BulkTopicCreateRequest, db: Session = Depends(get_db)) -> BulkTopicCreateResponse:
    cluster = db.get(Cluster, payload.cluster_id) if payload.cluster_id else None
    if payload.cluster_id and not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    if not cluster:
        cluster_slug = InterlinkingService()._slug_like(payload.cluster_name)[:255]
        cluster = db.query(Cluster).filter(Cluster.slug == cluster_slug).first()
        if not cluster:
            cluster = Cluster(name=payload.cluster_name, slug=cluster_slug, description="Bulk imported topic cluster")
            db.add(cluster)
            db.flush()

    created = 0
    skipped = 0
    results: list[BulkTopicCreateResult] = []
    existing_queries = {
        item.target_query.strip().lower()
        for item in db.query(ContentTopic).filter(ContentTopic.cluster_id == cluster.id).all()
    }
    for raw_query in payload.topic_queries[:200]:
        topic_query = raw_query.strip()
        if not topic_query:
            continue
        normalized = topic_query.lower()
        if normalized in existing_queries:
            skipped += 1
            continue
        topic = ContentTopic(
            cluster_id=cluster.id,
            working_title=topic_query[:255],
            target_query=topic_query[:255],
            audience=payload.audience,
            content_type=payload.content_type,
            status="planned",
            cannibalization_hash=InterlinkingService().cannibalization_hash(topic_query),
        )
        db.add(topic)
        db.flush()
        existing_queries.add(normalized)
        created += 1
        results.append(BulkTopicCreateResult(topic_id=str(topic.id), working_title=topic.working_title, status=topic.status))
    db.commit()
    return BulkTopicCreateResponse(cluster_id=str(cluster.id), created=created, skipped=skipped, results=results)


@router.get("/topics", response_model=list[TopicRead])
def list_topics(db: Session = Depends(get_db)) -> list[ContentTopic]:
    return db.query(ContentTopic).order_by(ContentTopic.created_at.desc()).all()


@router.get("/topics/{topic_id}", response_model=TopicRead)
def get_topic(topic_id: UUID, db: Session = Depends(get_db)) -> ContentTopic:
    topic = db.get(ContentTopic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.get("/topics/{topic_id}/workspace", response_model=TopicWorkspaceRead)
def get_topic_workspace(topic_id: UUID, db: Session = Depends(get_db)) -> TopicWorkspaceRead:
    topic = db.get(ContentTopic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    sources = db.query(Source).filter(Source.topic_id == topic_id).order_by(Source.created_at.asc()).all()
    research_notes = db.query(ResearchNote).filter(ResearchNote.topic_id == topic_id).order_by(ResearchNote.created_at.asc()).all()
    briefs = db.query(Brief).filter(Brief.topic_id == topic_id).order_by(Brief.version.desc()).all()
    articles = db.query(Article).filter(Article.topic_id == topic_id).order_by(Article.created_at.desc()).all()
    return TopicWorkspaceRead(
        topic=TopicRead.model_validate(topic),
        sources=[SourceRead.model_validate(source).model_dump(mode="json") for source in sources],
        research_notes=[ResearchNoteRead.model_validate(note).model_dump(mode="json") for note in research_notes],
        briefs=[BriefRead.model_validate(brief).model_dump(mode="json") for brief in briefs],
        articles=[ArticleRead.model_validate(article).model_dump(mode="json") for article in articles],
    )


@router.get("/topics/{topic_id}/cannibalization-check", response_model=CannibalizationReportRead)
def check_topic_cannibalization(topic_id: UUID, db: Session = Depends(get_db)) -> CannibalizationReportRead:
    topic = db.get(ContentTopic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    interlinking = InterlinkingService()
    existing_items = [
        {
            "entity_id": str(other.id),
            "entity_type": "topic",
            "title": other.working_title,
            "slug": None,
            "comparison_text": f"{other.working_title} {other.target_query}",
        }
        for other in db.query(ContentTopic).filter(ContentTopic.id != topic.id).all()
    ]
    existing_items.extend(
        [
            {
                "entity_id": str(article.id),
                "entity_type": "article",
                "title": article.title,
                "slug": article.slug,
                "comparison_text": article.title,
            }
            for article in db.query(Article).filter(Article.status == "published").all()
        ]
    )
    candidate_text = f"{topic.working_title} {topic.target_query}"
    report = interlinking.find_cannibalization_candidates(candidate_text, existing_items)
    return CannibalizationReportRead(topic_id=topic.id, candidate_text=candidate_text, **report)


@router.post("/topics/{topic_id}/collect-sources", dependencies=[Depends(require_role("admin", "editor", "operator"))])
def collect_sources(topic_id: UUID, db: Session = Depends(get_db)) -> dict:
    topic = db.get(ContentTopic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    providers = [YouTubeTranscriptProvider(), ManualSourceProvider()]
    collected = []
    existing_urls = {
        source.url for source in db.query(Source).filter(Source.topic_id == topic.id).all()
    }
    for provider in providers:
        collected.extend(provider.collect(topic.target_query))
    inserted = 0
    for item in collected:
        if item["url"] in existing_urls:
            continue
        db.add(Source(topic_id=topic.id, **item))
        inserted += 1
    db.flush()
    topic_sources = db.query(Source).filter(Source.topic_id == topic.id).all()
    extracted_notes = ResearchNoteExtractor().extract_for_topic(db, topic.id, topic_sources)
    db.commit()
    return {
        "collected": inserted,
        "skipped_duplicates": len(collected) - inserted,
        "research_notes_extracted": len(extracted_notes),
    }


@router.get("/topics/{topic_id}/sources", response_model=list[SourceRead])
def list_sources(topic_id: UUID, db: Session = Depends(get_db)) -> list[Source]:
    return db.query(Source).filter(Source.topic_id == topic_id).all()


@router.post("/topics/{topic_id}/sources/manual", response_model=SourceRead, dependencies=[Depends(require_role("admin", "editor", "operator"))])
def create_manual_source(topic_id: UUID, payload: ManualSourceCreate, db: Session = Depends(get_db)) -> Source:
    topic = db.get(ContentTopic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    if db.query(Source).filter(Source.topic_id == topic_id, Source.url == str(payload.url)).first():
        raise HTTPException(status_code=409, detail="Source with this URL already exists for the topic")
    source = Source(
        topic_id=topic.id,
        source_type=payload.source_type,
        url=str(payload.url),
        title=payload.title,
        author=payload.author,
        published_at=payload.published_at,
        raw_content=payload.raw_content,
        cleaned_content=payload.cleaned_content or payload.raw_content,
        reliability_score=payload.reliability_score,
        ingestion_status=payload.ingestion_status,
    )
    db.add(source)
    db.flush()
    ResearchNoteExtractor().extract_for_topic(db, topic.id, [source])
    db.commit()
    db.refresh(source)
    return source


@router.post("/topics/{topic_id}/extract-research-notes", response_model=ResearchNoteExtractionResponse, dependencies=[Depends(require_role("admin", "editor", "operator"))])
def extract_research_notes(topic_id: UUID, db: Session = Depends(get_db)) -> ResearchNoteExtractionResponse:
    topic = db.get(ContentTopic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    sources = db.query(Source).filter(Source.topic_id == topic.id).all()
    notes = ResearchNoteExtractor().extract_for_topic(db, topic.id, sources)
    db.commit()
    return ResearchNoteExtractionResponse(extracted=len(notes))


@router.get("/topics/{topic_id}/research-notes", response_model=list[ResearchNoteRead])
def list_research_notes(topic_id: UUID, db: Session = Depends(get_db)) -> list[ResearchNote]:
    return db.query(ResearchNote).filter(ResearchNote.topic_id == topic_id).order_by(ResearchNote.created_at.asc()).all()


@router.post("/topics/bulk-fast-lane", response_model=BulkTopicFastLaneResponse, dependencies=[Depends(require_role("admin", "editor", "operator"))])
def bulk_fast_lane_topics(payload: BulkTopicFastLaneRequest, db: Session = Depends(get_db)) -> BulkTopicFastLaneResponse:
    topic_ids = [item.strip() for item in payload.topic_ids if item.strip()]
    if not topic_ids:
        raise HTTPException(status_code=400, detail="At least one topic_id is required")
    results: list[BulkTopicActionResult] = []
    completed = 0
    for topic_id in topic_ids[:50]:
        try:
            topic = db.get(ContentTopic, UUID(topic_id))
        except ValueError:
            topic = None
        if not topic:
            results.append(BulkTopicActionResult(topic_id=topic_id, status="skipped", detail="Topic not found"))
            continue
        try:
            _ensure_topic_sources(db, topic)
            brief = db.query(Brief).filter(Brief.topic_id == topic.id).order_by(Brief.version.desc()).first()
            if not brief:
                research_pack, _ = _research_pack_for_topic(db, topic)
                generator = BriefGenerator()
                gateway = OpenAIGateway()
                brief_payload = gateway.generate_brief_json(research_pack) or generator.generate(research_pack)
                brief = Brief(
                    topic_id=topic.id,
                    version=db.query(Brief).filter(Brief.topic_id == topic.id).count() + 1,
                    brief_json=brief_payload,
                    prompt_snapshot=generator.prompt_snapshot(research_pack),
                    model_name=settings.openai_brief_model if gateway.enabled else "stub",
                )
                db.add(brief)
                db.flush()
            research_pack, _ = _research_pack_for_topic(db, topic)
            article, version = _create_article_for_topic(db, topic, brief, research_pack)
            report = _run_quality_check_for_article(db, article)
            _apply_fast_lane_outcome(db, article, version, topic, report)
            completed += 1
            results.append(
                BulkTopicActionResult(
                    topic_id=topic_id,
                    article_id=str(article.id),
                    status=article.status,
                    detail=f"risk_tier={report.get('risk_tier')} fast_lane={report.get('fast_lane_eligible')}",
                )
            )
        except Exception as exc:
            results.append(BulkTopicActionResult(topic_id=topic_id, status="failed", detail=str(exc)))
    db.commit()
    return BulkTopicFastLaneResponse(requested=len(topic_ids[:50]), completed=completed, results=results)


@router.post("/topics/{topic_id}/generate-brief", dependencies=[Depends(require_role("admin", "editor", "operator"))])
def generate_brief(topic_id: UUID, db: Session = Depends(get_db)) -> dict:
    topic = db.get(ContentTopic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    research_pack, _ = _research_pack_for_topic(db, topic)
    gateway = OpenAIGateway()
    generator = BriefGenerator()
    brief_payload = gateway.generate_brief_json(research_pack) or generator.generate(research_pack)
    brief = Brief(
        topic_id=topic.id,
        version=db.query(Brief).filter(Brief.topic_id == topic.id).count() + 1,
        brief_json=brief_payload,
        prompt_snapshot=generator.prompt_snapshot(research_pack),
        model_name=settings.openai_brief_model if gateway.enabled else "stub",
    )
    db.add(brief)
    db.commit()
    db.refresh(brief)
    return {"id": str(brief.id), "version": brief.version, "brief": brief.brief_json}


@router.get("/topics/{topic_id}/briefs", response_model=list[BriefRead])
def list_briefs(topic_id: UUID, db: Session = Depends(get_db)) -> list[Brief]:
    return db.query(Brief).filter(Brief.topic_id == topic_id).order_by(Brief.version.desc()).all()


@router.post("/topics/{topic_id}/generate-draft", response_model=ArticleRead, dependencies=[Depends(require_role("admin", "editor", "operator"))])
def generate_draft(topic_id: UUID, db: Session = Depends(get_db)) -> Article:
    topic = db.get(ContentTopic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    brief = db.query(Brief).filter(Brief.topic_id == topic.id).order_by(Brief.version.desc()).first()
    if not brief:
        raise HTTPException(status_code=400, detail="Brief required before draft generation")
    research_pack, _ = _research_pack_for_topic(db, topic)
    article, version = _create_article_for_topic(db, topic, brief, research_pack)
    report = _run_quality_check_for_article(db, article)
    _apply_fast_lane_outcome(db, article, version, topic, report)
    db.commit()
    db.refresh(article)
    return article


@router.post("/articles/{article_id}/generate-images", response_model=list[ImageRead], dependencies=[Depends(require_role("admin", "editor", "operator"))])
def generate_images(article_id: UUID, db: Session = Depends(get_db)) -> list[Image]:
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    rows = _ensure_article_images(db, article)
    db.commit()
    for image in rows:
        db.refresh(image)
    return rows


@router.post("/images/{image_id}/approve", response_model=ImageRead, dependencies=[Depends(require_role("admin", "editor"))])
def approve_image(image_id: UUID, payload: ImageModerationRequest, db: Session = Depends(get_db)) -> Image:
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image.moderation_status = "approved"
    image.moderation_notes = payload.notes
    db.commit()
    db.refresh(image)
    return image


@router.post("/images/{image_id}/reject", response_model=ImageRead, dependencies=[Depends(require_role("admin", "editor"))])
def reject_image(image_id: UUID, payload: ImageModerationRequest, db: Session = Depends(get_db)) -> Image:
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image.moderation_status = "rejected"
    image.moderation_notes = payload.notes
    db.commit()
    db.refresh(image)
    return image


@router.post("/images/{image_id}/regenerate", response_model=ImageRead, dependencies=[Depends(require_role("admin", "editor"))])
def regenerate_image(image_id: UUID, payload: ImageModerationRequest, db: Session = Depends(get_db)) -> Image:
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image.moderation_notes = payload.notes
    _regenerate_image_asset(image, db)
    db.commit()
    db.refresh(image)
    return image


@router.post("/images/bulk-moderate", response_model=BulkImageModerationResponse, dependencies=[Depends(require_role("admin", "editor"))])
def bulk_moderate_images(payload: BulkImageModerationRequest, db: Session = Depends(get_db)) -> BulkImageModerationResponse:
    supported_actions = {"approve", "reject", "regenerate"}
    if payload.action not in supported_actions:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {payload.action}")
    image_ids = [item.strip() for item in payload.image_ids if item.strip()]
    if not image_ids:
        raise HTTPException(status_code=400, detail="At least one image_id is required")

    completed = 0
    results: list[BulkImageModerationResult] = []
    for image_id in image_ids[:50]:
        try:
            image = db.get(Image, UUID(image_id))
        except ValueError:
            image = None
        if not image:
            results.append(BulkImageModerationResult(image_id=image_id, status="skipped", detail="Image not found"))
            continue
        if payload.action == "approve":
            image.moderation_status = "approved"
        elif payload.action == "reject":
            image.moderation_status = "rejected"
        elif payload.action == "regenerate":
            _regenerate_image_asset(image, db)
        image.moderation_notes = payload.notes
        completed += 1
        results.append(
            BulkImageModerationResult(
                image_id=image_id,
                article_id=str(image.article_id),
                status="completed",
                detail=payload.action,
            )
        )
    db.commit()
    return BulkImageModerationResponse(requested=len(image_ids[:50]), completed=completed, results=results)


@router.post("/articles/{article_id}/regenerate-section", dependencies=[Depends(require_role("admin", "editor", "operator"))])
def regenerate_section(article_id: UUID, payload: RegenerateSectionRequest, db: Session = Depends(get_db)) -> dict:
    article = db.get(Article, article_id)
    if not article or not article.current_version_id:
        raise HTTPException(status_code=404, detail="Article not found")
    current = db.get(ArticleVersion, article.current_version_id)
    updated_markdown = ArticleSectionRegenerator().regenerate(
        current.content_markdown,
        payload.section_heading,
        payload.instructions,
    )
    renderer = DraftGenerator()
    new_version = ArticleVersion(article_id=article.id, version=db.query(ArticleVersion).filter(ArticleVersion.article_id == article.id).count() + 1, content_markdown=updated_markdown, content_html=renderer.render_html(updated_markdown), excerpt=current.excerpt, meta_title=current.meta_title, meta_description=current.meta_description, faq_json=current.faq_json, schema_json=current.schema_json, word_count=len(updated_markdown.split()), created_by="system", generation_context={"action": "regenerate_section", "section_heading": payload.section_heading})
    db.add(new_version)
    db.flush()
    article.current_version_id = new_version.id
    article.status = "needs_revision"
    db.commit()
    return {"article_id": str(article_id), "new_version": new_version.version}


@router.post("/articles/{article_id}/save-manual-version", dependencies=[Depends(require_role("admin", "editor"))])
def save_manual_version(article_id: UUID, payload: ManualArticleVersionCreate, db: Session = Depends(get_db)) -> dict:
    article = db.get(Article, article_id)
    if not article or not article.current_version_id:
        raise HTTPException(status_code=404, detail="Article not found")
    current = db.get(ArticleVersion, article.current_version_id)
    if not current:
        raise HTTPException(status_code=404, detail="Current article version not found")

    renderer = DraftGenerator()
    markdown_content = payload.content_markdown.strip()
    new_version = ArticleVersion(
        article_id=article.id,
        version=db.query(ArticleVersion).filter(ArticleVersion.article_id == article.id).count() + 1,
        content_markdown=markdown_content,
        content_html=renderer.render_html(markdown_content),
        excerpt=payload.excerpt,
        meta_title=payload.meta_title.strip(),
        meta_description=payload.meta_description.strip(),
        faq_json=current.faq_json,
        schema_json=current.schema_json,
        word_count=len(markdown_content.split()),
        created_by="editor",
        generation_context={
            "action": "manual_edit",
            "editor_name": payload.editor_name,
            "change_note": payload.change_note,
        },
    )
    db.add(new_version)
    db.flush()

    if payload.title:
        article.title = payload.title.strip()
    if payload.slug:
        article.slug = payload.slug.strip()
    article.current_version_id = new_version.id
    article.status = "needs_revision"
    db.commit()
    return {"article_id": str(article_id), "new_version": new_version.version, "status": article.status}


@router.get("/articles/{article_id}", response_model=ArticleRead)
def get_article(article_id: UUID, db: Session = Depends(get_db)) -> Article:
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.get("/articles", response_model=list[ArticleRead])
def list_articles(db: Session = Depends(get_db)) -> list[Article]:
    return db.query(Article).order_by(Article.updated_at.desc()).all()


@router.get("/images/review-queue", response_model=list[ImageReviewQueueItemRead])
def image_review_queue(db: Session = Depends(get_db)) -> list[ImageReviewQueueItemRead]:
    rows = (
        db.query(Image, Article)
        .join(Article, Article.id == Image.article_id)
        .filter(Image.moderation_status.in_(["generated", "needs_regeneration", "rejected"]))
        .order_by(Image.created_at.asc())
        .limit(100)
        .all()
    )
    return [
        ImageReviewQueueItemRead(
            id=image.id,
            article_id=article.id,
            article_title=article.title,
            article_slug=article.slug,
            alt_text=image.alt_text,
            storage_url=image.storage_url,
            local_path=image.local_path,
            is_featured=image.is_featured,
            moderation_status=image.moderation_status,
            moderation_notes=image.moderation_notes,
            created_at=image.created_at,
        )
        for image, article in rows
    ]


@router.get("/articles/{article_id}/workspace", response_model=ArticleWorkspaceRead)
def get_article_workspace(article_id: UUID, db: Session = Depends(get_db)) -> ArticleWorkspaceRead:
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    topic = db.get(ContentTopic, article.topic_id)
    versions = db.query(ArticleVersion).filter(ArticleVersion.article_id == article_id).order_by(ArticleVersion.version.desc()).all()
    images = db.query(Image).filter(Image.article_id == article_id).order_by(Image.created_at.asc()).all()
    sources = db.query(Source).filter(Source.topic_id == article.topic_id).order_by(Source.created_at.asc()).all()
    research_notes = db.query(ResearchNote).filter(ResearchNote.topic_id == article.topic_id).order_by(ResearchNote.created_at.asc()).all()
    brief = db.get(Brief, article.brief_id)
    current_version = db.get(ArticleVersion, article.current_version_id) if article.current_version_id else None
    latest_quality_report = None
    if article.current_version_id:
        latest_quality_report = db.query(QualityReport).filter(QualityReport.article_version_id == article.current_version_id).order_by(QualityReport.created_at.desc()).first()
    publishing_job = db.query(PublishingJob).filter(PublishingJob.article_id == article_id).order_by(PublishingJob.created_at.desc()).first()
    editorial_reviews = db.query(EditorialReview).filter(EditorialReview.article_id == article_id).order_by(EditorialReview.created_at.desc()).all()
    return ArticleWorkspaceRead(
        article=ArticleRead.model_validate(article),
        current_version=ArticleVersionRead.model_validate(current_version) if current_version else None,
        versions=[ArticleVersionRead.model_validate(version) for version in versions],
        images=[ImageRead.model_validate(image) for image in images],
        latest_quality_report=QualityReportRead.model_validate(latest_quality_report) if latest_quality_report else None,
        publishing_job=PublishingJobRead.model_validate(publishing_job) if publishing_job else None,
        editorial_reviews=[EditorialReviewRead.model_validate(review) for review in editorial_reviews],
        topic=TopicRead.model_validate(topic).model_dump(mode="json") if topic else None,
        sources=[SourceRead.model_validate(source).model_dump(mode="json") for source in sources],
        research_notes=[ResearchNoteRead.model_validate(note).model_dump(mode="json") for note in research_notes],
        brief=BriefRead.model_validate(brief).model_dump(mode="json") if brief else None,
    )


@router.get("/articles/{article_id}/versions", response_model=list[ArticleVersionRead])
def list_versions(article_id: UUID, db: Session = Depends(get_db)) -> list[ArticleVersion]:
    return db.query(ArticleVersion).filter(ArticleVersion.article_id == article_id).order_by(ArticleVersion.version.desc()).all()


@router.get("/articles/{article_id}/editorial-reviews", response_model=list[EditorialReviewRead])
def list_editorial_reviews(article_id: UUID, db: Session = Depends(get_db)) -> list[EditorialReview]:
    return db.query(EditorialReview).filter(EditorialReview.article_id == article_id).order_by(EditorialReview.created_at.desc()).all()


@router.post("/articles/{article_id}/run-quality-check", dependencies=[Depends(require_role("admin", "editor", "operator"))])
def run_quality_check(article_id: UUID, db: Session = Depends(get_db)) -> dict:
    article = db.get(Article, article_id)
    if not article or not article.current_version_id:
        raise HTTPException(status_code=404, detail="Article not found")
    report = _run_quality_check_for_article(db, article)
    db.commit()
    return report


@router.post("/articles/bulk-action", response_model=BulkArticleActionResponse, dependencies=[Depends(require_role("admin", "editor"))])
def bulk_article_action(payload: BulkArticleActionRequest, db: Session = Depends(get_db)) -> BulkArticleActionResponse:
    supported_actions = {"run_quality_check", "submit_for_review", "approve", "publish", "generate_images"}
    if payload.action not in supported_actions:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {payload.action}")
    article_ids = [item.strip() for item in payload.article_ids if item.strip()]
    if not article_ids:
        raise HTTPException(status_code=400, detail="At least one article_id is required")
    results: list[BulkActionResult] = []
    completed = 0
    for article_id in article_ids[:20]:
        article = db.get(Article, UUID(article_id))
        if not article:
            results.append(BulkActionResult(article_id=article_id, status="skipped", detail="Article not found"))
            continue
        try:
            if payload.action == "run_quality_check":
                report = _run_quality_check_for_article(db, article)
                results.append(BulkActionResult(article_id=article_id, status="completed", detail=report["overall_status"]))
            elif payload.action == "generate_images":
                images = _ensure_article_images(db, article)
                results.append(BulkActionResult(article_id=article_id, status="completed", detail=f"{len(images)} images ready"))
            elif payload.action == "submit_for_review":
                article.status = "in_review"
                results.append(BulkActionResult(article_id=article_id, status="completed", detail=article.status))
            elif payload.action == "approve":
                reviewer_name = payload.reviewer_name or "Editor"
                article.status = "approved"
                db.add(
                    EditorialReview(
                        article_id=article.id,
                        article_version_id=article.current_version_id,
                        reviewer_name=reviewer_name,
                        decision="approved",
                        notes=payload.notes,
                    )
                )
                results.append(BulkActionResult(article_id=article_id, status="completed", detail="approved"))
            elif payload.action == "publish":
                if article.status != "approved":
                    results.append(BulkActionResult(article_id=article_id, status="skipped", detail="Only approved articles can be published"))
                    continue
                report = db.query(QualityReport).filter(QualityReport.article_version_id == article.current_version_id).order_by(QualityReport.created_at.desc()).first()
                if not report:
                    results.append(BulkActionResult(article_id=article_id, status="skipped", detail="Quality report required before publishing"))
                    continue
                version = db.get(ArticleVersion, article.current_version_id)
                images = db.query(Image).filter(Image.article_id == article.id).all()
                if not _approved_images_ready(images):
                    results.append(BulkActionResult(article_id=article_id, status="skipped", detail="Approved images are required before publishing"))
                    continue
                payload_data = {"title": version.meta_title or article.title, "slug": article.slug, "excerpt": version.excerpt, "status": "draft", "image_count": len(images)}
                job = PublishingJob(article_id=article.id, target_system="wordpress", status="running", request_payload=payload_data, response_payload={})
                db.add(job)
                db.flush()
                response = PublishingService().publish_article(article, version, images)
                remote_post = response["post"]
                article.cms_post_id = str(remote_post["id"])
                article.published_url = remote_post.get("link")
                article.status = "published"
                job.status = "published"
                job.response_payload = response
                results.append(BulkActionResult(article_id=article_id, status="completed", detail="published"))
            completed += 1
        except Exception as exc:
            results.append(BulkActionResult(article_id=article_id, status="failed", detail=str(exc)))
    db.commit()
    return BulkArticleActionResponse(requested=len(article_ids[:20]), completed=completed, results=results)


@router.get("/articles/{article_id}/quality-report", response_model=QualityReportRead)
def get_quality_report(article_id: UUID, db: Session = Depends(get_db)) -> QualityReport:
    article = db.get(Article, article_id)
    if not article or not article.current_version_id:
        raise HTTPException(status_code=404, detail="Article not found")
    report = db.query(QualityReport).filter(QualityReport.article_version_id == article.current_version_id).order_by(QualityReport.created_at.desc()).first()
    if not report:
        raise HTTPException(status_code=404, detail="Quality report not found")
    return report


@router.post("/articles/{article_id}/submit-for-review", dependencies=[Depends(require_role("admin", "editor"))])
def submit_for_review(article_id: UUID, db: Session = Depends(get_db)) -> dict:
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article.status = "in_review"
    db.commit()
    return {"status": article.status}


@router.post("/articles/{article_id}/approve", dependencies=[Depends(require_role("admin", "editor"))])
def approve_article(article_id: UUID, payload: ReviewDecisionRequest, db: Session = Depends(get_db)) -> dict:
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article.status = "approved"
    db.add(EditorialReview(article_id=article.id, article_version_id=article.current_version_id, reviewer_name=payload.reviewer_name, decision="approved", notes=payload.notes))
    db.commit()
    return {"status": article.status, "reviewer": payload.reviewer_name}


@router.post("/articles/{article_id}/reject", dependencies=[Depends(require_role("admin", "editor"))])
def reject_article(article_id: UUID, payload: ReviewDecisionRequest, db: Session = Depends(get_db)) -> dict:
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article.status = "rejected"
    db.add(EditorialReview(article_id=article.id, article_version_id=article.current_version_id, reviewer_name=payload.reviewer_name, decision="rejected", notes=payload.notes))
    db.commit()
    return {"status": article.status, "reviewer": payload.reviewer_name}


@router.post("/articles/{article_id}/publish", dependencies=[Depends(require_role("admin", "editor"))])
def publish_article(article_id: UUID, db: Session = Depends(get_db)) -> dict:
    article = db.get(Article, article_id)
    if not article or not article.current_version_id:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.status != "approved":
        raise HTTPException(status_code=400, detail="Only approved articles can be published")
    report = db.query(QualityReport).filter(QualityReport.article_version_id == article.current_version_id).order_by(QualityReport.created_at.desc()).first()
    if not report:
        raise HTTPException(status_code=400, detail="Quality report required before publishing")
    version = db.get(ArticleVersion, article.current_version_id)
    images = db.query(Image).filter(Image.article_id == article.id).all()
    if not _approved_images_ready(images):
        raise HTTPException(status_code=400, detail="Approved images are required before publishing")
    payload = {"title": version.meta_title or article.title, "slug": article.slug, "excerpt": version.excerpt, "status": "draft", "image_count": len(images)}
    job = PublishingJob(article_id=article.id, target_system="wordpress", status="running", request_payload=payload, response_payload={})
    db.add(job)
    db.commit()
    response = PublishingService().publish_article(article, version, images)
    remote_post = response["post"]
    article.cms_post_id = str(remote_post["id"])
    article.published_url = remote_post.get("link")
    article.status = "published"
    job.status = "published"
    job.response_payload = response
    db.commit()
    return {"cms_post_id": article.cms_post_id, "published_url": article.published_url}


@router.get("/articles/{article_id}/publishing-status", response_model=PublishingJobRead)
def publishing_status(article_id: UUID, db: Session = Depends(get_db)) -> PublishingJob:
    job = db.query(PublishingJob).filter(PublishingJob.article_id == article_id).order_by(PublishingJob.created_at.desc()).first()
    if not job:
        raise HTTPException(status_code=404, detail="Publishing job not found")
    return job


@router.post("/pipeline/run", dependencies=[Depends(require_role("admin", "editor", "operator"))])
def run_pipeline(payload: PipelineRunRequest, db: Session = Depends(get_db)) -> dict:
    return PipelineService().run_with_task_log(db, payload.topic_query, payload.audience)


@router.post("/pipeline/run-bulk", dependencies=[Depends(require_role("admin", "editor", "operator"))])
def run_pipeline_bulk(payload: BulkPipelineRunRequest, db: Session = Depends(get_db)) -> dict:
    topic_queries = [item.strip() for item in payload.topic_queries if item.strip()]
    if not topic_queries:
        raise HTTPException(status_code=400, detail="At least one topic query is required")
    if len(topic_queries) > 20:
        raise HTTPException(status_code=400, detail="Bulk pipeline is limited to 20 topic queries per request")
    return PipelineService().run_bulk_with_task_log(db, topic_queries, payload.audience)


@router.post("/demo/bootstrap", response_model=DemoBootstrapResponse, dependencies=[Depends(require_role("admin", "editor", "operator"))])
def bootstrap_demo(payload: DemoBootstrapRequest, db: Session = Depends(get_db)) -> DemoBootstrapResponse:
    cluster = Cluster(
        name=payload.cluster_name,
        slug=InterlinkingService()._slug_like(f"{payload.cluster_name}-{payload.topic_query}")[:255],
        description="Local demo cluster",
    )
    db.add(cluster)
    db.flush()

    topic = ContentTopic(
        cluster_id=cluster.id,
        working_title=payload.topic_query.title(),
        target_query=payload.topic_query,
        audience=payload.audience,
        content_type="blog_post",
        status="planned",
        cannibalization_hash=InterlinkingService().cannibalization_hash(payload.topic_query),
    )
    db.add(topic)
    db.flush()

    providers = [YouTubeTranscriptProvider(), ManualSourceProvider()]
    collected = []
    for provider in providers:
        collected.extend(provider.collect(topic.target_query))
    for item in collected:
        db.add(
            Source(
                topic_id=topic.id,
                source_type=item["source_type"],
                url=item["url"],
                title=item["title"],
                author=item.get("author"),
                published_at=item.get("published_at"),
                transcript_text=item.get("transcript_text"),
                raw_content=item.get("raw_content"),
                cleaned_content=item.get("cleaned_content"),
                reliability_score=item.get("reliability_score"),
                ingestion_status=item.get("ingestion_status", "ingested"),
            )
        )
    db.flush()

    topic_sources = db.query(Source).filter(Source.topic_id == topic.id).all()
    extracted_notes = ResearchNoteExtractor().extract_for_topic(db, topic.id, topic_sources)

    source_rows = [
        {
            "source_type": source.source_type,
            "url": source.url,
            "title": source.title,
            "reliability_score": source.reliability_score,
            "summary": source.cleaned_content or source.raw_content or "",
        }
        for source in topic_sources
    ]
    research_pack = ResearchPackBuilder().build(
        topic.working_title,
        topic.target_query,
        topic.audience,
        "informational",
        source_rows,
        _fact_rows(db, topic.id),
    )
    gateway = OpenAIGateway()
    brief_generator = BriefGenerator()
    brief_payload = gateway.generate_brief_json(research_pack) or brief_generator.generate(research_pack)
    brief = Brief(
        topic_id=topic.id,
        version=1,
        brief_json=brief_payload,
        prompt_snapshot=brief_generator.prompt_snapshot(research_pack),
        model_name=settings.openai_brief_model if gateway.enabled else "stub",
    )
    db.add(brief)
    db.flush()

    draft_generator = DraftGenerator()
    draft = gateway.generate_draft_json(brief.brief_json, research_pack) or draft_generator.generate(brief.brief_json, research_pack)
    article = Article(topic_id=topic.id, brief_id=brief.id, title=draft["title"], slug=draft["slug"], status="draft")
    db.add(article)
    db.flush()

    version = ArticleVersion(
        article_id=article.id,
        version=1,
        content_markdown=draft["content_markdown"],
        content_html=draft["content_html"],
        excerpt=draft["excerpt"],
        meta_title=draft["meta_title"],
        meta_description=draft["meta_description"],
        faq_json=draft["faq_json"],
        schema_json=draft["schema_json"],
        word_count=len(draft["content_markdown"].split()),
        created_by="system",
        generation_context={
            "brief_id": str(brief.id),
            "generation_mode": "openai" if gateway.enabled else "stub",
            "image_prompts": draft["image_prompts"],
            "alt_texts": draft["alt_texts"],
            "demo_bootstrap": True,
        },
    )
    db.add(version)
    db.flush()
    article.current_version_id = version.id

    image_rows = []
    for image_payload in ImageGenerator().generate(article.title, article.slug):
        image = Image(article_id=article.id, **image_payload)
        db.add(image)
        image_rows.append(image)

    report = _run_quality_check_for_article(db, article)
    db.commit()

    return DemoBootstrapResponse(
        cluster_id=str(cluster.id),
        topic_id=str(topic.id),
        brief_id=str(brief.id),
        article_id=str(article.id),
        quality_status=report["overall_status"],
        quality_score=report["quality_score"],
        risk_score=report["risk_score"],
        sources_collected=len(collected),
        research_notes_extracted=len(extracted_notes),
        images_generated=len(image_rows),
    )
