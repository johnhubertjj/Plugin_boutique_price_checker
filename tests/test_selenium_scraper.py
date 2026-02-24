"""Unit tests for Selenium scraper behavior."""

import pytest
from selenium.common.exceptions import TimeoutException

from plugin_boutique_price_checker.models import PriceResult
from plugin_boutique_price_checker.selenium_scraper import PluginBoutiqueSeleniumScraper


def test_extract_closest_price_prefers_anchor_nearest_price() -> None:
    html = """
    <span>$999.99</span>
    <span>$49.95</span>
    <button>Add to Cart</button>
    """

    result = PluginBoutiqueSeleniumScraper._extract_closest_price(html)

    assert result == PriceResult(amount=49.95, currency="$")


def test_extract_closest_price_without_anchor_uses_first_match() -> None:
    html = "<span>EUR €12.50</span> <span>$22.00</span>"
    result = PluginBoutiqueSeleniumScraper._extract_closest_price(html)
    assert result == PriceResult(amount=12.50, currency="€")


def test_extract_closest_price_raises_when_no_currency_found() -> None:
    with pytest.raises(RuntimeError, match="No currency-like prices found"):
        PluginBoutiqueSeleniumScraper._extract_closest_price("<html><body>No price</body></html>")


def test_build_driver_configures_expected_options(monkeypatch) -> None:
    import plugin_boutique_price_checker.selenium_scraper as scraper_module

    class FakeOptions:
        def __init__(self) -> None:
            self.arguments = []

        def add_argument(self, arg: str) -> None:
            self.arguments.append(arg)

    class FakeService:
        def __init__(self, driver_path: str) -> None:
            self.driver_path = driver_path

    class FakeChromeDriverManager:
        def install(self) -> str:
            return "/tmp/chromedriver"

    captured = {}

    def fake_chrome(service, options):
        captured["service"] = service
        captured["options"] = options
        return "fake-driver"

    monkeypatch.setattr(scraper_module, "Options", FakeOptions)
    monkeypatch.setattr(scraper_module, "Service", FakeService)
    monkeypatch.setattr(scraper_module, "ChromeDriverManager", FakeChromeDriverManager)
    monkeypatch.setattr(scraper_module.webdriver, "Chrome", fake_chrome)

    scraper = PluginBoutiqueSeleniumScraper(headless=True)
    driver = scraper._build_driver()

    assert driver == "fake-driver"
    assert captured["service"].driver_path == "/tmp/chromedriver"
    assert "--headless=new" in captured["options"].arguments
    assert "--disable-gpu" in captured["options"].arguments
    assert "--no-sandbox" in captured["options"].arguments
    assert "--window-size=1920,1080" in captured["options"].arguments
    assert "--disable-dev-shm-usage" in captured["options"].arguments


def test_get_price_returns_extracted_result_and_quits_driver(monkeypatch) -> None:
    import plugin_boutique_price_checker.selenium_scraper as scraper_module

    class FakeDriver:
        def __init__(self) -> None:
            self.page_source = "<button>Buy Now</button><span>$18.00</span>"
            self.got = []
            self.quit_called = False

        def get(self, url: str) -> None:
            self.got.append(url)

        def quit(self) -> None:
            self.quit_called = True

    class FakeWait:
        def __init__(self, driver, timeout_seconds: int) -> None:
            self.driver = driver
            self.timeout_seconds = timeout_seconds

        def until(self, _condition) -> bool:
            return True

    fake_driver = FakeDriver()
    monkeypatch.setattr(PluginBoutiqueSeleniumScraper, "_build_driver", lambda self: fake_driver)
    monkeypatch.setattr(scraper_module, "WebDriverWait", FakeWait)

    scraper = PluginBoutiqueSeleniumScraper(timeout_seconds=7)
    result = scraper.get_price("https://example.com/product")

    assert result == PriceResult(amount=18.0, currency="$")
    assert fake_driver.got == ["https://example.com/product"]
    assert fake_driver.quit_called is True


def test_get_price_raises_runtime_error_on_timeout_and_quits_driver(monkeypatch) -> None:
    import plugin_boutique_price_checker.selenium_scraper as scraper_module

    class FakeDriver:
        def __init__(self) -> None:
            self.page_source = ""
            self.quit_called = False

        def get(self, _url: str) -> None:
            return None

        def quit(self) -> None:
            self.quit_called = True

    class FakeWait:
        def __init__(self, driver, timeout_seconds: int) -> None:
            self.driver = driver
            self.timeout_seconds = timeout_seconds

        def until(self, _condition) -> None:
            raise TimeoutException("timed out")

    fake_driver = FakeDriver()
    monkeypatch.setattr(PluginBoutiqueSeleniumScraper, "_build_driver", lambda self: fake_driver)
    monkeypatch.setattr(scraper_module, "WebDriverWait", FakeWait)

    scraper = PluginBoutiqueSeleniumScraper()
    with pytest.raises(RuntimeError, match="Timed out waiting for page to load"):
        scraper.get_price("https://example.com/product")

    assert fake_driver.quit_called is True
