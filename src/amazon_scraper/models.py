"""Data models used by the price tracking workflow."""

from dataclasses import dataclass


@dataclass
class PriceResult:
    """Represents a parsed product price and its currency symbol.

    Args:
        amount: Numeric price amount without currency formatting.
        currency: Currency symbol associated with the amount.

    Returns:
        PriceResult: Dataclass instance containing parsed price details.
    """

    amount: float
    currency: str

    @property
    def formatted(self) -> str:
        """Format the price as currency symbol plus amount with two decimals.

        Args:
            None.

        Returns:
            str: Formatted price string such as ``$19.99``.
        """
        return f"{self.currency}{self.amount:.2f}"
