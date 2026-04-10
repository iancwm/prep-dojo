from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import get_settings
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


def uses_metadata_schema_management(init_mode: str | None = None) -> bool:
    mode = (init_mode or settings.database.init_mode).strip().lower()
    if mode not in {"metadata", "migrations"}:
        raise ValueError("DATABASE_INIT_MODE must be either `metadata` or `migrations`.")
    return mode == "metadata"


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
