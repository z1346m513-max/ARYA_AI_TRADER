#!/usr/bin/env python3
"""Smoke test زندهٔ TSETMC؛ این فایل عمداً بخشی از pytest نیست.

اجرا فقط در محیط عملیاتی/شبکه‌ای که دسترسی به cdn.tsetmc.com دارد:
  python scripts/live_tsetmc_smoke.py --ticker فولاد
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from arya.models.market_data import Symbol
from arya.providers.market.tsetmc_provider import TsetmcMarketProvider, TsetmcProviderError


def main() -> int:
    parser = argparse.ArgumentParser(description="Live TSETMC connectivity smoke test")
    parser.add_argument("--ticker", default="فولاد")
    parser.add_argument("--base-url", default="https://cdn.tsetmc.com")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    try:
        provider = TsetmcMarketProvider(base_url=args.base_url, timeout=args.timeout, retries=2)
        series = provider.fetch_ohlcv(Symbol(args.ticker, "stock"), "1d", args.limit)
        closes = [c.close for c in series.candles]
        timestamps = [c.timestamp for c in series.candles]
        if any(value <= 0 for value in closes) or timestamps != sorted(timestamps):
            raise TsetmcProviderError("دادهٔ دریافتی از نظر قیمت یا ترتیب زمانی معتبر نیست")
        result = {
            "ok": True,
            "provider": provider.name,
            "ticker": series.symbol.ticker,
            "candles": len(series.candles),
            "first_timestamp": timestamps[0].isoformat(),
            "last_timestamp": timestamps[-1].isoformat(),
            "last_close": closes[-1],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        print(json.dumps(result, ensure_ascii=False) if args.as_json else result)
        return 0
    except Exception as exc:  # smoke test باید خطای عملیاتی را با exit code اعلام کند
        result = {"ok": False, "error": str(exc), "checked_at": datetime.now(timezone.utc).isoformat()}
        print(json.dumps(result, ensure_ascii=False) if args.as_json else result, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
