from fastapi import FastAPI

from app.api.router import api_router
from app.config import settings
from app.logging import configure_logging

configure_logging()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
