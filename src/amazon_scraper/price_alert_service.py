from .email_notifier import EmailNotifier
from .models import PriceResult
from .selenium_scraper import PluginBoutiqueSeleniumScraper


class PriceAlertService:
    def __init__(self, scraper: PluginBoutiqueSeleniumScraper, notifier: EmailNotifier) -> None:
        self.scraper = scraper
        self.notifier = notifier

    def check_and_notify(self, url: str, threshold: float, recipient_email: str) -> PriceResult:
        price = self.scraper.get_price(url)
        print(f"Current price: {price.formatted}")

        if price.amount < threshold:
            self.notifier.send_price_alert(recipient_email, url, price, threshold)
            print("Alert sent.")
        else:
            print("No alert sent.")

        return price
