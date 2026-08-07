"""
CLI ورودی برنامه.

نمونه استفاده:
    arya analyze --ticker FOOLAD --market stock
    arya list-symbols --market crypto
"""
from __future__ import annotations

import argparse
import sys

from rich.console import Console

from arya.app.bootstrap import AryaApp
from arya.dashboard.console_dashboard import render_recommendation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="arya", description="ARYA AI Trader CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze_p = sub.add_parser("analyze", help="تحلیل یک نماد و نمایش پیشنهاد")
    analyze_p.add_argument("--ticker", required=True, help="نماد، مثلا FOOLAD یا BTCUSDT")
    analyze_p.add_argument("--market", default="stock", choices=["stock", "crypto", "forex"])
    analyze_p.add_argument("--timeframe", default="1d")

    list_p = sub.add_parser("list-symbols", help="لیست نمادهای موجود در یک بازار")
    list_p.add_argument("--market", default="stock", choices=["stock", "crypto", "forex"])

    scan_p = sub.add_parser("scan", help="تحلیل تمام نمادهای یک بازار")
    scan_p.add_argument("--market", default="stock", choices=["stock", "crypto", "forex"])

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    console = Console()

    app = AryaApp()

    if args.command == "analyze":
        rec = app.analyze_symbol(args.ticker, market=args.market, timeframe=args.timeframe)
        render_recommendation(rec, console)

    elif args.command == "list-symbols":
        symbols = app.list_symbols(market=args.market)
        for s in symbols:
            console.print(f"  {s.ticker}  ({s.name})")

    elif args.command == "scan":
        symbols = app.list_symbols(market=args.market)
        for s in symbols:
            rec = app.analyze_symbol(s.ticker, market=args.market)
            render_recommendation(rec, console)

    return 0


if __name__ == "__main__":
    sys.exit(main())
