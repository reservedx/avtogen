FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry==1.8.3
COPY pyproject.toml /app/pyproject.toml
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-root

COPY backend /app/backend
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

ENV PYTHONPATH=/app/backend
WORKDIR /app/backend
