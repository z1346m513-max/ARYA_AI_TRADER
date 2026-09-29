#!/usr/bin/env python3
"""Run a deterministic, long-only SMA-crossover backtest from OHLCV CSV data."""
from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Bar:
    timestamp: str
    open: float
    close: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="CSV with timestamp,open,high,low,close,volume")
    parser.add_argument("--output", type=Path, default=Path("data/reports/backtest-report.json"))
    parser.add_argument("--initial-cash", type=float, default=100_000.0)
    parser.add_argument("--fast", type=int, default=20, help="Fast SMA period")
    parser.add_argument("--slow", type=int, default=50, help="Slow SMA period")
    parser.add_argument("--fee-bps", type=float, default=10.0, help="Fee per fill in basis points")
    parser.add_argument("--slippage-bps", type=float, default=5.0, help="Slippage per fill in basis points")
    args = parser.parse_args()
    if args.initial_cash <= 0 or args.fast <= 0 or args.slow <= args.fast:
        parser.error("initial-cash must be positive and slow must exceed fast")
    if args.fee_bps < 0 or args.slippage_bps < 0:
        parser.error("fee-bps and slippage-bps must be non-negative")
    return args


def load_bars(path: Path) -> list[Bar]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"timestamp", "open", "close"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("input CSV must contain timestamp,open,close columns")
        bars = [Bar(row["timestamp"], float(row["open"]), float(row["close"])) for row in reader]
    if len(bars) < 3:
        raise ValueError("input CSV requires at least three rows")
    if any(bar.open <= 0 or bar.close <= 0 for bar in bars):
        raise ValueError("open and close prices must be positive")
    return bars


def sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def run(bars: list[Bar], initial_cash: float, fast: int, slow: int, fee_bps: float, slippage_bps: float) -> dict:
    cash, units, trades = initial_cash, 0.0, []
    closes: list[float] = []
    previous_signal = 0
    equity_curve: list[float] = []
    costs = (fee_bps + slippage_bps) / 10_000

    # Signal uses completed bars only; execution occurs at the next bar's open.
    for index, bar in enumerate(bars):
        if index > 0:
            fast_sma, slow_sma = sma(closes, fast), sma(closes, slow)
            signal = 0 if fast_sma is None or slow_sma is None else (1 if fast_sma > slow_sma else -1)
            if signal > 0 and previous_signal <= 0 and units == 0:
                fill = bar.open * (1 + costs)
                units = cash / fill
                cash = 0.0
                trades.append({"timestamp": bar.timestamp, "side": "BUY", "price": fill, "units": units})
            elif signal < 0 and previous_signal >= 0 and units > 0:
                fill = bar.open * (1 - costs)
                cash = units * fill
                trades.append({"timestamp": bar.timestamp, "side": "SELL", "price": fill, "units": units})
                units = 0.0
            if signal:
                previous_signal = signal
        closes.append(bar.close)
        equity_curve.append(cash + units * bar.close)

    final_equity = equity_curve[-1]
    peaks, max_drawdown = [], 0.0
    peak = equity_curve[0]
    for equity in equity_curve:
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity / peak - 1)
    returns = [equity_curve[i] / equity_curve[i - 1] - 1 for i in range(1, len(equity_curve)) if equity_curve[i - 1]]
    volatility = math.sqrt(sum((r - sum(returns) / len(returns)) ** 2 for r in returns) / len(returns)) if returns else 0.0
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(), "bars": len(bars),
        "parameters": {"initial_cash": initial_cash, "fast": fast, "slow": slow, "fee_bps": fee_bps, "slippage_bps": slippage_bps},
        "metrics": {"final_equity": final_equity, "net_return": final_equity / initial_cash - 1, "max_drawdown": max_drawdown, "return_volatility": volatility, "trade_count": len(trades)},
        "trades": trades,
    }


def main() -> None:
    args = parse_args()
    report = run(load_bars(args.input), args.initial_cash, args.fast, args.slow, args.fee_bps, args.slippage_bps)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["metrics"], indent=2))


if __name__ == "__main__":
    main()
