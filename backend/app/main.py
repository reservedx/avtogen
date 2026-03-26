from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.config import settings
from app.db.session import database_ready, init_db
from app.logging import configure_logging

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["health"])
def readinesscheck() -> dict[str, str]:
    db_ok = database_ready()
    return {
        "status": "ready" if db_ok else "degraded",
        "database": "ok" if db_ok else "unavailable",
        "app_env": settings.app_env,
    }


@app.get("/version", tags=["health"])
def versioncheck() -> dict[str, str]:
    return {"app_name": settings.app_name, "version": "0.1.0", "app_env": settings.app_env}
