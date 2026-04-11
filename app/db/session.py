from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import get_settings, normalize_database_init_mode
from app.db.base import Base

settings = get_settings()
ROOT_DIR = Path(__file__).resolve().parents[2]


def create_db_engine(database_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, future=True, connect_args=connect_args)


def create_session_factory(bind: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=bind, autoflush=False, autocommit=False, expire_on_commit=False)


DATABASE_URL = os.getenv("DATABASE_URL", settings.database.url)
engine = create_db_engine(DATABASE_URL)
SessionLocal = create_session_factory(engine)


@dataclass(frozen=True)
class DatabaseReadinessReport:
    ready: bool
    message: str


def uses_metadata_schema_management(init_mode: str | None = None) -> bool:
    mode = normalize_database_init_mode(init_mode or settings.database.init_mode)
    return mode == "metadata"


def check_database_readiness(bind: Engine | None = None) -> DatabaseReadinessReport:
    engine_to_check = bind or engine
    try:
        with engine_to_check.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        return DatabaseReadinessReport(
            ready=False,
            message=f"database readiness check failed: {exc}",
        )

    return DatabaseReadinessReport(ready=True, message="database is reachable")


def init_db(bind: Engine | None = None) -> None:
    if not uses_metadata_schema_management():
        return
    Base.metadata.create_all(bind=bind or engine)


def get_alembic_config_path() -> Path:
    return ROOT_DIR / "alembic.ini"


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
