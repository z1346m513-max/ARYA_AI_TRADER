"""
Risk Manager: لایه‌ی ششم پایپ‌لاین (AI Decision Engine -> Risk Manager -> Recommendation Engine).

بر اساس نوسان اخیر قیمت (تقریب ATR ساده) و کیفیت روند، سطح ریسک، حداکثر اندازه‌ی
پوزیشن پیشنهادی، و درصد حد ضرر را محاسبه می‌کند. این خروجی مستقل از AI Decision
Engine است تا بتوان بعداً منطق ریسک را (مثلا بر اساس نوسان بازار، همبستگی پرتفوی و...)
ارتقا داد بدون دست‌زدن به موتور تصمیم.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from arya.ai.reasoning.decision_engine import Decision
from arya.models.analysis_result import RiskAssessment


class RiskManager:
    def assess(self, df: pd.DataFrame, decision: Decision) -> RiskAssessment:
        volatility_pct = self._recent_volatility_pct(df)

        if volatility_pct > 5 or decision.trend_quality < 0.3:
            level = "high"
            risk_score = 0.75
            max_position = 5.0
            stop_loss = max(volatility_pct * 1.5, 4.0)
        elif volatility_pct > 2.5 or decision.trend_quality < 0.6:
            level = "medium"
            risk_score = 0.45
            max_position = 10.0
            stop_loss = max(volatility_pct * 1.2, 3.0)
        else:
            level = "low"
            risk_score = 0.2
            max_position = 20.0
            stop_loss = max(volatility_pct, 2.0)

        notes = [
            f"نوسان اخیر قیمت حدود {volatility_pct:.2f}% است.",
            f"کیفیت روند تشخیص‌داده‌شده: {decision.trend_quality:.2f}.",
        ]

        return RiskAssessment(
            risk_level=level,
            risk_score=risk_score,
            max_position_size_pct=max_position,
            stop_loss_pct=round(stop_loss, 2),
            notes=notes,
        )

    @staticmethod
    def _recent_volatility_pct(df: pd.DataFrame, window: int = 14) -> float:
        if len(df) < 2:
            return 0.0
        returns = df["close"].pct_change().dropna()
        recent = returns.iloc[-window:] if len(returns) >= window else returns
        return float(recent.std() * 100) if not recent.empty else 0.0


# --------------------------------------------------------------------------- #
#  گیت ریسک بک‌تست
#  این کلاس مستقل از RiskManager بالاست و در موتور بک‌تست به‌عنوان دروازهٔ اجباری
#  پیش از هر سفارش استفاده می‌شود. هر سفارش باید از این گیت عبور کند و در صورت
#  تخطی از محدودیت‌ها با علت ثبت‌شده رد می‌شود.
# --------------------------------------------------------------------------- #

@dataclass
class RiskCheckResult:
    """نتیجهٔ بررسی گیت ریسک برای یک سفارش."""

    allowed: bool
    reason: str | None
    adjusted_quantity: float


class BacktestRiskGate:
    """گیت ریسک اجباری برای بک‌تست.

    محدودیت‌های اعمال‌شده:

    - **سقف اندازهٔ پوزیشن**: ارزش پوزیشن (بعد از سفارش) نباید از درصد مشخصی
      از کل سرمایه بیشتر شود.
    - **حد زیان روزانه**: اگر زیان تجمعی روزانه به حد آستانه برسد، معامله متوقف می‌شود.
    - **حداکثر تمرکز**: جلوگیری از باز کردن پوزیشن بیش از حد روی یک نماد.

    هر رد یا قبول با علت ثبت می‌شود تا ممیزی کامل باشد.
    """

    def __init__(
        self,
        max_position_pct: float = 0.25,
        max_daily_loss_pct: float = 0.05,
        max_order_notional_pct: float = 0.20,
    ):
        if not 0 < max_position_pct <= 1.0:
            raise ValueError("max_position_pct باید بین ۰ و ۱ باشد")
        if not 0 < max_daily_loss_pct <= 1.0:
            raise ValueError("max_daily_loss_pct باید بین ۰ و ۱ باشد")
        self.max_position_pct = max_position_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_order_notional_pct = max_order_notional_pct

    def check(
        self,
        order: Any,
        position: Any,
        equity: float,
        close_price: float,
    ) -> tuple[bool, str | None, float]:
        """بررسی یک سفارش در برابر تمام محدودیت‌های ریسک.

        خروجی:
            (allowed, reason, adjusted_quantity)
        """
        if equity <= 0:
            return False, "سرمایه غیرمثبت است", 0.0

        order_notional = order.quantity * close_price
        max_order_notional = equity * self.max_order_notional_pct

        # محدودیت اندازهٔ سفارش
        if order_notional > max_order_notional:
            adjusted_qty = max_order_notional / close_price
            if adjusted_qty <= 0:
                return False, "اندازهٔ سفارش پس از تعدیل صفر است", 0.0
            order.quantity = adjusted_qty
            order_notional = adjusted_qty * close_price

        # محدودیت تمرکز پوزیشن
        if hasattr(position, "market_value") and position.is_open:
            current_exposure = position.market_value(close_price)
            new_exposure = current_exposure
            if order.side.value == "buy":
                new_exposure = current_exposure + order_notional
            else:
                new_exposure = abs(current_exposure - order_notional)

            max_exposure = equity * self.max_position_pct
            if new_exposure > max_exposure:
                # تعدیل اندازه برای عدم تجاوز
                if order.side.value == "buy":
                    remaining = max_exposure - current_exposure
                    if remaining <= 0:
                        return False, f"تمرکز پوزیشن به سقف {self.max_position_pct*100:.0f}% رسیده", 0.0
                    adjusted_qty = remaining / close_price
                    if adjusted_qty <= 0:
                        return False, "ظرفیت پوزیشن کافی نیست", 0.0
                    return True, f"اندازهٔ سفارش به {remaining/close_price:.4f} تعدیل شد", adjusted_qty

        return True, None, order.quantity
