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
- image record generation scaffold
- markdown to HTML rendering
- quality gate rules
- interlinking and cannibalization placeholder service
- task run recording service for pipeline executions
- manual review routing
- article pipeline orchestrator
- OpenAI gateway boundary for future real generation
- WordPress REST adapter boundary
- minimal Next.js admin UI
- Alembic initial migration
- starter tests and seed data

## API Surface

- `POST /api/v1/clusters`
- `GET /api/v1/clusters`
- `POST /api/v1/topics`
- `GET /api/v1/topics`
- `GET /api/v1/topics/{id}`
- `POST /api/v1/topics/{id}/collect-sources`
- `GET /api/v1/topics/{id}/sources`
- `POST /api/v1/topics/{id}/generate-brief`
- `GET /api/v1/topics/{id}/briefs`
- `POST /api/v1/topics/{id}/generate-draft`
- `POST /api/v1/articles/{id}/generate-images`
- `POST /api/v1/articles/{id}/regenerate-section`
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
```

## OpenAI Mode

By default the project runs in stub generation mode for safe local development.

To enable real OpenAI generation:

1. Set `OPENAI_API_KEY` in `.env`
2. Set `USE_STUB_GENERATION=false`
3. Keep using the same API endpoints; the gateway will switch from fallback stubs to real OpenAI calls
## Tests

```bash
poetry run pytest
```

## Roadmap

1. Replace stub generation with OpenAI structured responses and strict DTO validation.
2. Add actual OpenAI Images + S3 upload flow behind `ImageGenerator`.
3. Persist interlink suggestions and duplicate detection via embeddings.
4. Add richer editor review UI with source explorer and version diffing.
5. Add observability dashboards for `task_runs`, pipeline tracing, and publishing retries.
