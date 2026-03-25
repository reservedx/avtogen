from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from app.services.platform import InterlinkingService, TaskRunRecorder
from app.workflows.pipeline import ArticlePipeline


class PipelineService:
    def __init__(self) -> None:
        self.pipeline = ArticlePipeline()
        self.task_recorder = TaskRunRecorder()
        self.interlinking = InterlinkingService()

    def run_preview(self, topic_query: str, audience: str) -> dict:
        result = self.pipeline.run(topic_query, audience)
        result["internal_link_suggestions"] = self.interlinking.suggest_links([], None)
        return result

    def run_with_task_log(self, db: Session, topic_query: str, audience: str) -> dict:
        synthetic_entity_id = uuid4()
        task = self.task_recorder.start(
            db,
            task_type="article_pipeline",
            entity_type="topic_query",
            entity_id=synthetic_entity_id,
            input_json={"topic_query": topic_query, "audience": audience},
        )
        try:
            result = self.run_preview(topic_query, audience)
            self.task_recorder.finish(db, task, result)
            db.commit()
            return result
        except Exception as exc:
            self.task_recorder.fail(db, task, str(exc))
            db.commit()
            raise

    def run_bulk_with_task_log(self, db: Session, topic_queries: list[str], audience: str) -> dict:
        results = []
        for topic_query in topic_queries:
            results.append(
                {
                    "topic_query": topic_query,
                    "result": self.run_with_task_log(db, topic_query, audience),
                }
            )
        return {
            "requested": len(topic_queries),
            "completed": len(results),
            "results": results,
        }
