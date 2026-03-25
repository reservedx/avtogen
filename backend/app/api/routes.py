from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.application.pipeline_service import PipelineService
from app.config import settings
from app.db.models import Article, ArticleVersion, Brief, Cluster, ContentTopic, Image, PublishingJob, QualityReport, Source, TaskRun
from app.db.session import get_db
from app.schemas.article import ArticleRead, ArticleVersionRead, BriefRead, ImageRead, MetricsRead, PublishingJobRead, QualityReportRead, RegenerateSectionRequest, SettingsSummaryRead, SourceRead, TaskRunRead
from app.schemas.cluster import ClusterCreate, ClusterRead
from app.schemas.topic import TopicCreate, TopicRead
from app.schemas.workflow import PipelineRunRequest, ReviewDecisionRequest
from app.services.platform import BriefGenerator, DraftGenerator, ImageGenerator, ManualSourceProvider, QualityGateService, ResearchPackBuilder, WordPressAdapter, YouTubeTranscriptProvider

router = APIRouter()


@router.get("/settings", response_model=SettingsSummaryRead)
def get_settings_summary() -> SettingsSummaryRead:
    return SettingsSummaryRead(
        app_name=settings.app_name,
        app_env=settings.app_env,
        api_prefix=settings.api_prefix,
        database_url=settings.database_url,
        database_is_sqlite=settings.database_is_sqlite,
        auto_publish_enabled=settings.auto_publish_enabled,
        use_stub_generation=settings.use_stub_generation,
        openai_brief_model=settings.openai_brief_model,
        openai_draft_model=settings.openai_draft_model,
        openai_image_model=settings.openai_image_model,
        min_quality_score=settings.min_quality_score,
        max_risk_score_for_auto_publish=settings.max_risk_score_for_auto_publish,
        required_source_count=settings.required_source_count,
        similarity_threshold=settings.similarity_threshold,
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


@router.get("/task-runs", response_model=list[TaskRunRead])
def list_task_runs(db: Session = Depends(get_db)) -> list[TaskRun]:
    return db.query(TaskRun).order_by(TaskRun.started_at.desc()).limit(100).all()


@router.post("/clusters", response_model=ClusterRead)
def create_cluster(payload: ClusterCreate, db: Session = Depends(get_db)) -> Cluster:
    cluster = Cluster(**payload.model_dump())
    db.add(cluster)
    db.commit()
    db.refresh(cluster)
    return cluster


@router.get("/clusters", response_model=list[ClusterRead])
def list_clusters(db: Session = Depends(get_db)) -> list[Cluster]:
    return db.query(Cluster).order_by(Cluster.created_at.desc()).all()


@router.post("/topics", response_model=TopicRead)
def create_topic(payload: TopicCreate, db: Session = Depends(get_db)) -> ContentTopic:
    topic = ContentTopic(**payload.model_dump())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@router.get("/topics", response_model=list[TopicRead])
def list_topics(db: Session = Depends(get_db)) -> list[ContentTopic]:
    return db.query(ContentTopic).order_by(ContentTopic.created_at.desc()).all()


@router.get("/topics/{topic_id}", response_model=TopicRead)
def get_topic(topic_id: str, db: Session = Depends(get_db)) -> ContentTopic:
    topic = db.get(ContentTopic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.post("/topics/{topic_id}/collect-sources")
def collect_sources(topic_id: str, db: Session = Depends(get_db)) -> dict:
    topic = db.get(ContentTopic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    providers = [YouTubeTranscriptProvider(), ManualSourceProvider()]
    collected = []
    for provider in providers:
        collected.extend(provider.collect(topic.target_query))
    for item in collected:
        db.add(Source(topic_id=topic.id, **item))
    db.commit()
    return {"collected": len(collected)}


@router.get("/topics/{topic_id}/sources", response_model=list[SourceRead])
def list_sources(topic_id: str, db: Session = Depends(get_db)) -> list[Source]:
    return db.query(Source).filter(Source.topic_id == topic_id).all()


@router.post("/topics/{topic_id}/generate-brief")
def generate_brief(topic_id: str, db: Session = Depends(get_db)) -> dict:
    topic = db.get(ContentTopic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    source_rows = [
        {
            "source_type": source.source_type,
            "url": source.url,
            "title": source.title,
            "reliability_score": source.reliability_score,
            "summary": source.cleaned_content or source.raw_content or "",
        }
        for source in db.query(Source).filter(Source.topic_id == topic.id).all()
    ]
    research_pack = ResearchPackBuilder().build(topic.working_title, topic.target_query, topic.audience, "informational", source_rows, [])
    generator = BriefGenerator()
    brief = Brief(topic_id=topic.id, version=db.query(Brief).filter(Brief.topic_id == topic.id).count() + 1, brief_json=generator.generate(research_pack), prompt_snapshot=generator.prompt_snapshot(research_pack), model_name=settings.openai_brief_model)
    db.add(brief)
    db.commit()
    db.refresh(brief)
    return {"id": str(brief.id), "version": brief.version, "brief": brief.brief_json}


@router.get("/topics/{topic_id}/briefs", response_model=list[BriefRead])
def list_briefs(topic_id: str, db: Session = Depends(get_db)) -> list[Brief]:
    return db.query(Brief).filter(Brief.topic_id == topic_id).order_by(Brief.version.desc()).all()


@router.post("/topics/{topic_id}/generate-draft", response_model=ArticleRead)
def generate_draft(topic_id: str, db: Session = Depends(get_db)) -> Article:
    topic = db.get(ContentTopic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    brief = db.query(Brief).filter(Brief.topic_id == topic.id).order_by(Brief.version.desc()).first()
    if not brief:
        raise HTTPException(status_code=400, detail="Brief required before draft generation")
    sources = [{"url": source.url, "title": source.title, "source_type": source.source_type} for source in db.query(Source).filter(Source.topic_id == topic.id).all()]
    draft = DraftGenerator().generate(brief.brief_json, {"source_summaries": sources})
    article = Article(topic_id=topic.id, brief_id=brief.id, title=draft["title"], slug=draft["slug"], status="draft")
    db.add(article)
    db.flush()
    version = ArticleVersion(article_id=article.id, version=1, content_markdown=draft["content_markdown"], content_html=draft["content_html"], excerpt=draft["excerpt"], meta_title=draft["meta_title"], meta_description=draft["meta_description"], faq_json=draft["faq_json"], schema_json=draft["schema_json"], word_count=len(draft["content_markdown"].split()), created_by="system", generation_context={"brief_id": str(brief.id), "image_prompts": draft["image_prompts"], "alt_texts": draft["alt_texts"]})
    db.add(version)
    db.flush()
    article.current_version_id = version.id
    db.commit()
    db.refresh(article)
    return article


@router.post("/articles/{article_id}/generate-images", response_model=list[ImageRead])
def generate_images(article_id: str, db: Session = Depends(get_db)) -> list[Image]:
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    existing = db.query(Image).filter(Image.article_id == article.id).all()
    if existing:
        return existing
    rows = []
    for image_payload in ImageGenerator().generate(article.title):
        image = Image(article_id=article.id, **image_payload)
        db.add(image)
        rows.append(image)
    db.commit()
    for image in rows:
        db.refresh(image)
    return rows


@router.post("/articles/{article_id}/regenerate-section")
def regenerate_section(article_id: str, payload: RegenerateSectionRequest, db: Session = Depends(get_db)) -> dict:
    article = db.get(Article, article_id)
    if not article or not article.current_version_id:
        raise HTTPException(status_code=404, detail="Article not found")
    current = db.get(ArticleVersion, article.current_version_id)
    updated_markdown = current.content_markdown.replace(payload.section_heading, f"{payload.section_heading}\n\nUpdated for editorial revision. {payload.instructions or ''}".strip())
    renderer = DraftGenerator()
    new_version = ArticleVersion(article_id=article.id, version=db.query(ArticleVersion).filter(ArticleVersion.article_id == article.id).count() + 1, content_markdown=updated_markdown, content_html=renderer.render_html(updated_markdown), excerpt=current.excerpt, meta_title=current.meta_title, meta_description=current.meta_description, faq_json=current.faq_json, schema_json=current.schema_json, word_count=len(updated_markdown.split()), created_by="system", generation_context={"action": "regenerate_section", "section_heading": payload.section_heading})
    db.add(new_version)
    db.flush()
    article.current_version_id = new_version.id
    article.status = "needs_revision"
    db.commit()
    return {"article_id": article_id, "new_version": new_version.version}


@router.get("/articles/{article_id}", response_model=ArticleRead)
def get_article(article_id: str, db: Session = Depends(get_db)) -> Article:
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.get("/articles/{article_id}/versions", response_model=list[ArticleVersionRead])
def list_versions(article_id: str, db: Session = Depends(get_db)) -> list[ArticleVersion]:
    return db.query(ArticleVersion).filter(ArticleVersion.article_id == article_id).order_by(ArticleVersion.version.desc()).all()


@router.post("/articles/{article_id}/run-quality-check")
def run_quality_check(article_id: str, db: Session = Depends(get_db)) -> dict:
    article = db.get(Article, article_id)
    if not article or not article.current_version_id:
        raise HTTPException(status_code=404, detail="Article not found")
    version = db.get(ArticleVersion, article.current_version_id)
    image_count = db.query(Image).filter(Image.article_id == article.id).count()
    report = QualityGateService().evaluate(version.content_markdown, source_count=2, internal_link_count=0, image_count=image_count, has_meta=bool(version.meta_title and version.meta_description), faq_count=len(version.faq_json.get("items", [])))
    row = QualityReport(article_version_id=version.id, report_json=report, quality_score=report["quality_score"], risk_score=report["risk_score"], blocking_issues_count=len(report["blockers"]), warning_count=len(report["warnings"]))
    article.quality_score = report["quality_score"]
    article.risk_score = report["risk_score"]
    db.add(row)
    db.commit()
    return report


@router.get("/articles/{article_id}/quality-report", response_model=QualityReportRead)
def get_quality_report(article_id: str, db: Session = Depends(get_db)) -> QualityReport:
    article = db.get(Article, article_id)
    if not article or not article.current_version_id:
        raise HTTPException(status_code=404, detail="Article not found")
    report = db.query(QualityReport).filter(QualityReport.article_version_id == article.current_version_id).order_by(QualityReport.created_at.desc()).first()
    if not report:
        raise HTTPException(status_code=404, detail="Quality report not found")
    return report


@router.post("/articles/{article_id}/submit-for-review")
def submit_for_review(article_id: str, db: Session = Depends(get_db)) -> dict:
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article.status = "in_review"
    db.commit()
    return {"status": article.status}


@router.post("/articles/{article_id}/approve")
def approve_article(article_id: str, payload: ReviewDecisionRequest, db: Session = Depends(get_db)) -> dict:
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article.status = "approved"
    db.commit()
    return {"status": article.status, "reviewer": payload.reviewer_name}


@router.post("/articles/{article_id}/reject")
def reject_article(article_id: str, payload: ReviewDecisionRequest, db: Session = Depends(get_db)) -> dict:
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article.status = "rejected"
    db.commit()
    return {"status": article.status, "reviewer": payload.reviewer_name}


@router.post("/articles/{article_id}/publish")
def publish_article(article_id: str, db: Session = Depends(get_db)) -> dict:
    article = db.get(Article, article_id)
    if not article or not article.current_version_id:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.status != "approved":
        raise HTTPException(status_code=400, detail="Only approved articles can be published")
    report = db.query(QualityReport).filter(QualityReport.article_version_id == article.current_version_id).order_by(QualityReport.created_at.desc()).first()
    if not report:
        raise HTTPException(status_code=400, detail="Quality report required before publishing")
    version = db.get(ArticleVersion, article.current_version_id)
    payload = {"title": article.title, "slug": article.slug, "content": version.content_html, "excerpt": version.excerpt, "status": "draft"}
    job = PublishingJob(article_id=article.id, target_system="wordpress", status="running", request_payload=payload, response_payload={})
    db.add(job)
    db.commit()
    response = WordPressAdapter().create_post(payload)
    article.cms_post_id = str(response["id"])
    article.published_url = response.get("link")
    article.status = "published"
    job.status = "published"
    job.response_payload = response
    db.commit()
    return {"cms_post_id": article.cms_post_id, "published_url": article.published_url}


@router.get("/articles/{article_id}/publishing-status", response_model=PublishingJobRead)
def publishing_status(article_id: str, db: Session = Depends(get_db)) -> PublishingJob:
    job = db.query(PublishingJob).filter(PublishingJob.article_id == article_id).order_by(PublishingJob.created_at.desc()).first()
    if not job:
        raise HTTPException(status_code=404, detail="Publishing job not found")
    return job


@router.post("/pipeline/run")
def run_pipeline(payload: PipelineRunRequest, db: Session = Depends(get_db)) -> dict:
    return PipelineService().run_with_task_log(db, payload.topic_query, payload.audience)
