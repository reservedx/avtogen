import markdown
from slugify import slugify


class DraftGenerator:
    def generate(self, brief: dict, research_pack: dict) -> dict:
        title = brief["primary_keyword"].title()
        body = (
            f"# {title}\n\n"
            "This article provides general information and should be reviewed by a qualified editor before publication.\n\n"
            "## What is it?\n"
            "It is a symptom-focused topic that should be understood in context rather than self-diagnosed.\n\n"
            "## What are the main symptoms?\n"
            "- Frequent urges\n- Small urine volume\n- Burning or discomfort\n\n"
            "## What causes it?\n"
            "Possible causes include irritation, inflammation, infection, or non-infectious urinary triggers.\n\n"
            "## When should you see a doctor?\n"
            "Seek medical care if symptoms are severe, persistent, associated with fever, blood, pregnancy, or flank pain.\n\n"
            "## What should you avoid doing?\n"
            "Avoid self-prescribing, delaying care for red flags, or assuming the same cause applies to everyone.\n\n"
            "## FAQ\n"
            "### Can this continue after treatment?\n"
            "Yes, ongoing symptoms may need reassessment.\n\n"
            "## Conclusion\n"
            "Educational content can help readers prepare for a clinical conversation, not replace one.\n\n"
            "## Sources\n"
            + "\n".join(f"- {source['url']}" for source in research_pack["source_summaries"])
        )
        return {
            "title": title,
            "slug": slugify(title),
            "content_markdown": body,
            "content_html": markdown.markdown(body, extensions=["tables", "fenced_code", "toc"]),
            "excerpt": "Educational overview of symptoms, causes, and care-seeking red flags.",
            "meta_title": f"{title}: symptoms, causes, and when to seek care",
            "meta_description": "Educational overview of symptoms, causes, warning signs, and when to seek medical advice.",
            "faq_json": {
                "items": [
                    {
                        "question": question,
                        "answer": "Short evidence-aware answer for editorial review.",
                    }
                    for question in brief["faq_questions"]
                ]
            },
            "schema_json": {"@context": "https://schema.org", "@type": "Article"},
            "image_prompts": [
                "Editorial illustration of a woman reading reliable health information in a clinic waiting area",
                "Neutral educational diagram about urinary symptoms without gore",
                "Calm consultation scene with patient and clinician in soft medical setting",
            ],
            "alt_texts": [
                "Woman reviewing symptom information",
                "Educational symptom diagram",
                "Calm patient consultation scene",
            ],
        }

    def render_html(self, markdown_content: str) -> str:
        return markdown.markdown(markdown_content, extensions=["tables", "fenced_code", "toc"])
