"""Command-line interface for the Plugin Boutique price alert tool."""

import argparse
import json
import os
from pathlib import Path
from typing import Any

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for single-product or watchlist mode."""
    parser = argparse.ArgumentParser(description="Track Plugin Boutique prices with Selenium.")
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--url", help="Plugin Boutique product URL")
    target_group.add_argument(
        "--watchlist-file",
        help="Path to JSON file containing multiple URL/threshold entries",
    )
    parser.add_argument("--threshold", type=float, help="Send email when price is below this amount")
    parser.add_argument(
        "--to",
        help="Recipient email address. In watchlist mode this is the default if an item omits 'to'.",
    )
    parser.add_argument("--no-headless", action="store_true", help="Run browser with UI")
    args = parser.parse_args()

    if args.url and args.threshold is None:
        parser.error("--threshold is required when using --url")
    if args.threshold is not None and not args.url:
        parser.error("--threshold can only be used with --url")

    return args


def load_watchlist(watchlist_path: str) -> list[dict[str, Any]]:
    """Load and validate watchlist JSON content."""
    path = Path(watchlist_path).expanduser()
    if not path.exists():
        raise RuntimeError(f"Watchlist file does not exist: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or not data:
        raise RuntimeError("Watchlist file must be a non-empty JSON array")

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise RuntimeError(f"Watchlist item at index {index} must be a JSON object")

        url = item.get("url")
        threshold = item.get("threshold")
        recipient = item.get("to")

        if not isinstance(url, str) or not url.strip():
            raise RuntimeError(f"Watchlist item at index {index} is missing a valid 'url'")

        try:
            threshold_value = float(threshold)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"Watchlist item at index {index} has an invalid 'threshold'") from exc

        if recipient is not None and (not isinstance(recipient, str) or not recipient.strip()):
            raise RuntimeError(f"Watchlist item at index {index} has an invalid 'to'")

        normalized.append(
            {
                "url": url,
                "threshold": threshold_value,
                "to": recipient,
            }
        )

    return normalized


def main() -> None:
    """Load configuration, build services, and run one or many price checks."""
    args = parse_args()

    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        load_dotenv = None

    if load_dotenv is not None:
        load_dotenv()

    from .email_notifier import EmailNotifier
    from .price_alert_service import PriceAlertService
    from .selenium_scraper import PluginBoutiqueSeleniumScraper

    email_address = os.getenv("EMAIL_ADDRESS")
    app_password = os.getenv("EMAIL_PASSWORD")
    smtp_address = os.getenv("SMTP_ADDRESS")

    if not email_address or not app_password or not smtp_address:
        raise RuntimeError("Missing EMAIL_ADDRESS, EMAIL_PASSWORD, or SMTP_ADDRESS in environment")

    scraper = PluginBoutiqueSeleniumScraper(headless=not args.no_headless)
    notifier = EmailNotifier(smtp_address=smtp_address, email_address=email_address, app_password=app_password)
    service = PriceAlertService(scraper=scraper, notifier=notifier)

    default_recipient = args.to or email_address
    if args.watchlist_file:
        watchlist = load_watchlist(args.watchlist_file)
        for item in watchlist:
            recipient = item.get("to") or default_recipient
            service.check_and_notify(
                url=item["url"],
                threshold=item["threshold"],
                recipient_email=recipient,
            )
    else:
        service.check_and_notify(url=args.url, threshold=args.threshold, recipient_email=default_recipient)
