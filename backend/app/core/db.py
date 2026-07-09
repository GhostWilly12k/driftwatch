"""
Database engine and session management.

Provides:
    engine       — the SQLAlchemy Engine, built from settings.DATABASE_URL
    SessionLocal — session factory used by the get_db dependency
    get_db       — FastAPI dependency that yields a request-scoped Session
                   and guarantees it is closed after the request completes

DATABASE_URL is expected to be the Supabase pooler connection string using
the `postgres.[project-ref]` username format (avoids IPv4/IPv6 resolution
issues — see project notes / ADRs). pool_pre_ping guards against stale
connections being handed out after the pooler recycles them.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a Session, closes it when the request ends."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()