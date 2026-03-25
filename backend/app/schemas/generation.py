from pydantic import BaseModel, Field


class OutlineItem(BaseModel):
    heading: str
    level: str


class FAQItem(BaseModel):
    question: str
    answer: str


class BriefGenerationResult(BaseModel):
    primary_keyword: str
    secondary_keywords: list[str] = Field(default_factory=list)
    search_intent: str
    user_problem: str
    article_goal: str
    target_word_count: int
    tone: str
    reading_level: str
    outline: list[OutlineItem]
    required_sections: list[str]
    prohibited_sections: list[str] = Field(default_factory=list)
    medical_safety_notes: list[str] = Field(default_factory=list)
    faq_questions: list[str] = Field(default_factory=list)
    internal_link_targets: list[str] = Field(default_factory=list)
    schema_type: str
    meta_guidance: dict = Field(default_factory=dict)
    image_guidance: dict = Field(default_factory=dict)


class DraftGenerationResult(BaseModel):
    title: str
    slug: str
    content_markdown: str
    excerpt: str
    meta_title: str
    meta_description: str
    faq_items: list[FAQItem] = Field(default_factory=list)
    schema_payload: dict = Field(default_factory=dict)
    image_prompts: list[str] = Field(default_factory=list)
    alt_texts: list[str] = Field(default_factory=list)


class ImageGenerationItem(BaseModel):
    prompt: str
    alt_text: str
    storage_url: str | None = None
    local_path: str | None = None
    width: int | None = None
    height: int | None = None
    is_featured: bool = False
