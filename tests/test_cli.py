"""Unit tests for CLI argument and watchlist handling."""

import json
import os
import sys
from argparse import Namespace

import pytest

from plugin_boutique_price_checker import cli


def test_parse_args_single_url_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "--url",
            "https://example.com/p",
            "--threshold",
            "50",
            "--to",
            "alerts@example.com",
        ],
    )

    args = cli.parse_args()
    assert args.url == "https://example.com/p"
    assert args.threshold == 50.0
    assert args.watchlist_file is None


def test_parse_args_requires_threshold_with_url(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["prog", "--url", "https://example.com/p"])
    with pytest.raises(SystemExit):
        cli.parse_args()


def test_parse_args_disallows_threshold_with_watchlist(monkeypatch, tmp_path) -> None:
    watchlist = tmp_path / "watchlist.json"
    watchlist.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "--watchlist-file",
            str(watchlist),
            "--threshold",
            "25",
        ],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()


def test_load_watchlist_valid_file(tmp_path) -> None:
    watchlist = tmp_path / "watchlist.json"
    watchlist.write_text(
        json.dumps(
            [
                {
                    "url": "https://example.com/a",
                    "threshold": 99,
                    "to": "a@example.com",
                },
                {
                    "url": "https://example.com/b",
                    "threshold": "49.95",
                },
            ]
        ),
        encoding="utf-8",
    )

    items = cli.load_watchlist(str(watchlist))
    assert len(items) == 2
    assert items[0]["threshold"] == 99.0
    assert items[1]["threshold"] == 49.95
    assert items[1]["to"] is None


def test_load_watchlist_rejects_invalid_item(tmp_path) -> None:
    watchlist = tmp_path / "watchlist.json"
    watchlist.write_text(
        json.dumps([{"url": "https://example.com/a", "threshold": "not-a-number"}]),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="invalid 'threshold'"):
        cli.load_watchlist(str(watchlist))


def test_load_watchlist_rejects_missing_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"
    with pytest.raises(RuntimeError, match="does not exist"):
        cli.load_watchlist(str(missing))


def test_load_watchlist_rejects_empty_array(tmp_path) -> None:
    watchlist = tmp_path / "watchlist.json"
    watchlist.write_text("[]", encoding="utf-8")

    with pytest.raises(RuntimeError, match="non-empty JSON array"):
        cli.load_watchlist(str(watchlist))


def test_load_watchlist_rejects_non_object_item(tmp_path) -> None:
    watchlist = tmp_path / "watchlist.json"
    watchlist.write_text(json.dumps(["bad"]), encoding="utf-8")

    with pytest.raises(RuntimeError, match="must be a JSON object"):
        cli.load_watchlist(str(watchlist))


def test_load_watchlist_rejects_invalid_url(tmp_path) -> None:
    watchlist = tmp_path / "watchlist.json"
    watchlist.write_text(json.dumps([{"url": "", "threshold": 20}]), encoding="utf-8")

    with pytest.raises(RuntimeError, match="missing a valid 'url'"):
        cli.load_watchlist(str(watchlist))


def test_load_watchlist_rejects_invalid_recipient(tmp_path) -> None:
    watchlist = tmp_path / "watchlist.json"
    watchlist.write_text(
        json.dumps([{"url": "https://example.com/a", "threshold": 20, "to": ""}]),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="invalid 'to'"):
        cli.load_watchlist(str(watchlist))


def test_main_raises_when_required_env_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "parse_args",
        lambda: Namespace(
            url="https://example.com/p",
            threshold=50.0,
            watchlist_file=None,
            to=None,
            no_headless=False,
        ),
    )
    original_getenv = os.getenv

    def fake_getenv(key: str, default=None):
        if key in {"EMAIL_ADDRESS", "EMAIL_PASSWORD", "SMTP_ADDRESS"}:
            return None
        return original_getenv(key, default)

    monkeypatch.setattr(cli.os, "getenv", fake_getenv)

    with pytest.raises(RuntimeError, match="Missing EMAIL_ADDRESS"):
        cli.main()


