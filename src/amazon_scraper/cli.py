import argparse
import os

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Track Plugin Boutique prices with Selenium.")
    parser.add_argument("--url", required=True, help="Plugin Boutique product URL")
    parser.add_argument("--threshold", required=True, type=float, help="Send email when price is below this amount")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--no-headless", action="store_true", help="Run browser with UI")
    return parser.parse_args()


def main() -> None:
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
    service.check_and_notify(url=args.url, threshold=args.threshold, recipient_email=args.to)
