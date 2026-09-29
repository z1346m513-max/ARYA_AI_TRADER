"""
مدل‌های دامنهٔ بک‌تست: سیگنال، سفارش، اجرا، پوزیشن، معامله و معیارهای عملکرد.

این مدل‌ها قرارداد روشنی برای جریان بک‌تست فراهم می‌کنند و از نمایش داده‌های
آینده (look-ahead bias) جلوگیری می‌کنند.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Signal:
    """سیگنال معاملاتی تولیدشده توسط یک استراتژی در یک زمان مشخص.

    مهم: ``bar_index`` اندیس کندلی است که سیگنال بر اساس داده‌های *تا آن لحظه*
    (شامل خود آن کندل) تولید کرده است. اجرای سفارش ناشی از این سیگنال باید
    در کندل بعدی صورت گیرد تا از look-ahead bias جلوگیری شود.
    """

    timestamp: datetime
    side: Side
    bar_index: int
    strength: float = 1.0          # [0, 1] - اطمینان استراتژی
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Order:
    """سفارش معاملاتی مشتق‌شده از یک سیگنال."""

    timestamp: datetime
    side: Side
    quantity: float
    order_type: str = "market"     # market | limit
    limit_price: float | None = None
    signal: Signal | None = None
    status: OrderStatus = OrderStatus.PENDING
    rejection_reason: str | None = None

    @property
    def is_buy(self) -> bool:
        return self.side == Side.BUY


@dataclass
class Fill:
    """اجرای یک سفارش با قیمت و هزینهٔ واقعی."""

    timestamp: datetime
    side: Side
    quantity: float
    price: float
    commission: float = 0.0
    slippage_cost: float = 0.0

    @property
    def total_cost(self) -> float:
        """هزینهٔ خالص اجرا شامل کارمزد و اسلیپیج."""
        sign = 1.0 if self.side == Side.BUY else -1.0
        return sign * (self.price * self.quantity + self.commission + self.slippage_cost)

    @property
    def notional(self) -> float:
        return self.price * self.quantity


@dataclass
class Position:
    """پوزیشن باز برای یک نماد."""

    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0
    realized_pnl: float = 0.0

    @property
    def is_open(self) -> bool:
        return abs(self.quantity) > 1e-10

    def market_value(self, price: float) -> float:
        return self.quantity * price

    def update_on_fill(self, fill: Fill) -> None:
        """به‌روزرسانی پوزیشن پس از هر اجرا."""
        if fill.side == Side.BUY:
            new_qty = self.quantity + fill.quantity
            if new_qty > 1e-10:
                self.avg_price = (
                    (self.avg_price * self.quantity + fill.price * fill.quantity) / new_qty
                )
            self.quantity = new_qty
        else:
            # فروش: محاسبهٔ سود/زیان تحقق‌یافته
            closed_qty = min(fill.quantity, max(self.quantity, 0.0))
            if closed_qty > 1e-10:
                self.realized_pnl += (fill.price - self.avg_price) * closed_qty
            self.quantity -= fill.quantity


@dataclass
class Trade:
    """یک معاملهٔ کامل: ورود و خروج."""

    entry_time: datetime
    exit_time: datetime
    side: Side
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    return_pct: float
    bars_held: int


@dataclass
class EquityPoint:
    """یک نقطه از منحنی سرمایه در طول بک‌تست."""

    timestamp: datetime
    equity: float
    bar_index: int


@dataclass
class PerformanceMetrics:
    """معیارهای عملکرد بک‌تست."""

    total_return_pct: float
    annualized_return_pct: float
    volatility_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win_pct: float
    avg_loss_pct: float
    profit_factor: float
    avg_bars_held: float
    turnover: float
    final_equity: float
    initial_equity: float


@dataclass
class BacktestResult:
    """خروجی کامل یک اجرای بک‌تست."""

    symbol: str
    strategy_name: str
    initial_equity: float
    metrics: PerformanceMetrics
    equity_curve: list[EquityPoint] = field(default_factory=list)
    trades: list[Trade] = field(default_factory=list)
    fills: list[Fill] = field(default_factory=list)
    rejected_orders: list[Order] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    run_id: str = ""