def test_main_single_url_mode_builds_services_and_checks(monkeypatch) -> None:
    class FakeScraper:
        def __init__(self, headless: bool) -> None:
            self.headless = headless

    class FakeNotifier:
        def __init__(self, smtp_address: str, email_address: str, app_password: str) -> None:
            self.smtp_address = smtp_address
            self.email_address = email_address
            self.app_password = app_password

    created = {}

    class FakeService:
        def __init__(self, scraper, notifier) -> None:
            created["scraper"] = scraper
            created["notifier"] = notifier
            self.calls = []
            created["service"] = self

        def check_and_notify(self, url: str, threshold: float, recipient_email: str) -> None:
            self.calls.append((url, threshold, recipient_email))

    import plugin_boutique_price_checker.email_notifier as email_notifier_module
    import plugin_boutique_price_checker.price_alert_service as service_module
    import plugin_boutique_price_checker.selenium_scraper as scraper_module

    monkeypatch.setattr(email_notifier_module, "EmailNotifier", FakeNotifier)
    monkeypatch.setattr(service_module, "PriceAlertService", FakeService)
    monkeypatch.setattr(scraper_module, "PluginBoutiqueSeleniumScraper", FakeScraper)
    monkeypatch.setattr(
        cli,
        "parse_args",
        lambda: Namespace(
            url="https://example.com/single",
            threshold=49.0,
            watchlist_file=None,
            to="alerts@example.com",
            no_headless=False,
        ),
    )

    monkeypatch.setenv("EMAIL_ADDRESS", "sender@example.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "app-password")
    monkeypatch.setenv("SMTP_ADDRESS", "smtp.example.com")

    cli.main()

    assert created["scraper"].headless is True
    assert created["notifier"].smtp_address == "smtp.example.com"
    assert created["service"].calls == [
        ("https://example.com/single", 49.0, "alerts@example.com")
    ]


def test_main_watchlist_mode_uses_item_or_default_recipient(monkeypatch) -> None:
    class FakeScraper:
        def __init__(self, headless: bool) -> None:
            self.headless = headless

    class FakeNotifier:
        def __init__(self, smtp_address: str, email_address: str, app_password: str) -> None:
            self.smtp_address = smtp_address
            self.email_address = email_address
            self.app_password = app_password

    created = {}

    class FakeService:
        def __init__(self, scraper, notifier) -> None:
            created["scraper"] = scraper
            self.calls = []
            created["service"] = self

        def check_and_notify(self, url: str, threshold: float, recipient_email: str) -> None:
            self.calls.append((url, threshold, recipient_email))

    import plugin_boutique_price_checker.email_notifier as email_notifier_module
    import plugin_boutique_price_checker.price_alert_service as service_module
    import plugin_boutique_price_checker.selenium_scraper as scraper_module

    monkeypatch.setattr(email_notifier_module, "EmailNotifier", FakeNotifier)
    monkeypatch.setattr(service_module, "PriceAlertService", FakeService)
    monkeypatch.setattr(scraper_module, "PluginBoutiqueSeleniumScraper", FakeScraper)
    monkeypatch.setattr(
        cli,
        "parse_args",
        lambda: Namespace(
            url=None,
            threshold=None,
            watchlist_file="watchlist.json",
            to="fallback@example.com",
            no_headless=True,
        ),
    )
    monkeypatch.setattr(
        cli,
        "load_watchlist",
        lambda _: [
            {"url": "https://example.com/a", "threshold": 10.0, "to": None},
            {"url": "https://example.com/b", "threshold": 20.0, "to": "item@example.com"},
        ],
    )

    monkeypatch.setenv("EMAIL_ADDRESS", "sender@example.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "app-password")
    monkeypatch.setenv("SMTP_ADDRESS", "smtp.example.com")

    cli.main()

    assert created["scraper"].headless is False
    assert created["service"].calls == [
        ("https://example.com/a", 10.0, "fallback@example.com"),
        ("https://example.com/b", 20.0, "item@example.com"),
    ]
