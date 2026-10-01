"""مدل‌های دادهٔ بنیادی؛ مستقل از منبع Codal و آمادهٔ اتصال به provider."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FundamentalMetrics:
    """نسبت‌های بنیادی استاندارد؛ مقادیر ناموجود باید None بمانند."""

    eps: float | None = None
    revenue: float | None = None
    net_income: float | None = None
    book_value_per_share: float | None = None
    market_price: float | None = None
    dividend_per_share: float | None = None
    debt: float | None = None
    equity: float | None = None
    current_assets: float | None = None
    current_liabilities: float | None = None

    @staticmethod
    def _ratio(numerator: float | None, denominator: float | None) -> float | None:
        if numerator is None or denominator in (None, 0):
            return None
        return numerator / denominator

    @property
    def pe(self) -> float | None:
        return self._ratio(self.market_price, self.eps) if self.eps and self.eps > 0 else None

    @property
    def pb(self) -> float | None:
        return self._ratio(self.market_price, self.book_value_per_share)

    @property
    def dividend_yield(self) -> float | None:
        return self._ratio(self.dividend_per_share, self.market_price)

    @property
    def net_margin(self) -> float | None:
        return self._ratio(self.net_income, self.revenue)

    @property
    def debt_to_equity(self) -> float | None:
        return self._ratio(self.debt, self.equity)

    @property
    def current_ratio(self) -> float | None:
        return self._ratio(self.current_assets, self.current_liabilities)

    def as_dict(self) -> dict[str, float | None]:
        return {
            "eps": self.eps,
            "pe": self.pe,
            "pb": self.pb,
            "dividend_yield": self.dividend_yield,
            "net_margin": self.net_margin,
            "debt_to_equity": self.debt_to_equity,
            "current_ratio": self.current_ratio,
        }
