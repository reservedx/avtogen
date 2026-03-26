from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db.base import Base
from app.db import models  # noqa: F401
from app.services.runtime_settings import load_runtime_overrides

engine_kwargs = {"future": True, "pool_pre_ping": True}
if settings.database_is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _ensure_sqlite_compat_columns() -> None:
    if not settings.database_is_sqlite:
        return
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "images" not in tables:
        return
    image_columns = {column["name"] for column in inspector.get_columns("images")}
    statements: list[str] = []
    if "moderation_status" not in image_columns:
        statements.append("ALTER TABLE images ADD COLUMN moderation_status VARCHAR(50) DEFAULT 'generated'")
    if "moderation_notes" not in image_columns:
        statements.append("ALTER TABLE images ADD COLUMN moderation_notes TEXT")
    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_compat_columns()
    with SessionLocal() as db:
        load_runtime_overrides(db)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
