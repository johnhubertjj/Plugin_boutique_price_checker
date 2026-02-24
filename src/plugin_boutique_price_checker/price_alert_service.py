"""Application service that coordinates scraping and email notifications."""

from .email_notifier import EmailNotifier
from .models import PriceResult
from .selenium_scraper import PluginBoutiqueSeleniumScraper


class PriceAlertService:
    """Coordinate scraping and notification behavior for threshold alerts.

    Args:
        None.

    Returns:
        PriceAlertService: Service instance that orchestrates alert checks.
    """

    def __init__(self, scraper: PluginBoutiqueSeleniumScraper, notifier: EmailNotifier) -> None:
        """Initialize service dependencies.

        Args:
            scraper: Price scraper implementation.
            notifier: Email notifier implementation.

        Returns:
            None: This constructor stores the supplied collaborators.
        """
        self.scraper = scraper
        self.notifier = notifier

    def check_and_notify(self, url: str, threshold: float, recipient_email: str) -> PriceResult:
        """Check a product price and send an alert when below threshold.

        Args:
            url: Product page URL to check.
            threshold: Alert threshold for the numeric product price.
            recipient_email: Email address that receives alert notifications.

        Returns:
            PriceResult: The current parsed product price.
        """
        price = self.scraper.get_price(url)
        print(f"Current price: {price.formatted}")

        if price.amount < threshold:
            self.notifier.send_price_alert(recipient_email, url, price, threshold)
            print("Alert sent.")
        else:
            print("No alert sent.")

        return price
