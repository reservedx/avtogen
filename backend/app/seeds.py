from app.db.models import Cluster, ContentTopic, Keyword
from app.db.session import SessionLocal


def seed() -> None:
    db = SessionLocal()
    cluster = Cluster(name="Cystitis symptoms", slug="cystitis-symptoms", description="Symptom cluster")
    db.add(cluster)
    db.flush()
    keyword = Keyword(cluster_id=cluster.id, keyword="frequent urination with cystitis", search_intent="informational", priority=100, status="active")
    db.add(keyword)
    db.flush()
    topic = ContentTopic(cluster_id=cluster.id, keyword_id=keyword.id, working_title="Frequent urination with cystitis", target_query="frequent urination with cystitis", audience="Women looking for reliable educational information", content_type="blog_post", status="planned")
    db.add(topic)
    db.commit()
    db.close()


if __name__ == "__main__":
    seed()
