"""Unit tests for data models."""

from plugin_boutique_price_checker.models import PriceResult


def test_price_result_formatted_two_decimals() -> None:
    result = PriceResult(amount=49.9, currency="$")
    assert result.formatted == "$49.90"
