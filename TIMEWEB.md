# Timeweb Cloud Deployment

## Recommended layout

Use three separate services instead of trying to run everything inside WordPress:

1. Frontend app
   - Deploy the Next.js admin UI as a separate application.
2. Backend app
   - Deploy the FastAPI API and background logic as a separate application.
3. Managed PostgreSQL
   - Store all platform data outside the app containers.

WordPress should remain the publishing target, not the place where the platform logic lives.

## Recommended architecture

- GitHub: source code and deployments
- Timeweb Cloud frontend app: internal admin UI
- Timeweb Cloud backend app: API, pipeline, quality gate, publishing logic
- Timeweb Managed PostgreSQL: database
- WordPress on Timeweb or elsewhere: public website and final published posts

## Why this setup works

- keeps YMYL review logic outside WordPress
- makes article versioning and audit trail easier to manage
- allows replacing WordPress later without rebuilding the whole platform
- separates editorial workflow from the public website

## Minimal deployment order

1. Create a Managed PostgreSQL instance.
2. Create a backend app from the repository using `infra/backend.prod.Dockerfile`.
3. Set backend environment variables from `infra/timeweb.backend.env.example`.
4. Create a frontend app from the repository using `infra/frontend.prod.Dockerfile`.
5. Point the frontend to the backend base URL with `API_BASE_URL`.
6. Add WordPress credentials only when live publishing is needed.
7. Keep OpenAI in stub mode until you intentionally switch to live generation.

## Backend environment variables

Required for the first online prototype:

```env
APP_ENV=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DBNAME
USE_STUB_GENERATION=true
AUTO_PUBLISH_ENABLED=false
DEFAULT_MEDICAL_DISCLAIMER=Важно: Информация в статье не заменяет консультацию специалиста. Обратитесь к врачу при любых тревожных симптомах.
ASSET_STORAGE_BACKEND=s3
```

Optional later:

```env
OPENAI_API_KEY=
YOUTUBE_API_KEY=
WORDPRESS_BASE_URL=
WORDPRESS_USERNAME=
WORDPRESS_APP_PASSWORD=
S3_ENDPOINT_URL=
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_BUCKET=
S3_REGION=
S3_PUBLIC_BASE_URL=
AUTH_ENABLED=true
AUTH_ADMIN_TOKEN=
AUTH_EDITOR_TOKEN=
AUTH_OPERATOR_TOKEN=
```

## Frontend environment variables

```env
API_BASE_URL=https://your-backend-domain.example.com/api/v1
API_AUTH_ROLE=admin
API_AUTH_TOKEN=your-admin-token
```

## Publishing model

- editors work in the internal admin UI
- approved versions are published through the WordPress adapter
- WordPress remains the final CMS and public website
- high-risk medical content should stay on manual review

## Notes

- backend has public endpoints `/health`, `/ready`, and `/version`
- `infra/backend-entrypoint.sh` runs `alembic upgrade head` before starting uvicorn
- use `infra/timeweb.backend.env.example` and `infra/timeweb.frontend.env.example` as templates
- keep `USE_STUB_GENERATION=true` until you are ready to spend OpenAI credits
- keep `AUTO_PUBLISH_ENABLED=false` for health content until the review workflow is fully approved
- switch media storage to S3-compatible storage later if local assets become limiting
