import dramatiq
from dramatiq.brokers.redis import RedisBroker

from app.application.pipeline_service import PipelineService
from app.config import settings
from app.db.session import SessionLocal

redis_broker = RedisBroker(url=settings.redis_url)
dramatiq.set_broker(redis_broker)


@dramatiq.actor(max_retries=5, min_backoff=1000)
def run_article_pipeline(topic_query: str, audience: str) -> dict:
    db = SessionLocal()
    try:
        return PipelineService().run_with_task_log(db, topic_query, audience)
    finally:
        db.close()
