# Women Health Content Platform

Production-oriented MVP scaffold for an AI-assisted article generation and publishing system focused on women's health. The design assumes YMYL constraints, mandatory quality gates, article versioning, and manual review for risky content.

## High-Level Architecture

The project is a modular monolith with a split between domain, application, infrastructure, API, and admin UI:

- `backend/app/domain`: enums and business rules
- `backend/app/application`: use-case orchestration and task-logged pipeline service
- `backend/app/services`: transcript cleaning, research pack assembly, brief generation, draft generation, image scaffolding, quality gate, interlinking, review logic, OpenAI/CMS/provider boundaries
- `backend/app/workflows`: article pipeline orchestration
- `backend/app/api`: FastAPI endpoints with typed request/response schemas
- `backend/app/db`: SQLAlchemy models and session
- `backend/app/workers`: Dramatiq worker entrypoints
- `frontend`: minimal Next.js editorial admin
- `alembic`: migrations
- `tests`: unit and workflow tests

## Folder Structure

```text
.
|-- alembic/
|-- backend/
|   `-- app/
|       |-- api/
|       |-- application/
|       |-- db/
|       |-- domain/
|       |-- schemas/
|       |-- services/
|       |-- workflows/
|       `-- workers/
|-- frontend/
|   `-- app/
|-- infra/
|-- tests/
|-- docker-compose.yml
`-- pyproject.toml
```

## ERD / Tables

- `clusters`
- `keywords`
- `content_topics`
- `sources`
- `research_notes`
- `briefs`
- `articles`
- `article_versions`
- `images`
- `internal_links`
- `quality_reports`
- `editorial_reviews`
- `publishing_jobs`
- `task_runs`

## Pipeline Diagram

```text
topic_selected
  -> source_collection
  -> transcript_ingestion
  -> research_pack_build
  -> brief_generation
  -> draft_generation
  -> image_generation
  -> markdown_to_html_render
  -> interlinking
  -> quality_gate
      -> if blockers: needs_revision / manual_review
      -> if risky medical content: manual_review_only
      -> else approved
  -> publish_to_cms
  -> post_publish_finalize
```

## MVP Coverage

Implemented in scaffold form:

- cluster/topic/source/article core entities
- YouTube transcript provider stub + manual source provider stub
- research pack builder
- brief generator scaffold
- draft generator scaffold
- image prompt generation plus local PNG asset persistence
- markdown to HTML rendering
- quality gate rules
- interlinking and cannibalization placeholder service
- task run recording service for pipeline executions
- manual review routing with editorial decision audit trail
- article pipeline orchestrator
- OpenAI gateway with structured JSON generation and fallback validation
- asset storage abstraction with local and S3-compatible persistence modes
- WordPress publishing service with media upload and featured image flow
- Next.js admin UI with live-or-fallback dashboard plus article workspace actions for QA, review, publish, and section regeneration
- Alembic initial migration
- starter tests and seed data

## API Surface

- `POST /api/v1/clusters`
- `GET /api/v1/clusters`
- `POST /api/v1/keywords`
- `GET /api/v1/keywords`
- `POST /api/v1/topics`
- `GET /api/v1/topics`
- `GET /api/v1/topics/{id}`
- `POST /api/v1/topics/{id}/collect-sources`
- `GET /api/v1/topics/{id}/sources`
- `POST /api/v1/topics/{id}/sources/manual`
- `GET /api/v1/launch-readiness`
- `POST /api/v1/topics/{id}/generate-brief`
- `GET /api/v1/topics/{id}/briefs`
- `POST /api/v1/topics/{id}/generate-draft`
- `GET /api/v1/articles`
- `GET /api/v1/articles/{id}/workspace`
- `POST /api/v1/articles/{id}/generate-images`
- `POST /api/v1/articles/{id}/regenerate-section`
- `POST /api/v1/articles/{id}/save-manual-version`
- `GET /api/v1/articles/{id}`
- `GET /api/v1/articles/{id}/versions`
- `POST /api/v1/articles/{id}/run-quality-check`
- `GET /api/v1/articles/{id}/quality-report`
- `POST /api/v1/articles/{id}/submit-for-review`
- `POST /api/v1/articles/{id}/approve`
- `POST /api/v1/articles/{id}/reject`
- `POST /api/v1/articles/{id}/publish`
- `GET /api/v1/articles/{id}/publishing-status`
- `POST /api/v1/pipeline/run`
- `POST /api/v1/pipeline/run-bulk`

