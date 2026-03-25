from app.config import settings


class LaunchReadinessService:
    def evaluate(self, *, topics_count: int, articles_count: int, published_articles_count: int) -> dict:
        items: list[dict] = [
            self._item(
                "medical_disclaimer",
                "Medical disclaimer configured",
                "ready" if bool(settings.default_medical_disclaimer.strip()) else "needs_attention",
                "Default health disclaimer is available for research, draft generation, and QA checks."
                if bool(settings.default_medical_disclaimer.strip())
                else "Add a required medical disclaimer before generating launch content.",
            ),
            self._item(
                "editorial_review_mode",
                "Auto-publish disabled",
                "ready" if not settings.auto_publish_enabled else "needs_attention",
                "Articles stay in review-first mode before publication."
                if not settings.auto_publish_enabled
                else "Disable auto-publish before launch for YMYL content.",
            ),
            self._item(
                "content_seed",
                "Topics and articles seeded",
                "ready" if topics_count > 0 and articles_count > 0 else "needs_attention",
                f"{topics_count} topics and {articles_count} articles available for editorial testing."
                if topics_count > 0 and articles_count > 0
                else "Create at least one topic and one article to validate the workflow.",
            ),
            self._item(
                "wordpress_connection",
                "WordPress publishing configured",
                "ready"
                if settings.wordpress_base_url != "https://example.com" and settings.wordpress_app_password != "changeme"
                else "optional",
                "WordPress credentials are configured for live publishing."
                if settings.wordpress_base_url != "https://example.com" and settings.wordpress_app_password != "changeme"
                else "You can keep this unset until you are ready to publish live.",
            ),
            self._item(
                "database_mode",
                "Production database mode",
                "ready" if not settings.database_is_sqlite else "warning",
                "External database is configured."
                if not settings.database_is_sqlite
                else "SQLite is fine for local prototype work, but switch to PostgreSQL before public launch.",
            ),
            self._item(
                "openai_budget",
                "Generation mode",
                "ready" if settings.use_stub_generation else "warning",
                "Stub generation is active, so you can continue building flows without spending API budget."
                if settings.use_stub_generation
                else "Live OpenAI generation is enabled. Watch API usage before scaling runs.",
            ),
            self._item(
                "published_articles",
                "Published content available",
                "ready" if published_articles_count > 0 else "optional",
                f"{published_articles_count} published article(s) already exist."
                if published_articles_count > 0
                else "No published articles yet. This is okay before the first moderated launch.",
            ),
        ]
        overall_status = "ready" if all(item["status"] in {"ready", "optional"} for item in items) else "needs_attention"
        summary = (
            "Prototype can be operated without Semrush. Remaining gaps are mostly launch hygiene and publication setup."
            if overall_status == "ready"
            else "Core product flow is usable, but a few launch checks still need attention."
        )
        return {
            "overall_status": overall_status,
            "summary": summary,
            "items": items,
        }

    def _item(self, code: str, label: str, status: str, detail: str) -> dict:
        return {
            "code": code,
            "label": label,
            "status": status,
            "detail": detail,
        }
