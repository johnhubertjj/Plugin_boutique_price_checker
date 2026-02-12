"""Dependency helpers for FastAPI routes."""

from collections.abc import Generator

from .database import SessionLocal


def get_db() -> Generator:
    """Yield a DB session for request scope and always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

