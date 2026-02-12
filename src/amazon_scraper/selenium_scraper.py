import re

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from .models import PriceResult


class PluginBoutiqueSeleniumScraper:
    def __init__(self, headless: bool = True, timeout_seconds: int = 20) -> None:
        self.headless = headless
        self.timeout_seconds = timeout_seconds

    def _build_driver(self) -> webdriver.Chrome:
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def get_price(self, url: str) -> PriceResult:
        driver = self._build_driver()
        try:
            driver.get(url)
            try:
                WebDriverWait(driver, self.timeout_seconds).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException as exc:
                raise RuntimeError("Timed out waiting for page to load") from exc

            html = driver.page_source
            return self._extract_closest_price(html)
        finally:
            driver.quit()

    @staticmethod
    def _extract_closest_price(html: str) -> PriceResult:
        lower_html = html.lower()
        anchor = lower_html.find("add to cart")
        if anchor == -1:
            anchor = lower_html.find("buy now")

        matches = list(re.finditer(r"([\u00a3\u20ac$])\s?(\d[\d,]*(?:\.\d{2})?)", html))
        if not matches:
            raise RuntimeError("No currency-like prices found in page source")

        best = min(matches, key=lambda m: abs(m.start() - anchor) if anchor != -1 else m.start())
        currency = best.group(1)
        amount = float(best.group(2).replace(",", ""))
        return PriceResult(amount=amount, currency=currency)
