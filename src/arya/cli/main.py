"""
CLI ورودی برنامه — بورس ایران + کدال.

نمونه:
    arya analyze --ticker FOOLAD --market stock
    arya list-symbols --market stock
    arya codal --symbol فولاد --limit 5
"""
from __future__ import annotations

import argparse
import sys

from rich.console import Console

from arya.app.bootstrap import AryaApp
from arya.dashboard.console_dashboard import render_recommendation
from arya.cli.codal_command import register_codal_parser, run_codal


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="arya", description="ARYA AI Trader — بورس ایران و کدال")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze_p = sub.add_parser("analyze", help="تحلیل یک نماد و نمایش پیشنهاد")
    analyze_p.add_argument("--ticker", required=True, help="نماد، مثلا FOOLAD")
    analyze_p.add_argument("--market", default="stock", choices=["stock"])
    analyze_p.add_argument("--timeframe", default="1d")

    list_p = sub.add_parser("list-symbols", help="لیست نمادهای موجود")
    list_p.add_argument("--market", default="stock", choices=["stock"])

    scan_p = sub.add_parser("scan", help="تحلیل تمام نمادهای بازار")
    scan_p.add_argument("--market", default="stock", choices=["stock"])

    register_codal_parser(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    console = Console()

    if args.command == "codal":
        return run_codal(args, console)

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
