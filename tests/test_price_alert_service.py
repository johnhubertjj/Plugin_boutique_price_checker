"""Unit tests for alert orchestration logic."""

from plugin_boutique_price_checker.models import PriceResult
from plugin_boutique_price_checker.price_alert_service import PriceAlertService


class StubScraper:
    def __init__(self, amount: float) -> None:
        self.amount = amount

    def get_price(self, url: str) -> PriceResult:
        _ = url
        return PriceResult(amount=self.amount, currency="$")


class StubNotifier:
    def __init__(self) -> None:
        self.calls = []

    def send_price_alert(self, to_email: str, product_url: str, price: PriceResult, threshold: float) -> None:
        self.calls.append((to_email, product_url, price.amount, threshold))


def test_check_and_notify_sends_email_when_below_threshold() -> None:
    scraper = StubScraper(amount=49.99)
    notifier = StubNotifier()
    service = PriceAlertService(scraper=scraper, notifier=notifier)

    result = service.check_and_notify(
        url="https://example.com/product",
        threshold=50.0,
        recipient_email="alerts@example.com",
    )

    assert result.amount == 49.99
    assert notifier.calls == [
        ("alerts@example.com", "https://example.com/product", 49.99, 50.0)
    ]


def test_check_and_notify_does_not_send_when_above_threshold() -> None:
    scraper = StubScraper(amount=75.0)
    notifier = StubNotifier()
    service = PriceAlertService(scraper=scraper, notifier=notifier)

    service.check_and_notify(
        url="https://example.com/product",
        threshold=50.0,
        recipient_email="alerts@example.com",
    )

    assert notifier.calls == []
