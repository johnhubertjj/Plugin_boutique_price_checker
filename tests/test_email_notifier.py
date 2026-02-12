"""Unit tests for SMTP email notifications."""

from amazon_scraper.email_notifier import EmailNotifier
from amazon_scraper.models import PriceResult


class FakeSMTP:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.logged_in_with = None
        self.sent_message = None

    def __enter__(self) -> "FakeSMTP":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)

    def login(self, username: str, password: str) -> None:
        self.logged_in_with = (username, password)

    def send_message(self, message) -> None:
        self.sent_message = message


def test_send_price_alert_formats_and_sends_email(monkeypatch) -> None:
    captured = {}

    def fake_smtp_factory(host: str, port: int) -> FakeSMTP:
        smtp = FakeSMTP(host, port)
        captured["smtp"] = smtp
        return smtp

    monkeypatch.setattr("amazon_scraper.email_notifier.smtplib.SMTP_SSL", fake_smtp_factory)

    notifier = EmailNotifier(
        smtp_address="smtp.gmail.com",
        email_address="sender@example.com",
        app_password="app-password",
    )
    notifier.send_price_alert(
        to_email="recipient@example.com",
        product_url="https://example.com/product",
        price=PriceResult(amount=19.99, currency="$"),
        threshold=20.00,
    )

    smtp = captured["smtp"]
    assert smtp.host == "smtp.gmail.com"
    assert smtp.port == 465
    assert smtp.logged_in_with == ("sender@example.com", "app-password")
    assert smtp.sent_message is not None
    assert smtp.sent_message["To"] == "recipient@example.com"
    assert smtp.sent_message["From"] == "sender@example.com"
    assert smtp.sent_message["Subject"] == "Plugin Boutique price alert"
    body = smtp.sent_message.get_content()
    assert "Current price: $19.99" in body
    assert "Threshold: 20.00" in body
