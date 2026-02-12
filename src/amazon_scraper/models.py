"""Data models used by the price tracking workflow."""

from dataclasses import dataclass


@dataclass
class PriceResult:
    """Represents a parsed product price and its currency symbol."""

    amount: float
    currency: str

    @property
    def formatted(self) -> str:
        return f"{self.currency}{self.amount:.2f}"
