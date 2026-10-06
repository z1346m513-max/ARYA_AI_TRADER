"""
مدل داده‌ی بنیادی برای محاسبه‌ی نسبت‌های مالی.

این مدل تمام اقلام صورت‌های مالی مورد نیاز برای ۱۸ نسبت را در خود نگه می‌دارد.
سازگار با FundamentalMetrics موجود در arya.models.fundamentals؛ فیلدهای جدید
اضافه شده‌اند اما فیلدهای قبلی حذف نشده‌اند.

تمام مقادیر به‌صورت float یا None ذخیره می‌شوند.
برای نسبت‌های میانگین‌دار (ROE، ROA، گردش‌ها) اگر مقدار میانگین در دسترس نیست،
مقدار پایان دوره استفاده می‌شود و هشدار داده می‌شود.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arya.models.fundamentals import FundamentalMetrics


@dataclass(frozen=True)
class FinancialData:
    """
    داده‌ی بنیادی برای محاسبه‌ی نسبت‌های مالی.

    مقادیر None به‌معنای «داده موجود نیست» هستند.
    رشد سود به‌صورت درصد ذخیره می‌شود (۲۰ یعنی ۲۰٪).
    """

    # ─── داده‌ی بازار ───
    market_price: float | None = None
    shares_outstanding: float | None = None
    market_cap: float | None = None

    # ─── صورت سود و زیان ───
    revenue: float | None = None
    cost_of_goods_sold: float | None = None
    gross_profit: float | None = None
    operating_income: float | None = None
    net_income: float | None = None
    eps: float | None = None
    interest_expense: float | None = None
    depreciation: float | None = None
    operating_cash_flow: float | None = None
    cash_flow_per_share: float | None = None

    # ─── ترازنامه ───
    total_assets: float | None = None
    total_liabilities: float | None = None
    equity: float | None = None
    current_assets: float | None = None
    current_liabilities: float | None = None
    inventory: float | None = None
    receivables: float | None = None
    fixed_assets: float | None = None
    cash: float | None = None
    debt: float | None = None
    book_value_per_share: float | None = None

    # ─── رشد و تقسیم سود ───
    earnings_growth_rate_percent: float | None = None
    dividend_per_share: float | None = None

    # ─── مقادیر میانگین (اختیاری) ───
    avg_total_assets: float | None = None
    avg_equity: float | None = None
    avg_inventory: float | None = None
    avg_receivables: float | None = None
    avg_fixed_assets: float | None = None

    @property
    def gross_profit_value(self) -> float | None:
        """حاشیه سود ناخالص را محاسبه می‌کند اگر gross_profit موجود نباشد."""
        if self.gross_profit is not None:
            return self.gross_profit
        if self.revenue is not None and self.cost_of_goods_sold is not None:
            return self.revenue - self.cost_of_goods_sold
        return None

    @property
    def market_cap_value(self) -> float | None:
        """ارزش بازار را محاسبه می‌کند اگر مستقیماً موجود نباشد."""
        if self.market_cap is not None:
            return self.market_cap
        if self.market_price is not None and self.shares_outstanding is not None:
            return self.market_price * self.shares_outstanding
        return None

    @classmethod
    def from_metrics(cls, metrics: "FundamentalMetrics") -> "FinancialData":
        """
        از FundamentalMetrics موجود در arya.models.fundamentals تبدیل می‌کند.

        این متد اجازه می‌دهد کدهای موجود که از FundamentalMetrics استفاده می‌کنند،
        بدون تغییر به نسبت‌های جدید دسترسی داشته باشند.
        """
        return cls(
            market_price=metrics.market_price,
            eps=metrics.eps,
            revenue=metrics.revenue,
            net_income=metrics.net_income,
            book_value_per_share=metrics.book_value_per_share,
            dividend_per_share=metrics.dividend_per_share,
            debt=metrics.debt,
            equity=metrics.equity,
            current_assets=metrics.current_assets,
            current_liabilities=metrics.current_liabilities,
        )