## Run Locally

1. Copy `.env.example` to `.env`
2. Start services:

```bash
docker-compose up --build
```

3. Apply migrations:

```bash
poetry run alembic upgrade head
```

4. Seed starter data:

```bash
poetry run python -m app.seeds
```

5. Open:

- Backend docs: `http://localhost:8000/docs`
- Frontend admin: `http://localhost:3000`


## Quick Local Commands

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_tests.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run_backend.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run_frontend.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run_demo.ps1
```

## Fastest Prototype Try

1. Start backend:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_backend.ps1
```

2. In a second terminal start frontend:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_frontend.ps1
```

3. In a third terminal bootstrap a demo article:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_demo.ps1
```

This will create a demo cluster, topic, sources, research notes, brief, draft, images, and a quality report so you can immediately inspect the prototype in the admin UI.

You can also operate the prototype without Semrush by:

1. creating topics manually,
2. collecting YouTube/manual sources,
3. adding manual sources directly in the topic workspace,
4. generating the brief and draft from the gathered research,
5. using the launch-readiness panel on the dashboard to track setup gaps.

## Render Deployment

The repo now includes a root [render.yaml](/C:/Users/РјСѓСЂ7РµРІРі9/Desktop/avtogen/render.yaml) blueprint for a simple online prototype deployment:

- `avtogen-backend` as a Docker web service
- `avtogen-frontend` as a Node.js web service
- `avtogen-db` as Render Postgres

To deploy:

1. Create or sign in to your Render account.
2. Create a new Blueprint and connect the GitHub repo.
3. Render will detect `render.yaml` automatically.
4. Fill in secret env vars when prompted:
   - `OPENAI_API_KEY`
   - `YOUTUBE_API_KEY`
   - optional WordPress credentials if you want live publishing
5. Deploy the stack.

Official Render docs used for this setup:
- [Blueprint YAML Reference](https://render.com/docs/blueprint-spec)
- [Render Blueprints](https://render.com/docs/infrastructure-as-code)
- [Environment Variables via Blueprints](https://render.com/docs/configure-environment-variables)

## OpenAI Mode

By default the project runs in stub generation mode for safe local development.

To enable real OpenAI generation:

1. Set `OPENAI_API_KEY` in `.env`
2. Set `USE_STUB_GENERATION=false`
3. Optional: set `ASSET_STORAGE_DIR` if you want generated images stored outside the default `data/generated_assets`
4. Optional: set `ASSET_STORAGE_BACKEND=s3` or `ASSET_STORAGE_BACKEND=hybrid` for MinIO/S3 upload
5. Keep using the same API endpoints; the gateway will switch from fallback stubs to real OpenAI calls

To enable real YouTube search/transcript ingestion:

1. Set `YOUTUBE_API_KEY`
2. Install dependencies from `pyproject.toml` so `youtube-transcript-api` is available
3. Optional: tune `YOUTUBE_MAX_RESULTS`, `YOUTUBE_REGION_CODE`, `YOUTUBE_RELEVANCE_LANGUAGE`, and `YOUTUBE_TRANSCRIPT_LANGUAGES`
4. Keep using `POST /api/v1/topics/{id}/collect-sources`; the provider will switch from fallback demo records to live search/transcript boundaries when possible

When image generation is enabled, `POST /api/v1/articles/{id}/generate-images` will:

- request 3 medically neutral prompts
- generate WEBP assets through the OpenAI Images API when available
- save files under `data/generated_assets/<article-slug>/`
- optionally upload them to S3-compatible storage and store remote URLs
- gracefully fall back to local prompt-only image records if binary generation fails
## Tests

```bash
poetry run pytest
```

## Timeweb Cloud

For a production-friendly Timeweb setup, use separate frontend, backend, and PostgreSQL services, with WordPress kept as the publishing target. See [TIMEWEB.md](TIMEWEB.md).

## Roadmap

1. Persist generated image assets to S3-compatible storage and expose signed/public URLs instead of local file paths.
2. Persist interlink suggestions and duplicate detection via embeddings.
3. Add richer editor review UI with source explorer and version diffing.
4. Add observability dashboards for `task_runs`, pipeline tracing, and publishing retries.
5. Expand source providers and stricter medical safety validation before auto-publish.

