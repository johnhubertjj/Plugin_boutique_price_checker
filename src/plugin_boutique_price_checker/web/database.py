"""SQLAlchemy setup for API and worker processes."""

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .settings import load_settings


class Base(DeclarativeBase):
    """Base declarative model class."""


settings = load_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def create_all_tables() -> None:
    """Create all tables declared in ORM models."""
    from . import orm_models  # noqa: F401

    _ensure_sqlite_schema_compat()
    Base.metadata.create_all(bind=engine)


def _ensure_sqlite_schema_compat() -> None:
    """Best-effort column adds for existing local SQLite databases."""
    if not settings.database_url.startswith("sqlite"):
        return

    with engine.begin() as conn:
        # PRAGMA table_info rows are: (cid, name, type, notnull, dflt_value, pk)
        # We need the column name at index 1, not cid at index 0.
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()}
        if not existing:
            return

        if "phone_number" not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(32)"))
        if "email_verified_at" not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN email_verified_at DATETIME"))
        if "phone_verified_at" not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN phone_verified_at DATETIME"))
        if "two_factor_enabled" not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN NOT NULL DEFAULT 0"))
