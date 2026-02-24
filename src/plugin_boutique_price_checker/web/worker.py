"""Background worker scaffold that polls active watchlist items."""

from time import sleep
import os

from sqlalchemy import select

from .database import SessionLocal, create_all_tables
from .orm_models import WatchlistItem
from .scrape_runner import run_check_for_item
from .settings import load_settings


def run_once() -> int:
    """Run checks for all active watchlist items one time."""
    db = SessionLocal()
    processed = 0
    try:
        items = list(db.scalars(select(WatchlistItem).where(WatchlistItem.is_active.is_(True))).all())
        for item in items:
            run_check_for_item(db, item)
            processed += 1
        return processed
    finally:
        db.close()


def main() -> None:
    """Continuously process active watchlist items with a fixed sleep interval."""
    settings = load_settings()
    if settings.db_auto_create:
        create_all_tables()

    run_once_mode_raw = os.getenv("WORKER_RUN_ONCE", "false").strip().lower()
    run_once_mode = run_once_mode_raw in {"1", "true", "yes", "on"}

    if run_once_mode:
        processed = run_once()
        print(f"Worker one-shot complete. Processed items: {processed}")
        return

    print(f"Worker started. Poll interval: {settings.worker_sleep_seconds} seconds")
    while True:
        processed = run_once()
        print(f"Worker cycle complete. Processed items: {processed}")
        sleep(settings.worker_sleep_seconds)
