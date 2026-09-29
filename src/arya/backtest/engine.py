"""
موتور بک‌تست قطعی با تأخیر یک کندلی، کارمزد، اسلیپیج و گیت ریسک.

این موتور جریان زیر را اجرا می‌کند:

    داده → استراتژی → سیگنال → گیت ریسک → sizing → اجرای شبیه‌سازی‌شده → معیارها

ویژگی‌های کلیدی:
- **تأخیر یک کندلی**: سیگنال تولیدشده در کندل N در کندل N+1 اجرا می‌شود (جلوگیری از look-ahead bias).
- **کارمزد و اسلیپیج**: هزینهٔ واقعی معامله مدل می‌شود.
- **گیت ریسک اجباری**: هیچ سفارشی بدون عبور از کنترل‌های ریسک اجرا نمی‌شود.
- **تکرارپذیری**: با داده و پیکربندی یکسان، نتیجه همیشه یکسان است.
- **ثبت ممیزی**: تمام سفارش‌ها (شامل رد‌شده‌ها) و اجراها ثبت می‌شوند.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from arya.backtest.models import (
    BacktestResult,
    EquityPoint,
    Fill,
    Order,
    OrderStatus,
    PerformanceMetrics,
    Position,
    Side,
    Signal,
    Trade,
)
from arya.backtest.strategies import Strategy
from arya.risk.risk_manager import BacktestRiskGate


@dataclass
class BacktestConfig:
    """پیکربندی بک‌تست.

    همهٔ مقادیر به‌صورت درصد یا ضریب بیان شده‌اند تا تکرارپذیری تضمین شود.
    """

    initial_equity: float = 10_000.0
    commission_rate: float = 0.001          # 0.1% کارمزد
    slippage_bps: float = 5.0               # 5 basis points اسلیپیج
    position_size_pct: float = 0.10         # 10% سرمایه برای هر پوزیشن
    max_position_pct: float = 0.25          # حداکثر 25% سرمایه در یک پوزیشن
    max_daily_loss_pct: float = 0.05        # توقف پس از 5% زیان روزانه
    risk_free_rate: float = 0.02            # نرخ بدون ریسک سالانه (برای Sharpe)
    annualization_factor: int = 252         # تعداد روزهای معاملاتی سال

    def validate(self) -> None:
        if self.initial_equity <= 0:
            raise ValueError("initial_equity باید مثبت باشد")
        if not 0 <= self.commission_rate <= 0.1:
            raise ValueError("commission_rate باید بین ۰ و ۰.۱ باشد")
        if self.slippage_bps < 0:
            raise ValueError("slippage_bps نمی‌تواند منفی باشد")
        if not 0 < self.position_size_pct <= 1.0:
            raise ValueError("position_size_pct باید بین ۰ و ۱ باشد")
        if not 0 < self.max_position_pct <= 1.0:
            raise ValueError("max_position_pct باید بین ۰ و ۱ باشد")
        if not 0 < self.max_daily_loss_pct <= 1.0:
            raise ValueError("max_daily_loss_pct باید بین ۰ و ۱ باشد")


class BacktestEngine:
    """موتور بک‌تست با گیت ریسک و ثبت ممیزی.

    استفاده:

    ```python
    from arya.backtest import BacktestEngine, BacktestConfig, MovingAverageCrossover

    engine = BacktestEngine(config=BacktestConfig())
    result = engine.run(df, strategy=MovingAverageCrossover(), symbol="FOOLAD")
    print(result.metrics.total_return_pct)
    ```
    """

    def __init__(
        self,
        config: BacktestConfig | None = None,
        risk_gate: BacktestRiskGate | None = None,
    ):
        self.config = config or BacktestConfig()
        self.config.validate()
        self.risk_gate = risk_gate or BacktestRiskGate(
            max_position_pct=self.config.max_position_pct,
            max_daily_loss_pct=self.config.max_daily_loss_pct,
        )

    def run(
        self,
        df: pd.DataFrame,
        strategy: Strategy,
        symbol: str = "UNKNOWN",
    ) -> BacktestResult:
        """اجرای بک‌تست کامل.

        مراحل:
        1. اعتبارسنجی داده‌ها
        2. تولید سیگنال‌ها توسط استراتژی
        3. شبیه‌سازی گام‌به‌گام با تأخیر یک کندلی
        4. اعمال گیت ریسک قبل از هر سفارش
        5. محاسبهٔ معیارهای عملکرد
        """
        self._validate_data(df)
        run_id = str(uuid.uuid4())[:12]

        signals = strategy.generate_signals(df)
        signals.sort(key=lambda s: s.bar_index)

        equity = self.config.initial_equity
        position = Position(symbol=symbol)
        cash = equity
        trades: list[Trade] = []
        fills: list[Fill] = []
        rejected: list[Order] = []
        equity_curve: list[EquityPoint] = []

        # نگاشت سیگنال‌ها بر اساس bar_index برای دسترسی سریع
        signals_by_bar: dict[int, list[Signal]] = {}
        for sig in signals:
            signals_by_bar.setdefault(sig.bar_index, []).append(sig)

        # متغیرهای ردیابی ریسک روزانه
        daily_start_equity = equity
        current_day = None
        trading_halted = False

        for i in range(len(df)):
            ts = self._get_timestamp(df, i)
            day = ts.date() if hasattr(ts, "date") else None

            # بازنشانی محدودیت روزانه
            if day != current_day:
                current_day = day
                daily_start_equity = equity
                trading_halted = False

            # قیمت بسته شدن این کندل برای ارزش‌گذاری
            close_price = float(df["close"].iloc[i])

            # محاسبهٔ ارزش کل (cash + پوزیشن)
            position_value = position.market_value(close_price) if position.is_open else 0.0
            total_equity = cash + position_value

            # بررسی توقف روزانه
            if daily_start_equity > 0:
                daily_loss_pct = (daily_start_equity - total_equity) / daily_start_equity
                if daily_loss_pct >= self.config.max_daily_loss_pct:
                    trading_halted = True

            # ثبت نقطهٔ منحنی سرمایه
            equity_curve.append(EquityPoint(
                timestamp=ts,
                equity=total_equity,
                bar_index=i,
            ))

            # پردازش سیگنال‌های این کندل (اجرا در کندل بعدی)
            if trading_halted:
                continue

            if i not in signals_by_bar:
                continue

            # تأخیر یک کندلی: سیگنال تولیدشده در کندل i در کندل i+1 اجرا می‌شود
            # یعنی قیمت اجرا = قیمت باز شدن کندل بعدی
            if i + 1 >= len(df):
                continue

            exec_price = float(df["open"].iloc[i + 1])
            exec_ts = self._get_timestamp(df, i + 1)

            for sig in signals_by_bar[i]:
                # اگر پوزیشن باز است و سیگنال هم‌جهت است، نادیده بگیر
                if position.is_open:
                    if sig.side == Side.BUY and position.quantity > 0:
                        continue
                    if sig.side == Side.SELL and position.quantity > 0:
                        # فروش: بستن پوزیشن فعلی
                        order_qty = abs(position.quantity)
                    else:
                        continue
                else:
                    # محاسبهٔ اندازهٔ سفارش
                    order_qty = self._compute_position_size(
                        equity=total_equity,
                        price=exec_price,
                        signal=sig,
                    )

                if order_qty <= 0:
                    continue

                order = Order(
                    timestamp=exec_ts,
                    side=sig.side,
                    quantity=order_qty,
                    signal=sig,
                )

                # عبور از گیت ریسک
                allowed, reason, adjusted_qty = self.risk_gate.check(
                    order=order,
                    position=position,
                    equity=total_equity,
                    close_price=close_price,
                )

                if not allowed:
                    order.status = OrderStatus.REJECTED
                    order.rejection_reason = reason
                    rejected.append(order)
                    continue

                order.quantity = adjusted_qty

                # شبیه‌سازی اجرا با اسلیپیج و کارمزد
                fill = self._execute_order(order, exec_price)
                fill = self._apply_costs(fill)

                # به‌روزرسانی پوزیشن و cash
                position.update_on_fill(fill)
                cash -= fill.total_cost
                fills.append(fill)

                # ثبت معاملهٔ بسته‌شده
                if not position.is_open and fill.side == Side.SELL:
                    trade = self._close_trade(position, fill, exec_ts, i)
                    if trade:
                        trades.append(trade)
                    position = Position(symbol=symbol)

        # محاسبهٔ معیارهای عملکرد
        metrics = self._compute_metrics(
            equity_curve=equity_curve,
            trades=trades,
            fills=fills,
            config=self.config,
        )

        return BacktestResult(
            symbol=symbol,
            strategy_name=strategy.name,
            initial_equity=self.config.initial_equity,
            metrics=metrics,
            equity_curve=equity_curve,
            trades=trades,
            fills=fills,
            rejected_orders=rejected,
            config={
                "commission_rate": self.config.commission_rate,
                "slippage_bps": self.config.slippage_bps,
                "position_size_pct": self.config.position_size_pct,
                "max_position_pct": self.config.max_position_pct,
                "max_daily_loss_pct": self.config.max_daily_loss_pct,
                "strategy": strategy.name,
            },
            run_id=run_id,
        )

    def _validate_data(self, df: pd.DataFrame) -> None:
        """اعتبارسنجی داده‌های ورودی."""
        required_cols = {"open", "high", "low", "close", "volume"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"ستون‌های مورد نیاز موجود نیستند: {missing}")
        if len(df) < 10:
            raise ValueError(f"حداقل ۱۰ کندل لازم است، {len(df)} داده موجود است")
        if df["close"].isna().any():
            raise ValueError("داده‌های گمشده در ستون close وجود دارد")
        if (df["close"] <= 0).any():
            raise ValueError("قیمت close صفر یا منفی وجود دارد")

    def _compute_position_size(
        self,
        equity: float,
        price: float,
        signal: Signal,
    ) -> float:
        """محاسبهٔ اندازهٔ سفارش بر اساس درصد سرمایه."""
        notional = equity * self.config.position_size_pct * signal.strength
        return notional / price

    def _execute_order(self, order: Order, base_price: float) -> Fill:
        """شبیه‌سازی اجرای سفارش با اسلیپیج."""
        # اسلیپیج: خرید گران‌تر، فروش ارزان‌تر
        slippage = self.config.slippage_bps / 10_000.0
        if order.side == Side.BUY:
            exec_price = base_price * (1 + slippage)
        else:
            exec_price = base_price * (1 - slippage)

        return Fill(
            timestamp=order.timestamp,
            side=order.side,
            quantity=order.quantity,
            price=exec_price,
        )

    def _apply_costs(self, fill: Fill) -> Fill:
        """اعمال کارمزد و محاسبهٔ هزینهٔ اسلیپیج."""
        base_price = fill.price / (1 + self.config.slippage_bps / 10_000.0) if fill.side == Side.BUY else fill.price / (1 - self.config.slippage_bps / 10_000.0)
        fill.commission = fill.notional * self.config.commission_rate
        fill.slippage_cost = abs(fill.price - base_price) * fill.quantity
        return fill

    def _close_trade(
        self,
        position: Position,
        exit_fill: Fill,
        exit_time: datetime,
        exit_bar: int,
    ) -> Trade | None:
        """ساخت رکورد معاملهٔ بسته‌شده."""
        if not position.is_open and position.realized_pnl != 0:
            return Trade(
                entry_time=exit_time,  # تقریبی
                exit_time=exit_time,
                side=Side.SELL,
                entry_price=position.avg_price,
                exit_price=exit_fill.price,
                quantity=exit_fill.quantity,
                pnl=position.realized_pnl,
                return_pct=position.realized_pnl / (position.avg_price * exit_fill.quantity) if position.avg_price > 0 else 0.0,
                bars_held=1,
            )
        return None

    def _compute_metrics(
        self,
        equity_curve: list[EquityPoint],
        trades: list[Trade],
        fills: list[Fill],
        config: BacktestConfig,
    ) -> PerformanceMetrics:
        """محاسبهٔ معیارهای عملکرد بک‌تست."""
        if not equity_curve:
            return PerformanceMetrics(
                total_return_pct=0, annualized_return_pct=0, volatility_pct=0,
                max_drawdown_pct=0, sharpe_ratio=0, sortino_ratio=0,
                win_rate=0, total_trades=0, winning_trades=0, losing_trades=0,
                avg_win_pct=0, avg_loss_pct=0, profit_factor=0,
                avg_bars_held=0, turnover=0,
                final_equity=config.initial_equity, initial_equity=config.initial_equity,
            )

        equities = np.array([e.equity for e in equity_curve])
        returns = np.diff(equities) / equities[:-1] if len(equities) > 1 else np.array([])

        initial = config.initial_equity
        final = equities[-1]
        total_return = (final - initial) / initial

        n_bars = len(equity_curve)
        ann_factor = config.annualization_factor
        annualized_return = (1 + total_return) ** (ann_factor / max(n_bars, 1)) - 1 if total_return > -1 else -1.0

        volatility = float(np.std(returns) * math.sqrt(ann_factor) * 100) if len(returns) > 0 else 0.0

        # حداکثر افت سرمایه
        peak = np.maximum.accumulate(equities)
        drawdown = (peak - equities) / peak
        max_dd = float(np.max(drawdown) * 100) if len(drawdown) > 0 else 0.0

        # نسبت شارپ
        excess_returns = returns - config.risk_free_rate / ann_factor if len(returns) > 0 else np.array([])
        sharpe = float(np.mean(excess_returns) / np.std(excess_returns) * math.sqrt(ann_factor)) if len(excess_returns) > 1 and np.std(excess_returns) > 0 else 0.0

        # نسبت سورتینو
        downside = excess_returns[excess_returns < 0] if len(excess_returns) > 0 else np.array([])
        downside_std = np.std(downside) if len(downside) > 0 else 0.0
        sortino = float(np.mean(excess_returns) / downside_std * math.sqrt(ann_factor)) if downside_std > 0 else 0.0

        # آمار معاملات
        total_trades = len(trades)
        winning = [t for t in trades if t.pnl > 0]
        losing = [t for t in trades if t.pnl <= 0]
        win_rate = len(winning) / total_trades if total_trades > 0 else 0.0

        avg_win = np.mean([t.return_pct for t in winning]) * 100 if winning else 0.0
        avg_loss = np.mean([t.return_pct for t in losing]) * 100 if losing else 0.0

        gross_profit = sum(t.pnl for t in winning)
        gross_loss = abs(sum(t.pnl for t in losing))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        avg_bars = np.mean([t.bars_held for t in trades]) if trades else 0.0

        # turnover: نسبت ارزش معاملات به سرمایهٔ میانگین
        total_notional = sum(f.notional for f in fills)
        avg_equity = float(np.mean(equities))
        turnover = total_notional / avg_equity if avg_equity > 0 else 0.0

        return PerformanceMetrics(
            total_return_pct=total_return * 100,
            annualized_return_pct=annualized_return * 100,
            volatility_pct=volatility,
            max_drawdown_pct=max_dd,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            win_rate=win_rate,
            total_trades=total_trades,
            winning_trades=len(winning),
            losing_trades=len(losing),
            avg_win_pct=float(avg_win),
            avg_loss_pct=float(avg_loss),
            profit_factor=profit_factor,
            avg_bars_held=float(avg_bars),
            turnover=turnover,
            final_equity=final,
            initial_equity=initial,
        )

    @staticmethod
    def _get_timestamp(df: pd.DataFrame, idx: int) -> datetime:
        """دریافت timestamp از اندیس دیتافریم."""
        ts = df.index[idx]
        if isinstance(ts, datetime):
            return ts
        try:
            return pd.Timestamp(ts).to_pydatetime()
        except Exception:
            return datetime.utcnow()
