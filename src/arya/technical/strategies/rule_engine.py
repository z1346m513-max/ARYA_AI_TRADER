"""
موتور استراتژی مبتنی بر قوانین قابل‌تنظیم (اندیکاتور + آستانه).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    rule_type: str
    passed: bool
    value: float | None
    detail: str


@dataclass(frozen=True)
class StrategyMatch:
    profile: str
    passed: bool
    action: str
    score: float
    reasons: tuple[str, ...]
    rule_results: tuple[RuleResult, ...] = field(default_factory=tuple)


def _rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gains = delta.clip(lower=0).rolling(period).mean()
    losses = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gains / losses.replace(0, pd.NA)
    return (100 - (100 / (1 + rs))).fillna(50.0)


def _eval_rule(df: pd.DataFrame, rule: dict[str, Any]) -> RuleResult:
    rid = str(rule.get("id") or rule.get("type") or "rule")
    rtype = str(rule.get("type") or "").lower()
    close = df["close"].astype(float)

    if rtype == "rsi":
        period = int(rule.get("period", 14))
        series = _rsi(close, period)
        val = float(series.iloc[-1])
        mn = rule.get("min")
        mx = rule.get("max")
        ok = True
        if mn is not None and val < float(mn):
            ok = False
        if mx is not None and val > float(mx):
            ok = False
        detail = f"RSI({period})={val:.1f}"
        if mn is not None:
            detail += f" min={mn}"
        if mx is not None:
            detail += f" max={mx}"
        return RuleResult(rid, rtype, ok, val, detail)

    if rtype == "ema_cross":
        fast_p = int(rule.get("fast", 20))
        slow_p = int(rule.get("slow", 50))
        cond = str(rule.get("condition", "fast_above_slow"))
        fast = close.ewm(span=fast_p, adjust=False).mean()
        slow = close.ewm(span=slow_p, adjust=False).mean()
        fv, sv = float(fast.iloc[-1]), float(slow.iloc[-1])
        if cond == "fast_below_slow":
            ok = fv < sv
        else:
            ok = fv > sv
        detail = f"EMA{fast_p}={fv:.2f} EMA{slow_p}={sv:.2f} ({cond})"
        return RuleResult(rid, rtype, ok, fv - sv, detail)

    if rtype == "macd":
        fast_p = int(rule.get("fast", 12))
        slow_p = int(rule.get("slow", 26))
        sig_p = int(rule.get("signal", 9))
        cond = str(rule.get("condition", "macd_above_signal"))
        ema_f = close.ewm(span=fast_p, adjust=False).mean()
        ema_s = close.ewm(span=slow_p, adjust=False).mean()
        macd = ema_f - ema_s
        signal = macd.ewm(span=sig_p, adjust=False).mean()
        mv, sv = float(macd.iloc[-1]), float(signal.iloc[-1])
        if cond == "macd_below_signal":
            ok = mv < sv
        else:
            ok = mv > sv
        detail = f"MACD={mv:.4f} Signal={sv:.4f}"
        return RuleResult(rid, rtype, ok, mv - sv, detail)

    if rtype == "volume_ratio":
        period = int(rule.get("period", 20))
        min_ratio = float(rule.get("min_ratio", 1.5))
        vol = df["volume"].astype(float)
        avg = vol.rolling(period).mean()
        last = float(vol.iloc[-1])
        base = float(avg.iloc[-1]) if avg.iloc[-1] == avg.iloc[-1] else 0.0
        ratio = (last / base) if base > 0 else 0.0
        ok = ratio >= min_ratio
        detail = f"VolRatio({period})={ratio:.2f} (min {min_ratio})"
        return RuleResult(rid, rtype, ok, ratio, detail)

    if rtype == "price_change_pct":
        lookback = int(rule.get("lookback", 1))
        mn = rule.get("min")
        mx = rule.get("max")
        if len(close) <= lookback:
            return RuleResult(rid, rtype, False, None, "history_short")
        prev = float(close.iloc[-1 - lookback])
        pct = ((float(close.iloc[-1]) - prev) / prev * 100.0) if prev else 0.0
        ok = True
        if mn is not None and pct < float(mn):
            ok = False
        if mx is not None and pct > float(mx):
            ok = False
        detail = f"Change%{lookback}d={pct:.2f}"
        return RuleResult(rid, rtype, ok, pct, detail)

    return RuleResult(rid, rtype, False, None, f"unknown_rule_type:{rtype}")


def evaluate_profile(df: pd.DataFrame, profile_name: str, profile: dict[str, Any]) -> StrategyMatch:
    min_candles = int(profile.get("min_candles", 30))
    if len(df) < min_candles:
        return StrategyMatch(
            profile_name,
            False,
            "hold",
            0.0,
            ("insufficient_history",),
            (),
        )

    rules = profile.get("rules") or []
    results: list[RuleResult] = []
    for rule in rules:
        if isinstance(rule, dict):
            results.append(_eval_rule(df, rule))

    if not results:
        return StrategyMatch(profile_name, False, "hold", 0.0, ("no_rules",), ())

    passed_all = all(r.passed for r in results)
    n_ok = sum(1 for r in results if r.passed)
    score = round((n_ok / len(results)) * (1.0 if passed_all else 0.5) - (0.0 if passed_all else 0.2), 4)
    action = str(profile.get("action_when_pass", "buy")) if passed_all else "hold"
    reasons = tuple(r.detail + (" ✓" if r.passed else " ✗") for r in results)
    return StrategyMatch(
        profile_name,
        passed_all,
        action,
        score,
        reasons,
        tuple(results),
    )
