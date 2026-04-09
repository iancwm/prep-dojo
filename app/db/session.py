from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import get_settings
from app.db.base import Base

settings = get_settings()


def create_db_engine(database_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, future=True, connect_args=connect_args)


def create_session_factory(bind: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=bind, autoflush=False, autocommit=False, expire_on_commit=False)

DATABASE_URL = os.getenv("DATABASE_URL", settings.database.url)
engine = create_db_engine(DATABASE_URL)
SessionLocal = create_session_factory(engine)


def init_db(bind: Engine | None = None) -> None:
    Base.metadata.create_all(bind=bind or engine)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
