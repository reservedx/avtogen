from enum import StrEnum


class TopicStatus(StrEnum):
    planned = "planned"
    researching = "researching"
    brief_ready = "brief_ready"
    draft_ready = "draft_ready"
    in_review = "in_review"
    approved = "approved"
    published = "published"
    rejected = "rejected"


class ArticleStatus(StrEnum):
    draft = "draft"
    in_review = "in_review"
    needs_revision = "needs_revision"
    approved = "approved"
    published = "published"
    rejected = "rejected"


class QualityOverallStatus(StrEnum):
    passed = "pass"
    review = "review"
    block = "block"
