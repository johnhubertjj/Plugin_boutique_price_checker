"""Shared check runner used by API-triggered and worker-triggered checks."""

from sqlalchemy.orm import Session

from plugin_boutique_price_checker.email_notifier import EmailNotifier
from plugin_boutique_price_checker.selenium_scraper import PluginBoutiqueSeleniumScraper

from .orm_models import PriceCheckRun, WatchlistItem, utc_now
from .settings import load_settings
from .database import SessionLocal


def _build_notifier_if_configured() -> EmailNotifier | None:
    settings = load_settings()
    if not settings.smtp_address or not settings.email_address or not settings.email_password:
        return None
    return EmailNotifier(
        smtp_address=settings.smtp_address,
        email_address=settings.email_address,
        app_password=settings.email_password,
    )


def run_check_for_item(db: Session, item: WatchlistItem) -> PriceCheckRun:
    """Execute one check, persist run row, and optionally send alert email."""
    scraper = PluginBoutiqueSeleniumScraper(headless=True)
    notifier = _build_notifier_if_configured()

    try:
        price = scraper.get_price(item.product_url)
        item.last_price = price.amount
        item.last_currency = price.currency
        item.last_checked_at = utc_now()

        alert_sent = False
        message = "Price checked successfully; no alert sent."
        if price.amount < float(item.threshold):
            if notifier is None:
                message = "Price below threshold, but SMTP settings are missing; alert skipped."
            else:
                notifier.send_price_alert(
                    to_email=item.user.email,
                    product_url=item.product_url,
                    price=price,
                    threshold=float(item.threshold),
                )
                alert_sent = True
                message = "Price below threshold and alert email sent."

        run = PriceCheckRun(
            watchlist_item_id=item.id,
            status="success",
            message=message,
            price_amount=price.amount,
            price_currency=price.currency,
            alert_sent=alert_sent,
        )
    except Exception as exc:  # pragma: no cover - broad catch is deliberate for worker robustness
        run = PriceCheckRun(
            watchlist_item_id=item.id,
            status="error",
            message=str(exc),
            price_amount=None,
            price_currency=None,
            alert_sent=False,
        )

    db.add(run)
    db.add(item)
    db.commit()
    db.refresh(run)
    return run


def run_check_by_id(item_id: int) -> PriceCheckRun:
    """Open a session and run one check by watchlist item id."""
    db = SessionLocal()
    try:
        item = db.get(WatchlistItem, item_id)
        if item is None:
            raise RuntimeError(f"Watchlist item {item_id} not found")
        return run_check_for_item(db, item)
    finally:
        db.close()
