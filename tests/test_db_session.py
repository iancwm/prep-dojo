from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.settings import (
    get_settings,
    is_development_environment,
    normalize_environment,
    resolve_database_init_mode,
    resolve_server_reload,
)
from app.db.session import check_database_readiness, uses_metadata_schema_management
from app.main import app


def test_metadata_schema_management_is_enabled_for_metadata_mode() -> None:
    assert uses_metadata_schema_management("metadata") is True


def test_metadata_schema_management_is_disabled_for_migrations_mode() -> None:
    assert uses_metadata_schema_management("migrations") is False


def test_metadata_schema_management_rejects_invalid_modes() -> None:
    try:
        uses_metadata_schema_management("invalid")
    except ValueError as exc:
        assert "metadata" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid init mode")


def test_runtime_mode_helpers_prefer_migrations_for_non_development_defaults() -> None:
    assert normalize_environment("Local") == "development"
    assert is_development_environment("development") is True
    assert resolve_database_init_mode("production", "metadata") == "migrations"
    assert resolve_database_init_mode("production", "metadata", explicit_override=True) == "metadata"
    assert resolve_server_reload("production", True) is False
    assert resolve_server_reload("production", True, explicit_override=True) is True


def test_get_settings_prefers_migration_first_runtime_outside_development(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("DATABASE_INIT_MODE", raising=False)
    monkeypatch.delenv("APP_RELOAD", raising=False)
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.app.environment == "production"
        assert settings.server.reload is False
        assert settings.database.init_mode == "migrations"
        assert settings.is_non_development() is True
        assert settings.uses_migration_first_database_init() is True
    finally:
        get_settings.cache_clear()


def test_check_database_readiness_reports_ready_for_sqlite() -> None:
    report = check_database_readiness(create_engine("sqlite:///:memory:"))
    assert report.ready is True
    assert report.message == "database is reachable"


def test_check_database_readiness_reports_failure_for_broken_engine() -> None:
    class BrokenEngine:
        def connect(self):
            raise SQLAlchemyError("boom")

    report = check_database_readiness(BrokenEngine())
    assert report.ready is False
    assert "boom" in report.message


def test_readyz_reports_runtime_readiness(monkeypatch) -> None:
    class Report:
        ready = True
        message = "database is reachable"

    monkeypatch.setattr("app.main.check_database_readiness", lambda: Report())

    with TestClient(app) as client:
        response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database_ready"] is True


def test_readyz_returns_503_when_database_is_unreachable(monkeypatch) -> None:
    class Report:
        ready = False
        message = "database readiness check failed: boom"

    monkeypatch.setattr("app.main.check_database_readiness", lambda: Report())

    with TestClient(app) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["database_ready"] is False
