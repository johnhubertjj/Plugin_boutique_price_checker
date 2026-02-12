from dataclasses import dataclass


@dataclass
class PriceResult:
    amount: float
    currency: str

    @property
    def formatted(self) -> str:
        return f"{self.currency}{self.amount:.2f}"
