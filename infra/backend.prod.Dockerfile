FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV PYTHONPATH=/app/backend

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==1.8.3

COPY pyproject.toml /app/pyproject.toml
RUN poetry install --no-interaction --no-root --only main

COPY backend /app/backend
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY infra/backend-entrypoint.sh /app/infra/backend-entrypoint.sh

RUN chmod +x /app/infra/backend-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/infra/backend-entrypoint.sh"]
