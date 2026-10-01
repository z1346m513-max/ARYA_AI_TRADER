#!/usr/bin/env python3
"""اتصال زنده به market-watch TSETMC و ثبت health snapshot.

نمونه:
  PYTHONPATH=src python scripts/tsetmc_live_check.py --ticker فولاد --json

این اسکریپت فقط health-check و گزارش‌گیری است و هیچ سفارش یا معامله‌ای ایجاد نمی‌کند.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from arya.providers.market.tsetmc_provider import TsetmcMarketProvider, TsetmcProviderError


def main() -> int:
    parser = argparse.ArgumentParser(description="TSETMC market-watch live health check")
    parser.add_argument("--ticker", default=None, help="اختیاری؛ مثلاً فولاد")
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--base-url", default="https://cdn.tsetmc.com")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    checked_at = datetime.now(timezone.utc)

    try:
        provider = TsetmcMarketProvider(base_url=args.base_url, timeout=args.timeout, retries=args.retries)
        quotes = provider.fetch_market_watch(args.ticker)
        if not quotes:
            raise TsetmcProviderError("market-watch بدون quote معتبر پاسخ داد")
        valid = [q for q in quotes if q["close"] > 0 and q["last"] > 0]
        result = {
            "ok": bool(valid),
            "provider": provider.name,
            "feed": "market-watch",
            "ticker": args.ticker,
            "quotes": len(quotes),
            "valid_quotes": len(valid),
            "sample": valid[0] if valid else None,
            "checked_at": checked_at.isoformat(),
            "market_status": "data_available" if valid else "no_valid_data",
        }
        print(json.dumps(result, ensure_ascii=False) if args.as_json else result)
        return 0 if valid else 2
    except Exception as exc:
        result = {"ok": False, "feed": "market-watch", "error": str(exc), "checked_at": checked_at.isoformat()}
        print(json.dumps(result, ensure_ascii=False) if args.as_json else result, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
