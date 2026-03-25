from app.config import settings


def test_default_database_uses_sqlite() -> None:
    assert settings.database_is_sqlite is True
    assert settings.database_url.startswith("sqlite")
