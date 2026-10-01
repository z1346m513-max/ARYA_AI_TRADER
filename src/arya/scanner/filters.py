"""فیلترهای قابل‌تکرار برای دیده‌بان بازار؛ مستقل از syntax فیلترنویسی سایت‌ها."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class MarketFilterConfig:
    min_price_change_pct: float = -100.0
    max_price_change_pct: float = 100.0
    min_volume_ratio: float = 1.5
    min_value: float = 0.0
    min_buyer_power: float | None = None
    require_positive_close: bool = False


@dataclass(frozen=True)
class FilterResult:
    passed: bool
    reasons: tuple[str, ...]
    metrics: dict[str, float]


def evaluate_market_filter(row: dict, config: MarketFilterConfig) -> FilterResult:
    """یک ردیف market-watch را ارزیابی می‌کند؛ کلیدهای اختیاری غیاب را تحمل می‌کنند."""
    close = float(row.get("close", row.get("pClosing", 0)) or 0)
    previous = float(row.get("previous_close", row.get("py", 0)) or 0)
    volume = float(row.get("volume", row.get("qTotTran5J", 0)) or 0)
    average_volume = float(row.get("average_volume", 0) or 0)
    value = float(row.get("value", row.get("qTotCap", 0)) or 0)
    price_change = ((close / previous) - 1) * 100 if previous > 0 else 0.0
    volume_ratio = volume / average_volume if average_volume > 0 else 0.0
    buyer_power = row.get("buyer_power")

    reasons: list[str] = []
    if not config.min_price_change_pct <= price_change <= config.max_price_change_pct:
        reasons.append("price_change_out_of_range")
    if volume_ratio < config.min_volume_ratio:
        reasons.append("volume_not_confirmed")
    if value < config.min_value:
        reasons.append("value_below_minimum")
    if config.require_positive_close and price_change <= 0:
        reasons.append("not_positive")
    if config.min_buyer_power is not None and (buyer_power is None or float(buyer_power) < config.min_buyer_power):
        reasons.append("buyer_power_not_confirmed")

    return FilterResult(
        passed=not reasons,
        reasons=tuple(reasons),
        metrics={"price_change_pct": price_change, "volume_ratio": volume_ratio, "value": value},
    )


def scan_ohlcv(df: pd.DataFrame, config: MarketFilterConfig) -> FilterResult:
    """فیلتر عمومی روی سری OHLCV؛ برای جلوگیری از look-ahead فقط آخرین ردیف را می‌سنجد."""
    if len(df) < 2:
        return FilterResult(False, ("insufficient_history",), {})
    last = df.iloc[-1]
    avg_volume = float(df["volume"].tail(20).iloc[:-1].mean()) if len(df) > 2 else 0.0
    return evaluate_market_filter(
        {"close": last["close"], "previous_close": df["close"].iloc[-2], "volume": last["volume"], "average_volume": avg_volume},
        config,
    )
